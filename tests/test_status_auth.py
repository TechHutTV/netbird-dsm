"""Run the status CGI with fixture DSM authentication and package data.

Only absolute host paths are redirected into a temporary directory. Production
authentication cannot be replaced through request headers or environment flags.
"""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CGI = ROOT / "spk/package/ui/index.cgi"


class StatusAuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="netbird-status-auth-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.var = self.base / "var"
        self.var.mkdir()
        self.calls = self.base / "calls"
        self.cli_args = self.base / "cli-args"
        self.status_file = self.base / "status.json"
        self.status = {
            "daemonStatus": "Connected",
            "fqdn": "private-peer.example",
            "netbirdIp": "100.64.0.2/16",
            "daemonVersion": "0.80.0",
            "profileName": "home",
            "peers": {"connected": 1, "total": 3},
            "relays": {"available": 2, "total": 4},
        }
        self.status_file.write_text(json.dumps(self.status))
        self.env = {
            "PATH": f"{self.bin}:{os.defpath}",
            "TEST_CALLS": str(self.calls),
            "TEST_CLI_ARGS": str(self.cli_args),
            "TEST_STATUS_FILE": str(self.status_file),
            "TEST_STATUS_EXIT": "0",
            "TEST_AUTH_USER": "dsm-admin",
            "TEST_AUTH_EXIT": "0",
            "TEST_GROUPS": "users administrators",
            "TEST_GROUP_EXIT": "0",
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "/webman/3rdparty/netbird/index.cgi",
            "HTTP_COOKIE": "id=valid-session",
            "QUERY_STRING": "SynoToken=valid-token",
            "REMOTE_ADDR": "127.0.0.1",
            "SERVER_ADDR": "127.0.0.1",
        }
        self.auth = self.script("authenticate.cgi", r'''
printf 'auth\n' >> "$TEST_CALLS"
printf 'PRIVATE_AUTH_DIAGNOSTIC\n' >&2
if [ "$HTTP_COOKIE" != 'id=valid-session' ] || [ "$QUERY_STRING" != 'SynoToken=valid-token' ]; then
    exit 5
fi
printf '%s\n' "$TEST_AUTH_USER"
exit "$TEST_AUTH_EXIT"
''')
        identity = self.script("id", r'''
printf 'groups\n' >> "$TEST_CALLS"
[ "$#" = 3 ] && [ "$1" = '-nG' ] && [ "$2" = '--' ] && [ "$3" = "$TEST_AUTH_USER" ] || exit 1
printf '%s\n' "$TEST_GROUPS"
exit "$TEST_GROUP_EXIT"
''')
        self.script("netbird.bin", r'''
printf 'netbird\n' >> "$TEST_CALLS"
printf '%s\n' "$*" >> "$TEST_CLI_ARGS"
[ "$#" = 2 ] && [ "$1" = status ] && [ "$2" = --json ] || exit 1
printf 'PRIVATE_CLI_DIAGNOSTIC\n' >&2
cat "$TEST_STATUS_FILE"
exit "$TEST_STATUS_EXIT"
''')
        # Detect data reads even if an unauthorized response hides their output.
        for command in ("hostname", "sed", "tail", "jq"):
            executable = shutil.which(command)
            self.assertIsNotNone(executable, f"Tests require {command} (jq 1.5 or newer)")
            executable = shlex.quote(executable)
            self.script(command, f'printf "{command}\\n" >> "$TEST_CALLS"\nexec {executable} "$@"\n')
        for command in ("sh", "cat"):
            (self.bin / command).symlink_to(shutil.which(command))
        (self.var / "config.json").write_text('{"AdminURL":"https://private-dashboard.example"}')
        (self.var / "netbird.log").write_text("PRIVATE_DAEMON_LOG\n")
        source = CGI.read_text()
        for original, replacement in (
            ("/usr/syno/synoman/webman/modules/authenticate.cgi", str(self.auth)),
            ("/usr/bin/id", str(identity)),
            ("/var/packages/netbird/var", str(self.var)),
            ("/var/packages/netbird/target", str(self.base)),
        ):
            self.assertEqual(source.count(original), 1)
            source = source.replace(original, replacement)
        self.cgi = self.base / "index.cgi"
        self.cgi.write_text(source)

    def script(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o700)
        return path

    def request(self, **env):
        self.calls.write_text("")
        self.cli_args.write_text("")
        result = subprocess.run(
            ["sh", str(self.cgi)], env={**self.env, **env},
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        headers, body = result.stdout.split("\n\n", 1)
        self.assertIn("Cache-Control: no-store", headers)
        self.assertIn("Referrer-Policy: no-referrer", headers)
        self.assertNotIn("PRIVATE_AUTH_DIAGNOSTIC", result.stdout)
        self.assertNotIn("PRIVATE_CLI_DIAGNOSTIC", result.stdout)
        return headers, body, self.calls.read_text().splitlines()

    def assert_denied(self, result, status):
        headers, body, calls = result
        self.assertIn(f"Status: {status}", headers)
        for private in ("private-peer.example", "100.64.0.2", "private-dashboard.example", "PRIVATE_DAEMON_LOG"):
            self.assertNotIn(private, body)
        self.assertFalse(set(calls) & {"netbird", "hostname", "sed", "tail", "jq"}, calls)

    def test_anonymous_requests_including_loopback_are_denied(self):
        for address in ("127.0.0.1", "192.0.2.10", "100.64.0.3"):
            with self.subTest(address=address):
                self.assert_denied(self.request(HTTP_COOKIE="", QUERY_STRING="", REMOTE_ADDR=address), "401 Unauthorized")

    def test_missing_forged_and_expired_credentials_are_denied(self):
        for cookie, query in (
            ("", "SynoToken=valid-token"),
            ("id=valid-session", ""),
            ("id=expired-session", "SynoToken=valid-token"),
            ("id=valid-session", "SynoToken=forged-token"),
        ):
            with self.subTest(cookie=cookie, query=query):
                self.assert_denied(self.request(HTTP_COOKIE=cookie, QUERY_STRING=query), "401 Unauthorized")

    def test_request_identity_headers_cannot_bypass_dsm_auth(self):
        self.assert_denied(self.request(
            HTTP_COOKIE="", REMOTE_USER="dsm-admin", HTTP_REMOTE_USER="dsm-admin",
            HTTP_X_FORWARDED_USER="dsm-admin", DSM_USER="dsm-admin", DSM_GROUPS="administrators",
        ), "401 Unauthorized")

    def test_authentication_errors_and_empty_identity_fail_closed(self):
        for env in ({"TEST_AUTH_EXIT": "1"}, {"TEST_AUTH_USER": ""}):
            with self.subTest(env=env):
                self.assert_denied(self.request(**env), "401 Unauthorized")
        self.auth.unlink()
        self.assert_denied(self.request(), "401 Unauthorized")

    def test_non_administrators_are_denied(self):
        for groups in ("users", "users administrators-other", "users notadministrators", ""):
            with self.subTest(groups=groups):
                self.assert_denied(self.request(TEST_GROUPS=groups), "403 Forbidden")

    def test_group_lookup_failure_fails_closed_even_with_output(self):
        self.assert_denied(self.request(TEST_GROUP_EXIT="1"), "403 Forbidden")

    def test_authenticated_administrator_can_read_status_and_logs(self):
        for groups in ("administrators", "administrators users", "users administrators other"):
            with self.subTest(groups=groups):
                headers, body, calls = self.request(TEST_GROUPS=groups)
                self.assertNotIn("Status:", headers)
                self.assertIn("private-peer.example", body)
                self.assertIn("PRIVATE_DAEMON_LOG", body)
                self.assertIn("https://private-dashboard.example", body)
                self.assertEqual(calls[:2], ["auth", "groups"])
                self.assertIn("netbird", calls)
                self.assertIn("tail", calls)
                self.assertEqual(self.cli_args.read_text().splitlines(), ["status --json"])

    def test_json_status_fields_are_rendered(self):
        _, body, _ = self.request()
        for value in ("private-peer.example", "100.64.0.2/16", "1 / 3", "2 / 4", "0.80.0", "home"):
            self.assertIn(f'class="value">{value}</span>', body)
        self.assertIn('class="value">Not reported</span>', body)
        self.assertNotIn('class="value">None</span>', body)

    def test_explicit_daemon_states(self):
        for state, label in (
            ("NeedsLogin", "Not Configured"), ("LoginFailed", "Login Required"),
            ("SessionExpired", "Login Required"), ("Connecting", "Connecting"),
            ("Idle", "Disconnected"), ("Connected", "Connected"),
        ):
            with self.subTest(state=state):
                # A stale management flag must not override the daemon state.
                self.status_file.write_text(json.dumps({**self.status, "daemonStatus": state, "management": {"connected": True}}))
                _, body, _ = self.request()
                self.assertIn(f'>{label}</span>', body)
                self.assertEqual('Open Dashboard' in body, state == "Connected")

    def test_invalid_json_does_not_render_connected_data(self):
        for payload in ("", "not json", "{}", "null", "[]", '{"daemonStatus":null}',
                        '{"daemonStatus":false}', '{"daemonStatus":{}}',
                        '{"daemonStatus":""}', json.dumps(self.status) + '\n{}'):
            with self.subTest(payload=payload):
                self.status_file.write_text(payload)
                _, body, _ = self.request()
                self.assertIn('>Status unavailable</span>', body)
                self.assertNotIn('Open Dashboard', body)
                self.assertNotIn('private-peer.example', body)

    def test_cli_failure_does_not_trust_partial_output(self):
        _, body, _ = self.request(TEST_STATUS_EXIT="1")
        self.assertIn('>Status unavailable</span>', body)
        self.assertNotIn('private-peer.example', body)
        self.assertNotIn('Open Dashboard', body)

    def test_missing_or_wrongly_typed_optional_fields_are_unknown(self):
        for payload in (
            {"daemonStatus": "Connected"},
            {"daemonStatus": "Connected", "fqdn": [], "netbirdIp": False,
             "daemonVersion": {}, "profileName": 42,
             "peers": {"connected": -1, "total": "many"},
             "relays": {"available": 1.5, "total": None}},
        ):
            with self.subTest(payload=payload):
                self.status_file.write_text(json.dumps(payload))
                _, body, _ = self.request()
                self.assertIn('>Connected</span>', body)
                self.assertEqual(body.count('class="value">—</span>'), 4)
                self.assertEqual(body.count('class="value">— / —</span>'), 2)

    def test_zero_counts_are_preserved(self):
        self.status.update(peers={"connected": 0, "total": 0}, relays={"available": 0, "total": 0})
        self.status_file.write_text(json.dumps(self.status))
        _, body, _ = self.request()
        self.assertEqual(body.count('class="value">0 / 0</span>'), 2)

    def test_json_values_are_escaped_and_never_executed(self):
        marker = self.base / "injected"
        hostile = f'<script>alert("x")</script> & $(touch {marker})'
        self.status.update(fqdn=hostile, profileName='Home "A" & <office>\nβ')
        self.status_file.write_text(json.dumps(self.status))
        _, body, _ = self.request()
        self.assertNotIn(hostile, body)
        self.assertIn('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;', body)
        self.assertIn('Home &quot;A&quot; &amp; &lt;office&gt;\nβ', body)
        self.assertFalse(marker.exists())
        self.status_file.write_text(json.dumps({"daemonStatus": hostile}))
        _, body, _ = self.request()
        self.assertIn('>Status unavailable</span>', body)
        self.assertNotIn(hostile, body)
        self.assertIn('&lt;script&gt;', body)

    def test_dashboard_config_uses_json_and_http_urls(self):
        config = self.var / "config.json"
        config.write_text('{"AdminURL":"https:\\/\\/dashboard.example/path?x=1&y=\\"two\\""}')
        _, body, _ = self.request()
        self.assertIn('href="https://dashboard.example/path?x=1&amp;y=&quot;two&quot;"', body)
        for payload in ('{"AdminURL":"javascript:alert(1)"}', '{}', 'invalid json'):
            with self.subTest(payload=payload):
                config.write_text(payload)
                _, body, _ = self.request()
                self.assertIn('href="https://app.netbird.io"', body)
                self.assertNotIn('javascript:', body)

    def test_missing_jq_reports_unavailable_without_running_cli(self):
        (self.bin / "jq").unlink()
        _, body, calls = self.request(PATH=str(self.bin))
        self.assertIn('>Status unavailable</span>', body)
        self.assertIn('requires jq', body)
        self.assertNotIn('netbird', calls)


if __name__ == "__main__":
    unittest.main()
