"""Exercise the service launcher with a fake daemon and simulated DSM privileges.

These tests never create a TUN device, load modules, or start a VPN connection.
They check the environment received by the daemon, including the root fallback.
"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "spk/scripts/start-stop-status"

HARNESS = r'''
id() { printf 'id\n' >> "$CALLS"; printf '%s\n' "$TEST_UID"; }
lsmod() { printf 'lsmod\n' >> "$CALLS"; printf 'tun 0 0\n'; }
modprobe() { printf 'modprobe\n' >> "$CALLS"; return 1; }
insmod() { printf 'insmod\n' >> "$CALLS"; return 1; }
mknod() { printf 'mknod\n' >> "$CALLS"; return 1; }
# Simulate device permissions without depending on the test host's /dev tree.
test_bracket() {
    case "$*" in
        '-c /dev/net/tun ]') test "$TEST_TUN" != missing ;;
        '! -c /dev/net/tun ]') test "$TEST_TUN" = missing ;;
        '-w /dev/net/tun ]') test "$TEST_TUN" = writable ;;
        '-d /dev/net ]') return 0 ;;
        *) command [ "$@" ;;
    esac
}
alias [=test_bracket

set -- "$TEST_ACTION"
. "$SERVICE_SCRIPT"
# An unrecognised action loads the functions without dispatching a service action.
# The fake daemon exits after recording its environment, so use its output as
# readiness rather than the real daemon's Linux /proc lifetime check.
daemon_status() { test -s "$SYNOPKG_PKGVAR/daemon.env"; }
# Conflict detection has its own isolated filesystem/process fixtures.
check_manual_install() { return 0; }
start_daemon
'''


class ServiceNetworkingTests(unittest.TestCase):
    def run_service(self, uid, tun, inherited=None, action="test-start"):
        with tempfile.TemporaryDirectory(prefix="netbird-dsm-test-") as tmp:
            base = Path(tmp)
            pkgvar = base / "var"
            bindir = base / "target/bin"
            pkgvar.mkdir()
            bindir.mkdir(parents=True)
            # Exercise the actual nohup/exec boundary, not just shell variables.
            (bindir / "netbird.bin").write_text(
                '#!/bin/sh\n'
                'printf "%s\\n" "$@" > "$SYNOPKG_PKGVAR/daemon.args"\n'
                'env > "$SYNOPKG_PKGVAR/daemon.env"\n'
            )
            (bindir / "netbird").write_text("#!/bin/sh\nexit 0\n")
            env = {k: v for k, v in os.environ.items() if not k.startswith(("NB_", "WT_"))}
            env.update(inherited or {})
            env.update(
                SYNOPKG_PKGVAR=str(pkgvar),
                SYNOPKG_PKGDEST=str(base / "target"),
                SERVICE_SCRIPT=str(SERVICE),
                TEST_UID=str(uid),
                TEST_TUN=tun,
                TEST_ACTION=action,
                CALLS=str(base / "calls"),
            )
            result = subprocess.run(
                ["sh", "-c", HARNESS, str(SERVICE)], env=env, capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.returncode, 3 if action == "status" else 0, result.stderr)
            calls = (base / "calls").read_text().splitlines() if (base / "calls").exists() else []
            if action in ("stop", "status"):
                self.assertFalse((pkgvar / "daemon.env").exists())
                self.assertEqual(calls, [], "stop/status must not prepare network devices")
                return
            daemon_env = dict(
                line.split("=", 1) for line in (pkgvar / "daemon.env").read_text().splitlines()
                if "=" in line
            )
            self.assertEqual(daemon_env["NB_STATE_DIR"], str(pkgvar))
            self.assertEqual(daemon_env["NB_DAEMON_ADDR"], f"unix://{pkgvar}/netbird.sock")
            self.assertEqual(daemon_env["NB_ENABLE_JSON_SOCKET"], "true")
            self.assertEqual(daemon_env["NB_JSON_SOCKET"], f"unix://{pkgvar}/run/netbird-http.sock")
            args = (pkgvar / "daemon.args").read_text().splitlines()
            self.assertEqual(args[:2], ["service", "run"])
            self.assertEqual(args[args.index("--config") + 1], str(pkgvar / "config.json"))
            self.assertIn("--enable-json-socket", args)
            self.assertEqual(args[args.index("--json-socket") + 1], f"unix://{pkgvar}/run/netbird-http.sock")
            self.assertEqual((pkgvar / "run").stat().st_mode & 0o777, 0o700)
            self.assertEqual(daemon_env["NB_WG_KERNEL_DISABLED"], "true")
            return daemon_env, calls, (pkgvar / "netbird.log").read_text()

    def assert_netstack(self, result):
        env, _, log = result
        self.assertEqual(env["NB_USE_NETSTACK_MODE"], "true")
        self.assertEqual(env["NB_ENABLE_NETSTACK_LOCAL_FORWARDING"], "true")
        self.assertEqual(env["NB_DISABLE_DNS"], "true")
        self.assertEqual(env["NB_ENABLE_CAPTURE"], "false")
        self.assertIn("netstack with local forwarding", log)

    def test_package_user_without_tun(self):
        result = self.run_service(1000, "missing")
        self.assert_netstack(result)
        self.assertEqual(result[1], ["id"])

    def test_writable_tun_does_not_give_package_user_network_privileges(self):
        result = self.run_service(1000, "writable", {
            "NB_USE_NETSTACK_MODE": "false",
            "NB_ENABLE_NETSTACK_LOCAL_FORWARDING": "false",
            "NB_DISABLE_DNS": "false",
            "NB_ENABLE_CAPTURE": "true",
            "NB_ENABLE_JSON_SOCKET": "false",
            "NB_JSON_SOCKET": "tcp://0.0.0.0:8080",
        })
        self.assert_netstack(result)
        self.assertEqual(result[1], ["id"])

    def test_explicit_root_start_keeps_kernel_tun_mode(self):
        env, calls, log = self.run_service(0, "writable", {"NB_USE_NETSTACK_MODE": "true"})
        self.assertEqual(env["NB_USE_NETSTACK_MODE"], "false")
        self.assertNotIn("NB_ENABLE_NETSTACK_LOCAL_FORWARDING", env)
        self.assertNotIn("NB_DISABLE_DNS", env)
        self.assertNotIn("NB_ENABLE_CAPTURE", env)
        self.assertEqual(calls, ["id", "lsmod"])
        self.assertIn("kernel TUN", log)
        self.assertIn("Starting as root can create root-owned state", log)
        self.assertIn("Returning to Package Center", log)

    def test_root_falls_back_when_tun_creation_fails(self):
        result = self.run_service(0, "missing")
        self.assert_netstack(result)
        self.assertIn("mknod", result[1])

    def test_root_falls_back_when_tun_is_not_writable(self):
        self.assert_netstack(self.run_service(0, "readonly"))

    def test_stop_and_status_do_not_prepare_networking(self):
        for action in ("stop", "status"):
            with self.subTest(action=action):
                self.run_service(0, "missing", action=action)

    def test_shell_syntax(self):
        for script in [*ROOT.glob("spk/scripts/*"), ROOT / "spk/INFO.sh",
                       ROOT / "spk/wrapper/netbird", *ROOT.glob("spk/package/ui/*.cgi")]:
            with self.subTest(script=script.name):
                subprocess.run(["sh", "-n", str(script)], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
