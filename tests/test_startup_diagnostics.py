"""Run the launcher against failing daemons and real log/permission changes."""

import os
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "spk/scripts/start-stop-status"
HARNESS = r'''
set -- load-functions
. "$SERVICE_SCRIPT"
check_manual_install() { return 0; }
configure_networking() { NETWORK_MODE="test"; }
# This fixture exits or execs sleep; production now also verifies NetBird's
# process identity. Lifecycle/ownership tests cover that separate boundary.
daemon_status() {
    test -r "$PID_FILE" && test -d "/proc/$(cat "$PID_FILE")"
}
# Keep the actual exec/exit and /proc checks; shorten only the startup delay.
sleep() { command sleep 0.2; }
start_daemon
'''
DAEMON = r'''#!/bin/sh
printf 'launched\n' > "$SYNOPKG_PKGVAR/launched"
case "$SCENARIO" in
    success) exec sleep 60 ;;
    truncate) : > "$SYNOPKG_PKGVAR/netbird.log" ;;
    regrow)
        : > "$SYNOPKG_PKGVAR/netbird.log"
        i=0
        while [ "$i" -lt 100 ]; do
            echo 'new output after truncation'
            i=$((i + 1))
        done
        ;;
    rotate)
        echo "${ATTEMPT}: before rename"
        mv "$SYNOPKG_PKGVAR/netbird.log" "$SYNOPKG_PKGVAR/netbird.log.1"
        echo "${ATTEMPT}: reopened log" > "$SYNOPKG_PKGVAR/netbird.log"
        ;;
    unlink)
        rm "$SYNOPKG_PKGVAR/netbird.log"
        : > "$SYNOPKG_PKGVAR/netbird.log"
        ;;
    copytruncate|compressed)
        printf '%s: %s\n' "$ATTEMPT" "$ERROR_TEXT" >&2
        cp "$SYNOPKG_PKGVAR/netbird.log" "$SYNOPKG_PKGVAR/netbird.log.1"
        : > "$SYNOPKG_PKGVAR/netbird.log"
        if [ "$SCENARIO" = compressed ]; then
            gzip -f "$SYNOPKG_PKGVAR/netbird.log.1"
        fi
        exit 1
        ;;
    silent) exit 42 ;;
esac
printf '%s: %s\n' "$ATTEMPT" "$ERROR_TEXT" >&2
exit 1
'''


class StartupDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="netbird-diagnostics-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.var = self.base / "var"
        self.var.mkdir()
        self.bin = self.base / "target/bin"
        self.bin.mkdir(parents=True)
        for name, content in (("netbird.bin", DAEMON), ("netbird", "#!/bin/sh\nexit 0\n")):
            (self.bin / name).write_text(content)
            (self.bin / name).chmod(0o755)
        self.log = self.var / "netbird.log"
        self.config = self.var / "config.json"
        self.config.write_text('{"ServerSSHAllowed":false}')
        self.message = self.base / "message"
        self.journal = self.base / "journal"
        # Never write tests' synthetic errors to the host's real journal.
        mockbin = self.base / "mockbin"
        mockbin.mkdir()
        (mockbin / "logger").write_text('#!/bin/sh\ncat >> "$TEST_JOURNAL"\n')
        (mockbin / "logger").chmod(0o755)
        self.env = dict(os.environ, PATH=str(mockbin) + ":" + os.environ["PATH"],
                        SYNOPKG_PKGVAR=str(self.var), SYNOPKG_PKGDEST=str(self.base / "target"),
                        SYNOPKG_TEMP_LOGFILE=str(self.message), SERVICE_SCRIPT=str(SERVICE),
                        TEST_JOURNAL=str(self.journal))

    def run_start(self, scenario="fail", attempt="current", error="FATL invalid character in JSON"):
        env = dict(self.env, SCENARIO=scenario, ATTEMPT=attempt, ERROR_TEXT=error)
        return subprocess.run(["sh", "-c", HARNESS, str(SERVICE)], env=env,
                              capture_output=True, text=True, timeout=10)

    def assert_failed(self, result, message):
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(message, result.stderr)
        if "SYNOPKG_TEMP_LOGFILE" in self.env:
            self.assertIn(message, self.message.read_text())
        self.assertIn(message, self.journal.read_text())
        self.assertEqual(list(self.var.glob("netbird.log.startup.*")), [])

    def test_repeated_failures_forward_each_error_once(self):
        self.log.write_text("OLD ERROR: permission denied\n")
        for attempt in ("first", "second", "third"):
            self.assert_failed(self.run_start(attempt=attempt), "configuration or profile JSON")
        journal = self.journal.read_text()
        self.assertNotIn("OLD ERROR", journal)
        for attempt in ("first", "second", "third"):
            self.assertEqual(journal.count(attempt + ": FATL"), 1)
        self.assertIn("OLD ERROR", self.log.read_text(), "preserve existing detailed logs")

    def test_log_creation_truncation_regrowth_rotation_and_unlink(self):
        for scenario in ("fail", "truncate", "regrow", "rotate", "unlink"):
            with self.subTest(scenario=scenario):
                self.log.unlink(missing_ok=True)
                if scenario != "fail":
                    self.log.write_text("OLD ERROR: permission denied\n")
                self.journal.write_text("")
                self.assert_failed(self.run_start(scenario), "configuration or profile JSON")
                journal = self.journal.read_text()
                self.assertNotIn("OLD ERROR", journal)
                self.assertEqual(journal.count("current: FATL"), 1)
                if scenario == "rotate":
                    self.assertIn("current: before rename", journal)
                    self.assertIn("current: reopened log", journal)

    def test_success_does_not_forward_old_errors_or_leave_capture_open(self):
        self.log.write_text("OLD ERROR: permission denied\n")
        result = self.run_start("success")
        pid = int((self.var / "netbird.pid").read_text())
        self.addCleanup(os.kill, pid, signal.SIGTERM)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.message.exists())
        self.assertFalse(self.journal.exists())
        self.assertEqual(list(self.var.glob("netbird.log.startup.*")), [])
        self.assertIn("started successfully", self.log.read_text())
        descriptors = Path(f"/proc/{pid}/fd")
        self.assertFalse(any("startup." in os.readlink(fd) for fd in descriptors.iterdir()))

    def test_copytruncate_after_failure_recovers_only_current_attempt(self):
        for scenario in ("copytruncate", "compressed"):
            with self.subTest(scenario=scenario):
                self.log.write_text("OLD ERROR: permission denied\n")
                self.journal.write_text("")
                for attempt in ("first", "second"):
                    self.assert_failed(self.run_start(scenario, attempt), "configuration or profile JSON")
                journal = self.journal.read_text()
                self.assertNotIn("OLD ERROR", journal)
                for attempt in ("first", "second"):
                    self.assertEqual(journal.count(attempt + ": FATL"), 1)

    def test_rotated_logs_without_current_marker_are_never_replayed(self):
        (self.var / "netbird.log.1").write_text("OLD ERROR: permission denied\n")
        self.assert_failed(self.run_start("truncate"), "configuration or profile JSON")
        self.assertNotIn("OLD ERROR", self.journal.read_text())

    def test_raw_credentials_and_config_are_not_in_dsm_message(self):
        raw = 'FATL invalid character: {"PrivateKey":"SYNTHETIC_SECRET"} https://example.invalid/?token=TEST_TOKEN'
        self.assert_failed(self.run_start(error=raw), "configuration or profile JSON")
        message = self.message.read_text()
        for value in ("PrivateKey", "SYNTHETIC_SECRET", "example.invalid", "TEST_TOKEN"):
            self.assertNotIn(value, message)
        self.assertIn(raw, self.log.read_text())

    def test_unknown_error_does_not_echo_arbitrary_output(self):
        self.assert_failed(self.run_start(error="SYNTHETIC_SECRET"), "exit code 1")
        self.assertNotIn("SYNTHETIC_SECRET", self.message.read_text())

    def test_silent_exit_has_useful_fallback(self):
        self.log.write_text("OLD ERROR: permission denied\n")
        self.assert_failed(self.run_start("silent"), "exit code 42")
        self.assertNotIn("OLD ERROR", self.journal.read_text())

    def test_common_daemon_errors_have_fixed_actionable_messages(self):
        for error, message in (("permission denied", "Check package-user permissions"),
                               ("no space left on device", "Free space"),
                               ("read-only file system", "Restore write access"),
                               ("address already in use", "Stop the conflicting instance")):
            with self.subTest(error=error):
                self.assert_failed(self.run_start(error=error), message)

    def test_direct_invocation_without_dsm_result_file(self):
        del self.env["SYNOPKG_TEMP_LOGFILE"]
        self.assert_failed(self.run_start(), "configuration or profile JSON")
        self.assertFalse(self.message.exists())

    def test_unwritable_result_file_does_not_prevent_stderr_and_syslog(self):
        self.env["SYNOPKG_TEMP_LOGFILE"] = str(self.base / "missing/message")
        result = self.run_start()
        self.assertEqual(result.returncode, 1)
        self.assertIn("configuration or profile JSON", result.stderr)
        self.assertIn("configuration or profile JSON", self.journal.read_text())

    def test_log_directory_is_reported_without_launching(self):
        self.log.mkdir()
        self.assert_failed(self.run_start(), "Cannot open")
        self.assertFalse((self.var / "launched").exists())

    @unittest.skipIf(os.geteuid() == 0, "permission checks require an unprivileged user")
    def test_unwritable_log_is_reported_without_launching(self):
        self.log.write_text("OLD ERROR\n")
        self.log.chmod(0o400)
        self.addCleanup(self.log.chmod, 0o600)
        self.assert_failed(self.run_start(), "Cannot open")
        self.assertFalse((self.var / "launched").exists())
        self.assertEqual(self.log.read_text(), "OLD ERROR\n")

    @unittest.skipIf(os.geteuid() == 0, "permission checks require an unprivileged user")
    def test_unreadable_config_is_reported_with_unwritable_log(self):
        self.config.chmod(0)
        self.log.write_text("")
        self.log.chmod(0o400)
        self.addCleanup(self.config.chmod, 0o600)
        self.addCleanup(self.log.chmod, 0o600)
        self.assert_failed(self.run_start(), "Existing package config")
        self.assertFalse((self.var / "launched").exists())

    def test_missing_binary_is_reported_before_launch(self):
        (self.bin / "netbird.bin").unlink()
        self.assert_failed(self.run_start(), "missing or not executable")
        self.assertFalse((self.var / "launched").exists())

    def test_pid_write_failure_is_reported_before_launch(self):
        (self.var / "netbird.pid").mkdir()
        self.assert_failed(self.run_start(), "Cannot write")
        self.assertFalse((self.var / "launched").exists())


if __name__ == "__main__":
    unittest.main()
