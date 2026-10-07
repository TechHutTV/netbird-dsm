"""Exercise ownership recovery without signalling any host processes.

The production /proc paths are redirected in a private script copy. Real file
permissions are used; only UID, signals and wait delays are simulated. Hardware
validation separately exercises root and package-user processes on DSM.
"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
id() { printf '%s\n' "$TEST_UID"; }
sleep() { :; }
kill() {
    printf '%s %s\n' "$1" "$2" >> "$TEST_SIGNALS"
    case "$TEST_SIGNAL_MODE:$1" in
        deny:*) return 1 ;;
        ignore:*|kill:-TERM) return 0 ;;
        reuse:-TERM)
            # Simulate PID reuse after TERM; never send KILL to its new owner.
            sed 's/ 12345$/ 99999/' "$TEST_PROC/$2/stat" > "$TEST_PROC/$2/stat.new"
            mv "$TEST_PROC/$2/stat.new" "$TEST_PROC/$2/stat"
            return 0 ;;
    esac
    rm -r "$TEST_PROC/$2"
}
set -- "$TEST_ACTION"
. "$SERVICE_SCRIPT"
if [ "$TEST_ACTION" = check-state ]; then check_package_state_access; fi
'''


class ServiceLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="netbird-lifecycle-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.realvar = self.base / "appdata/netbird"
        self.realvar.mkdir(parents=True)
        self.var = self.base / "var"
        self.var.symlink_to(self.realvar, target_is_directory=True)
        self.dest = self.base / "target"
        (self.dest / "bin").mkdir(parents=True)
        for name in ("netbird.bin", "netbird"):
            binary = self.dest / "bin" / name
            binary.write_text('#!/bin/sh\nprintf launched > "$SYNOPKG_PKGVAR/launched"\n')
            binary.chmod(0o755)
        self.config = self.var / "config.json"
        self.config.write_text('{"PrivateKey":"existing-test-enrollment"}\n')
        self.config_before = self.config.read_bytes()
        self.pidfile = self.var / "netbird.pid"
        self.proc = self.base / "system/proc"
        self.proc.mkdir(parents=True)
        for name in ("start-stop-status", "netbird-common"):
            source = (ROOT / "spk/scripts" / name).read_text()
            for path in ("/proc/", "/usr/local/bin/netbird", "/etc/netbird",
                         "/var/lib/netbird", "/var/run/netbird.sock"):
                source = source.replace(path, str(self.base / "system") + path)
            (self.base / name).write_text(source)
        self.service = self.base / "start-stop-status"
        mockbin = self.base / "mockbin"
        mockbin.mkdir()
        for name, script in (("systemctl", "exit 1"), ("logger", 'cat >> "$TEST_JOURNAL"')):
            (mockbin / name).write_text("#!/bin/sh\n" + script + "\n")
            (mockbin / name).chmod(0o755)
        self.signals = self.base / "signals"
        self.message = self.base / "message"
        self.env = dict(os.environ, PATH=str(mockbin) + ":" + os.environ["PATH"],
                        SYNOPKG_PKGVAR=str(self.var), SYNOPKG_PKGDEST=str(self.dest),
                        SYNOPKG_TEMP_LOGFILE=str(self.message), SERVICE_SCRIPT=str(self.service),
                        TEST_UID="1000", TEST_SIGNAL_MODE="exit", TEST_PROC=str(self.proc),
                        TEST_SIGNALS=str(self.signals), TEST_JOURNAL=str(self.base / "journal"))

    def daemon(self, uid=1000, pid=42001, state="S", tracked=True, package=True):
        proc = self.proc / str(pid)
        proc.mkdir()
        name = "netbird.bin" if package else "unrelated"
        (proc / "comm").write_text(name + "\n")
        (proc / "status").write_text(f"State:\t{state}\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n")
        (proc / "stat").write_text(f"{pid} ({name}) {state} " + "0 " * 18 + "12345\n")
        args = [str(self.dest / "bin/netbird.bin"), "service", "run", "--config",
                str(self.var / "config.json"), "--daemon-addr", "unix://" + str(self.var / "netbird.sock")]
        (proc / "cmdline").write_bytes(b"\0".join(a.encode() for a in args) + b"\0")
        if tracked:
            self.pidfile.write_text(str(pid) + "\n")
        return proc

    def run_action(self, action, **env):
        return subprocess.run(["sh", "-c", HARNESS, str(self.service)],
                              env=dict(self.env, TEST_ACTION=action, **env),
                              capture_output=True, text=True, timeout=10)

    def assert_recovery_error(self, result):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Returning to Package Center", result.stderr)
        self.assertIn(str(self.realvar), result.stderr, "show the resolved state directory")
        self.assertIn("Returning to Package Center", self.message.read_text())
        self.assertFalse((self.var / "launched").exists())
        self.assertEqual(self.config.read_bytes(), self.config_before)

    def test_root_daemon_blocks_package_stop_and_restart_and_keeps_pid(self):
        proc = self.daemon(uid=0)
        before = self.pidfile.stat()
        for action in ("stop", "prestart", "start"):
            with self.subTest(action=action):
                self.assert_recovery_error(self.run_action(action))
                self.assertTrue(proc.exists())
                self.assertEqual(self.pidfile.read_text(), "42001\n")
                self.assertEqual(self.pidfile.stat().st_ino, before.st_ino)
                self.assertFalse(self.signals.exists())
        self.assertEqual(self.run_action("status").returncode, 0)

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_root_daemon_is_found_even_with_unreadable_pid_file(self):
        proc = self.daemon(uid=0)
        self.pidfile.chmod(0)
        self.addCleanup(self.pidfile.chmod, 0o600)
        for action in ("stop", "start"):
            self.assert_recovery_error(self.run_action(action))
        self.assertTrue(proc.exists())
        self.assertTrue(self.pidfile.exists())
        self.assertEqual(self.run_action("status").returncode, 0)

    def test_missing_pid_does_not_allow_a_second_daemon_and_root_can_recover(self):
        proc = self.daemon(uid=0, tracked=False)
        self.assert_recovery_error(self.run_action("start"))
        self.assertEqual(self.run_action("stop", TEST_UID="0").returncode, 0)
        self.assertFalse(proc.exists())
        self.assertEqual(self.signals.read_text(), "-TERM 42001\n")

    def test_denied_signal_returns_failure_and_retains_tracking(self):
        proc = self.daemon()
        self.assert_recovery_error(self.run_action("stop", TEST_SIGNAL_MODE="deny"))
        self.assertTrue(proc.exists())
        self.assertEqual(self.pidfile.read_text(), "42001\n")
        self.assertEqual(self.signals.read_text(), "-TERM 42001\n")
        self.assertEqual(self.run_action("start").returncode, 0)
        self.assertFalse((self.var / "launched").exists(), "start must remain idempotent")

    def test_successful_stop_removes_pid_only_after_daemon_exits(self):
        proc = self.daemon()
        self.assertEqual(self.run_action("stop").returncode, 0)
        self.assertFalse(proc.exists())
        self.assertFalse(self.pidfile.exists())
        self.assertEqual(self.signals.read_text(), "-TERM 42001\n")

    def test_kill_fallback_waits_for_exit_before_removing_pid(self):
        proc = self.daemon()
        self.assertEqual(self.run_action("stop", TEST_SIGNAL_MODE="kill").returncode, 0)
        self.assertFalse(proc.exists())
        self.assertFalse(self.pidfile.exists())
        self.assertEqual(self.signals.read_text(), "-TERM 42001\n-KILL 42001\n")

    def test_successful_signal_without_exit_does_not_report_success(self):
        proc = self.daemon()
        self.assert_recovery_error(self.run_action("stop", TEST_SIGNAL_MODE="ignore"))
        self.assertTrue(proc.exists())
        self.assertEqual(self.pidfile.read_text(), "42001\n")
        self.assertEqual(self.signals.read_text(), "-TERM 42001\n-KILL 42001\n")

    def test_pid_reuse_after_term_never_signals_the_replacement(self):
        proc = self.daemon()
        self.assertEqual(self.run_action("stop", TEST_SIGNAL_MODE="reuse").returncode, 0)
        self.assertTrue(proc.exists())
        self.assertFalse(self.pidfile.exists())
        self.assertEqual(self.signals.read_text(), "-TERM 42001\n")

    def test_zombie_is_not_treated_as_a_running_daemon(self):
        self.daemon(state="Z")
        self.assertEqual(self.run_action("stop").returncode, 0)
        self.assertFalse(self.pidfile.exists())
        self.assertFalse(self.signals.exists())

    def test_stale_pid_never_signals_an_unrelated_process(self):
        proc = self.daemon(package=False)
        self.assertEqual(self.run_action("stop").returncode, 0)
        self.assertTrue(proc.exists())
        self.assertFalse(self.pidfile.exists())
        self.assertFalse(self.signals.exists())

    def test_invalid_pid_values_are_never_passed_to_kill(self):
        for value in ("", "-1", "0", "1", "42001 42002", "not-a-pid"):
            with self.subTest(value=value):
                self.pidfile.write_text(value)
                self.assertEqual(self.run_action("stop").returncode, 0)
                self.assertFalse(self.signals.exists())

    def test_multiple_daemons_require_administrator_recovery(self):
        self.daemon()
        self.daemon(pid=42002, tracked=False)
        for action in ("stop", "start"):
            self.assert_recovery_error(self.run_action(action))
        self.assertTrue(self.pidfile.exists())
        self.assertFalse(self.signals.exists())

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_unreadable_tracking_is_not_reported_as_stopped_or_deleted(self):
        self.pidfile.write_text("42001\n")
        self.pidfile.chmod(0)
        self.addCleanup(self.pidfile.chmod, 0o600)
        for action in ("stop", "start"):
            self.assert_recovery_error(self.run_action(action))
        self.assertEqual(self.run_action("status").returncode, 1)
        self.assertTrue(self.pidfile.exists())

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_unreadable_process_metadata_does_not_imply_daemon_exited(self):
        proc = self.daemon()
        for name in ("comm", "cmdline", "stat"):
            with self.subTest(name=name):
                entry = proc / name
                entry.chmod(0)
                try:
                    for action in ("stop", "start"):
                        self.assert_recovery_error(self.run_action(action))
                    self.assertEqual(self.run_action("status").returncode, 1)
                    self.assertEqual(self.pidfile.read_text(), "42001\n")
                    self.assertFalse(self.signals.exists())
                finally:
                    entry.chmod(0o600)

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_profile_state_and_nested_permissions_are_checked_without_reset(self):
        for name in ("active_profile.json", "state.json", ".config/netbird/profile.json"):
            with self.subTest(name=name):
                state = self.var / name
                state.parent.mkdir(parents=True, exist_ok=True)
                state.write_text("existing profile state")
                state.chmod(0o400)
                try:
                    for action in ("prestart", "start"):
                        self.assert_recovery_error(self.run_action(action))
                    self.assertEqual(state.read_text(), "existing profile state")
                finally:
                    state.chmod(0o600)

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_inaccessible_nested_directory_is_detected(self):
        directory = self.var / ".config/netbird"
        directory.mkdir(parents=True)
        directory.chmod(0)
        self.addCleanup(directory.chmod, 0o700)
        self.assert_recovery_error(self.run_action("start"))

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_log_and_pid_permission_errors_include_ownership_recovery(self):
        for name in ("netbird.log", "netbird.pid"):
            with self.subTest(name=name):
                entry = self.var / name
                entry.write_text("42001\n")
                entry.chmod(0o400)
                try:
                    self.assert_recovery_error(self.run_action("start"))
                    self.assertEqual(entry.read_text(), "42001\n")
                finally:
                    entry.chmod(0o600)

    @unittest.skipIf(os.geteuid() == 0, "requires unprivileged permission checks")
    def test_historical_logs_do_not_block_startup(self):
        archive = self.var / "netbird.log.1.gz"
        archive.touch(mode=0)
        self.addCleanup(archive.chmod, 0o600)
        self.assertEqual(self.run_action("check-state").returncode, 0)

    def test_state_directory_symlinks_are_not_followed(self):
        elsewhere = self.base / "elsewhere"
        elsewhere.mkdir()
        (self.var / "profiles").symlink_to(elsewhere, target_is_directory=True)
        self.assert_recovery_error(self.run_action("start"))
        self.assertEqual(list(elsewhere.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
