"""Exercise real shell preflight logic against isolated legacy-install fixtures."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "spk/scripts/netbird-common"


class PackageStartupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="netbird-startup-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.var = self.base / "var"
        self.var.mkdir()
        self.dest = self.base / "target"
        (self.dest / "bin").mkdir(parents=True)
        for binary in ("netbird", "netbird.bin"):
            (self.dest / "bin" / binary).touch()
        self.system = self.base / "system"
        for path in ("proc", "usr/local/bin", "etc", "var/lib", "var/run"):
            (self.system / path).mkdir(parents=True, exist_ok=True)
        # Redirect only system paths in the test copy; production has no
        # environment switch capable of disabling conflict detection.
        source = COMMON.read_text()
        for path in ("/proc/", "/usr/local/bin/netbird", "/etc/netbird",
                     "/var/lib/netbird", "/var/run/netbird.sock"):
            source = source.replace(path, str(self.system) + path)
        self.helper = self.base / "netbird-common"
        self.helper.write_text(source)
        self.mockbin = self.base / "mockbin"
        self.mockbin.mkdir()
        systemctl = self.mockbin / "systemctl"
        systemctl.write_text('#!/bin/sh\ncase "$1:$TEST_SERVICE" in\n'
                            'is-active:active) exit 0;;\n'
                            'is-enabled:*) echo "$TEST_SERVICE"; exit 0;;\nesac\nexit 1\n')
        systemctl.chmod(0o755)
        self.env = dict(os.environ, PKGVAR=str(self.var), PKGDEST=str(self.dest),
                        CONFIG_FILE=str(self.var / "config.json"),
                        SYNOPKG_TEMP_LOGFILE=str(self.base / "message"),
                        PATH=str(self.mockbin) + os.pathsep + os.environ["PATH"],
                        TEST_SERVICE="disabled")

    def run_helper(self, function):
        return subprocess.run(["sh", "-c", '. "$1"; ' + function, "sh", str(self.helper)],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def fake_process(self, argv, executable=None, name="netbird"):
        proc = self.system / "proc/123"
        proc.mkdir()
        (proc / "comm").write_text(name + "\n")
        (proc / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
        if executable:
            (proc / "exe").symlink_to(executable)

    def test_fresh_state_ignores_root_only_legacy_configuration(self):
        legacy = self.system / "etc/netbird"
        legacy.mkdir()
        config = legacy / "config.json"
        config.write_text("legacy fixture must remain untouched")
        config.chmod(0)
        self.addCleanup(config.chmod, 0o600)
        result = self.run_helper("check_manual_install && prepare_package_config")
        self.assertEqual(result.returncode, 0, result.stderr)
        new = self.var / "config.json"
        self.assertEqual(new.stat().st_mode & 0o777, 0o600)
        self.assertEqual(new.stat().st_uid, os.getuid())
        self.assertFalse(json.loads(new.read_text())["ServerSSHAllowed"])
        self.assertEqual(config.stat().st_mode & 0o777, 0)
        config.chmod(0o600)
        self.assertEqual(config.read_text(), "legacy fixture must remain untouched")

    def test_existing_config_is_never_rewritten(self):
        config = self.var / "config.json"
        contents = '{"PrivateKey":"existing-test-identity","ServerSSHAllowed":true}\n'
        config.write_text(contents)
        inode = config.stat().st_ino
        for _ in range(2):
            result = self.run_helper("prepare_package_config")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_text(), contents)
            self.assertEqual(config.stat().st_ino, inode)

    def test_missing_config_with_existing_state_is_rejected(self):
        for name in ("active_profile.json", "state.json", ".config", "another-profile"):
            with self.subTest(name=name):
                entry = self.var / name
                entry.write_text("existing state")
                result = self.run_helper("prepare_package_config")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("refusing to create a new identity", result.stderr)
                self.assertFalse((self.var / "config.json").exists())
                self.assertEqual(entry.read_text(), "existing state")
                entry.unlink()

    def test_logs_alone_do_not_prevent_first_start(self):
        (self.var / "netbird.log").write_text("previous failed attempt")
        result = self.run_helper("prepare_package_config")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_or_inaccessible_existing_config_is_not_replaced(self):
        config = self.var / "config.json"
        for contents, mode in (("", 0o600), ("existing", 0), ("existing", 0o400)):
            with self.subTest(contents=contents, mode=mode):
                config.write_text(contents)
                config.chmod(mode)
                try:
                    result = self.run_helper("prepare_package_config")
                    if os.getuid() != 0 or not contents:
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("will not be replaced", result.stderr)
                finally:
                    config.chmod(0o600)
                self.assertEqual(config.read_text(), contents)

    def test_dangling_config_link_is_not_replaced(self):
        config = self.var / "config.json"
        config.symlink_to(self.base / "missing")
        self.assertNotEqual(self.run_helper("prepare_package_config").returncode, 0)
        self.assertTrue(config.is_symlink())
        self.assertFalse((self.base / "missing").exists())

    def test_concurrent_config_creation_cannot_be_overwritten(self):
        ln = self.mockbin / "ln"
        ln.write_text('#!/bin/sh\nprintf "existing identity" > "$CONFIG_FILE"\nexec '
                      + shutil.which("ln") + ' "$@"\n')
        ln.chmod(0o755)
        result = self.run_helper("prepare_package_config")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.var / "config.json").read_text(), "existing identity")
        self.assertEqual(list(self.var.glob(".config-init.*")), [])

    def test_manual_cli_collision_is_rejected_and_package_link_is_allowed(self):
        cli = self.system / "usr/local/bin/netbird"
        cli.write_text("manual binary")
        result = self.run_helper("check_manual_install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("another installation", (self.base / "message").read_text())
        cli.unlink()
        cli.symlink_to(self.dest / "bin/netbird")
        result = self.run_helper("check_manual_install")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_deleted_manual_executable_is_detected(self):
        self.fake_process(["/usr/local/bin/netbird", "service", "run"],
                          "/usr/local/bin/netbird (deleted)")
        result = self.run_helper("check_manual_install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PID 123", result.stderr)

    def test_unresolvable_foreign_cli_link_is_a_conflict_on_first_install(self):
        shutil.rmtree(self.dest)
        cli = self.system / "usr/local/bin/netbird"
        cli.symlink_to(self.base / "missing-parent/netbird")
        result = self.run_helper("check_manual_install")
        self.assertNotEqual(result.returncode, 0)

    def test_package_cli_link_is_allowed_while_upgrade_target_is_absent(self):
        shutil.rmtree(self.dest)
        cli = self.system / "usr/local/bin/netbird"
        cli.symlink_to("/var/packages/netbird/target/bin/netbird")
        result = self.run_helper("check_manual_install")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_manual_process_is_detected_without_exe_access(self):
        self.fake_process(["/somewhere/netbird", "service", "run"])
        self.assertNotEqual(self.run_helper("check_manual_install").returncode, 0)

    def test_package_daemon_is_exempt_even_without_exe_access(self):
        self.fake_process([str(self.dest / "bin/netbird.bin"), "service", "run",
                           "--config", str(self.var / "config.json"),
                           "--daemon-addr", "unix://" + str(self.var / "netbird.sock")],
                          name="netbird.bin")
        result = self.run_helper("check_manual_install")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_package_binary_using_foreign_socket_is_a_conflict(self):
        self.fake_process([str(self.dest / "bin/netbird.bin"), "service", "run",
                           "--config", str(self.var / "config.json"),
                           "--daemon-addr", "unix:///somewhere/else.sock"], name="netbird.bin")
        self.assertNotEqual(self.run_helper("check_manual_install").returncode, 0)

    def test_package_binary_using_foreign_config_is_a_conflict(self):
        self.fake_process([str(self.dest / "bin/netbird.bin"), "service", "run",
                           "--config", "/somewhere/else.json"], name="netbird.bin")
        self.assertNotEqual(self.run_helper("check_manual_install").returncode, 0)

    def test_cli_client_is_not_mistaken_for_daemon(self):
        self.fake_process(["/usr/local/bin/netbird", "status"])
        self.assertEqual(self.run_helper("check_manual_install").returncode, 0)

    def test_active_or_enabled_manual_service_blocks_but_disabled_does_not(self):
        for state, expected in (("active", 1), ("enabled", 1), ("enabled-runtime", 1),
                                ("disabled", 0), ("static", 0), ("not-found", 0)):
            with self.subTest(state=state):
                self.env["TEST_SERVICE"] = state
                self.assertEqual(self.run_helper("check_manual_install").returncode, expected)

    def test_preinstall_invokes_conflict_check(self):
        preinst = self.base / "preinst"
        shutil.copyfile(ROOT / "spk/scripts/preinst", preinst)
        (self.system / "usr/local/bin/netbird").write_text("manual binary")
        self.env.update(SYNOPKG_PKGVAR=str(self.var), SYNOPKG_PKGDEST=str(self.dest))
        result = subprocess.run(["sh", str(preinst)], env=self.env, capture_output=True,
                                text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manual installation conflicts", result.stderr)

    def test_prestart_rejects_conflict_without_initializing_state(self):
        service = self.base / "start-stop-status"
        shutil.copyfile(ROOT / "spk/scripts/start-stop-status", service)
        (self.system / "usr/local/bin/netbird").write_text("manual binary")
        self.env.update(SYNOPKG_PKGVAR=str(self.var), SYNOPKG_PKGDEST=str(self.dest))
        result = subprocess.run(["sh", str(service), "prestart"], env=self.env,
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.var / "config.json").exists())


if __name__ == "__main__":
    unittest.main()
