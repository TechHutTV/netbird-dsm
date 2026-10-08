"""Exercise CGI auth, request validation and real HTTP over a private Unix socket.

Only DSM paths and its package account are redirected in the isolated CGI copy.
The HTTP server models the pinned daemon API; no VPN or NAS state is changed.
"""

import contextlib
import fcntl
from http.server import BaseHTTPRequestHandler
import importlib.util
import json
import os
from pathlib import Path
import pwd
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "spk/package/libexec/ui-control.py"
spec = importlib.util.spec_from_file_location("ui_control", CONTROL)
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class Gateway(socketserver.UnixStreamServer):
    def __init__(self, path):
        super().__init__(str(path), Handler)
        self.state = "Idle"
        self.level = "INFO"
        self.calls = []
        self.failed_method = None
        self.invalid_response = None
        self.wait_for_up = False
        self.up_started = threading.Event()
        self.release_up = threading.Event()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        method = self.path.split('/')[-1]
        self.server.calls.append((method, data))
        status = 200
        if method == self.server.failed_method:
            status = 400
            result = {"message": "PRIVATE_RAW_ERROR_WITH_SETUP_KEY"}
        elif method == 'Status':
            result = {"status": self.server.state}
        elif method == 'GetLogLevel':
            result = {'level': self.server.level}
        elif method == 'SetLogLevel':
            self.server.level = data['level']
            result = {}
        elif method == 'Login':
            self.server.state = 'Idle'
            result = {}
        elif method == 'Up':
            self.server.up_started.set()
            if self.server.wait_for_up:
                self.server.release_up.wait(5)
            self.server.state = 'Connected'
            result = {}
        elif method == 'Down':
            self.server.state = 'Idle'
            result = {}
        else:
            status = 404
            result = {}
        body = self.server.invalid_response
        if body is None:
            body = json.dumps(result).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        with contextlib.suppress(BrokenPipeError):
            self.wfile.write(body)

    def log_message(self, *args):
        pass


class UIControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nb-ui-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.var = self.base / 'var'
        self.run = self.var / 'run'
        self.run.mkdir(parents=True, mode=0o700)
        self.config = self.var / 'config.json'
        self.config.write_text('{"PrivateKey":"EXISTING_TEST_IDENTITY"}')
        try:
            self.server = Gateway(self.run / 'netbird-http.sock')
        except PermissionError:
            self.skipTest('This environment blocks Unix socket listeners; run integration tests on DSM or CI.')
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.auth = self.script('authenticate.cgi', '''
[ "$HTTP_COOKIE" = 'id=valid' ] && [ "$HTTP_X_SYNO_TOKEN" = 'valid-token' ] || exit 1
printf 'dsm-admin\n'
''')
        self.identity = self.script('id', '''
[ "$1" = '-nG' ] && [ "$2" = '--' ] && [ "$3" = 'dsm-admin' ] || exit 1
printf '%s\n' "${TEST_GROUPS-users administrators}"
exit "${TEST_GROUP_EXIT-0}"
''')
        source = CONTROL.read_text()
        for old, new in (
            (control.AUTHENTICATE, str(self.auth)),
            (control.IDENTITY, str(self.identity)),
            (str(control.PKGVAR), str(self.var)),
            ('pwd.getpwnam("netbird")', 'pwd.getpwnam({!r})'.format(pwd.getpwuid(os.getuid()).pw_name)),
        ):
            self.assertEqual(source.count(old), 1)
            source = source.replace(old, new)
        # CI normally runs unprivileged; support root-run DSM test runners too.
        if os.geteuid() == 0:
            source = source.replace('if account.pw_uid == 0:', 'if account.pw_uid == -1:')
        self.cgi = self.base / 'control.py'
        self.cgi.write_text(source)
        (self.base / 'ui-diagnostics.py').write_text(CONTROL.with_name('ui-diagnostics.py').read_text())
        self.env = {
            'PATH': os.defpath, 'REQUEST_METHOD': 'POST', 'HTTPS': 'on',
            'HTTP_COOKIE': 'id=valid', 'HTTP_X_SYNO_TOKEN': 'valid-token',
            'HTTP_HOST': 'nas.example:5001', 'HTTP_ORIGIN': 'https://nas.example:5001',
            'HTTP_X_NETBIRD_ACTION': '1', 'HTTP_SEC_FETCH_SITE': 'same-origin',
            'CONTENT_TYPE': 'application/json', 'QUERY_STRING': '',
        }

    def stop_server(self):
        self.server.release_up.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def script(self, name, body):
        path = self.base / name
        path.write_text('#!/bin/sh\n' + body)
        path.chmod(0o700)
        return path

    def request(self, payload=None, raw=None, details=False, **env):
        body = raw if raw is not None else json.dumps(payload or {'action': 'connect'}).encode()
        command = [sys.executable, '-I', '-B', str(self.cgi)] + (['--details'] if details else [])
        result = subprocess.run(command, input=body,
                                env={**self.env, 'CONTENT_LENGTH': str(len(body)), **env},
                                capture_output=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, b'')
        headers, body = result.stdout.decode().split('\r\n\r\n', 1)
        self.assertIn('Cache-Control: no-store', headers)
        self.assertNotIn('Access-Control-Allow-Origin', headers)
        self.assertNotIn('PRIVATE_RAW_ERROR', body)
        self.assertNotIn('EXISTING_TEST_IDENTITY', body)
        self.assertEqual(self.config.read_text(), '{"PrivateKey":"EXISTING_TEST_IDENTITY"}')
        return int(headers.split()[1]), json.loads(body)

    def denied(self, expected, **kwargs):
        status, body = self.request(**kwargs)
        self.assertEqual(status, expected, body)
        self.assertFalse(body['ok'])
        self.assertEqual(self.server.calls, [])

    def test_diagnostics_read_requires_dsm_admin_but_allows_http(self):
        self.assertEqual(self.request(details=True, REQUEST_METHOD='GET', HTTP_COOKIE='')[0], 401)
        self.assertEqual(self.request(details=True, REQUEST_METHOD='GET', TEST_GROUPS='users')[0], 403)
        self.assertEqual(self.server.calls, [])
        status, data = self.request(details=True, REQUEST_METHOD='GET', HTTPS='off')
        self.assertEqual(status, 200)
        self.assertTrue(data['ok'])
        self.assertEqual(data['logLevel'], 'INFO')
        self.assertEqual(self.server.calls, [('Status', {'getFullPeerStatus': True}), ('GetLogLevel', {})])

    def test_diagnostics_actions_use_the_same_request_protection(self):
        for action in ({'action': 'debug-start'}, {'action': 'bundle-create', 'destination': 'support'}):
            for changes in ({'HTTP_COOKIE': ''}, {'HTTP_X_SYNO_TOKEN': 'forged'},
                            {'HTTP_ORIGIN': 'https://evil.example'}, {'HTTPS': 'off'}):
                self.assertIn(self.request(action, **changes)[0], (401, 403))
        self.assertEqual(self.server.calls, [])

    def test_real_debug_worker_can_start_and_stop_without_connection_changes(self):
        try:
            status, _ = self.request({'action': 'debug-start'})
            self.assertEqual(status, 200)
            self.assertEqual(self.server.level, 'DEBUG')
            self.assertEqual(self.request({'action': 'debug-start'})[0], 409)
        finally:
            self.assertEqual(self.request({'action': 'debug-stop'})[0], 200)
        self.assertEqual(self.server.level, 'INFO')
        self.assertFalse(any(method in {'Login', 'Up', 'Down'} for method, _ in self.server.calls))

    def test_unauthenticated_and_expired_sessions_never_reach_daemon(self):
        for env in ({'HTTP_COOKIE': ''}, {'HTTP_COOKIE': 'id=expired'},
                    {'HTTP_X_SYNO_TOKEN': ''}, {'HTTP_X_SYNO_TOKEN': 'forged'}):
            with self.subTest(env=env):
                self.denied(401, **env)
        self.auth.unlink()
        self.denied(401)

    def test_nonadmins_and_failed_group_lookup_are_denied(self):
        for groups in ('users', 'users administrators-other', '', 'notadministrators'):
            with self.subTest(groups=groups):
                self.denied(403, TEST_GROUPS=groups)
        self.denied(403, TEST_GROUP_EXIT='1')

    def test_mutations_require_post_https_same_origin_and_custom_header(self):
        for method in ('GET', 'OPTIONS', 'PUT', 'HEAD'):
            self.denied(405, REQUEST_METHOD=method)
        for env in ({'HTTPS': ''}, {'HTTPS': 'off', 'HTTP_X_FORWARDED_PROTO': 'https'},
                    {'HTTP_ORIGIN': 'https://evil.example'}, {'HTTP_ORIGIN': 'null'},
                    {'HTTP_ORIGIN': ''}, {'HTTP_ORIGIN': 'https://nas.example'},
                    {'HTTP_X_NETBIRD_ACTION': ''}, {'HTTP_SEC_FETCH_SITE': 'cross-site'},
                    {'HTTP_HOST': 'nas.example:5001/evil'}, {'QUERY_STRING': 'action=connect'}):
            with self.subTest(env=env):
                self.denied(403, **env)

    def test_json_and_bounded_complete_body_required(self):
        self.denied(415, CONTENT_TYPE='application/x-www-form-urlencoded')
        for size in ('', '0', '-1', '4097', '10000000000000000', 'n/a'):
            self.denied(413, CONTENT_LENGTH=size)
        self.denied(400, CONTENT_LENGTH='100')
        for raw in (b'{', b'[]', b'null', b'{}', b'{}{}', b'\xff',
                    b'{"action":"connect","action":"disconnect"}',
                    b'{"action": ["connect"]}'):
            self.denied(400, raw=raw)

    def test_arbitrary_actions_flags_and_enrollment_fields_rejected(self):
        for payload in ({'action': 'service-start'}, {'action': 'Logout'},
                        {'action': 'connect', 'managementUrl': 'https://evil.example'},
                        {'action': 'enroll', 'setupKey': 'x'},
                        {'action': 'connect; touch /tmp/unwanted'}):
            self.denied(400, payload=payload)
        for url in ('http://example.com', 'https://user:secret@example.com',
                    'https://example.com/path', 'https://example.com?token=secret',
                    'https://example.com/#x', 'https://bad\nhost', 'https://',
                    'https://example.com:70000', 'https://example.com\\@evil.example'):
            self.denied(400, payload={'action': 'enroll', 'setupKey': '01234567-89ab-4def-8123-456789abcdef', 'managementUrl': url})
        self.denied(400, payload={'action': 'enroll', 'setupKey': '$(touch /tmp/unwanted)',
                                 'managementUrl': 'https://example.com'})

    def test_connect_and_disconnect_use_fixed_rpc_and_preserve_identity(self):
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.server.calls, [('Status', {}), ('Up', {'async': True}), ('Status', {})])
        self.server.calls.clear()
        self.assertEqual(self.request({'action': 'disconnect'})[0], 200)
        self.assertEqual(self.server.calls, [('Status', {}), ('Down', {}), ('Status', {})])
        self.assertEqual((self.var / '.ui-action.lock').stat().st_mode & 0o777, 0o600)

    def test_enrollment_sends_only_setup_key_and_management_url(self):
        self.server.state = 'NeedsLogin'
        key = '01234567-89ab-4def-8123-456789abcdef'
        status, result = self.request({'action': 'enroll', 'setupKey': key,
                                       'managementUrl': 'https://management.example:8443/'})
        self.assertEqual(status, 200, result)
        self.assertNotIn(key, json.dumps(result))
        self.assertEqual(self.server.calls, [('Status', {}), ('Login', {
            'setupKey': key, 'managementUrl': 'https://management.example:8443'}),
            ('Up', {'async': True}), ('Status', {})])
        self.assertEqual({p.name for p in self.var.iterdir()}, {'config.json', 'run', '.ui-action.lock'})

    def test_existing_enrollment_cannot_be_replaced(self):
        for state in ('Idle', 'Connected', 'Connecting'):
            self.server.state = state
            self.server.calls.clear()
            status, _ = self.request({'action': 'enroll', 'setupKey': '01234567-89ab-4def-8123-456789abcdef',
                                      'managementUrl': 'https://management.example'})
            self.assertEqual(status, 409)
            self.assertEqual(self.server.calls, [('Status', {})])

    def test_repeated_connect_disconnect_and_unenrolled_connect(self):
        for action, state, expected in (('connect', 'Connected', 200), ('connect', 'Connecting', 200),
                                        ('disconnect', 'Idle', 200), ('disconnect', 'NeedsLogin', 200),
                                        ('connect', 'NeedsLogin', 409)):
            self.server.state = state
            self.server.calls.clear()
            self.assertEqual(self.request({'action': action})[0], expected)
            self.assertEqual(self.server.calls, [('Status', {})])

    def test_raw_daemon_errors_and_invalid_responses_are_not_returned(self):
        self.server.state = 'NeedsLogin'
        self.server.failed_method = 'Login'
        status, _ = self.request({'action': 'enroll', 'setupKey': '01234567-89ab-4def-8123-456789abcdef',
                                  'managementUrl': 'https://management.example'})
        self.assertEqual(status, 400)
        self.assertNotIn('Up', [method for method, _ in self.server.calls])
        self.server.failed_method = None
        for response, expected in ((b'[]', 503), (b'not json', 503), (b'x' * 65537, 502)):
            self.server.invalid_response = response
            self.assertEqual(self.request()[0], expected)

    def test_missing_or_public_socket_directory_is_rejected(self):
        self.run.chmod(0o755)
        self.denied(503)
        self.run.chmod(0o700)
        (self.run / 'netbird-http.sock').unlink()
        self.denied(503)

    def test_symlink_socket_directory_and_lock_are_rejected(self):
        private = self.var / 'other'
        self.run.rename(private)
        self.run.symlink_to(private, target_is_directory=True)
        self.denied(503)
        self.run.unlink()
        private.rename(self.run)
        (self.var / '.ui-action.lock').unlink()
        (self.var / '.ui-action.lock').symlink_to(self.config)
        self.denied(503)

    def test_concurrent_request_is_rejected_and_lock_recovers(self):
        self.server.wait_for_up = True
        result = []
        worker = threading.Thread(target=lambda: result.append(self.request()))
        worker.start()
        try:
            self.assertTrue(self.server.up_started.wait(3))
            status, _ = self.request({'action': 'disconnect'})
            self.assertEqual(status, 409)
        finally:
            self.server.release_up.set()
            worker.join(5)
        self.assertEqual(result[0][0], 200)
        self.assertEqual(self.request({'action': 'disconnect'})[0], 200)

    def test_drop_privileges_precedes_daemon_access(self):
        with patch.object(control, 'become_package_user', side_effect=control.ControlError(503, 'identity failure')), \
             patch.object(control, 'daemon_state') as daemon:
            with self.assertRaises(control.ControlError):
                control.perform({'action': 'connect'})
            daemon.assert_not_called()


class UIControlValidationTests(unittest.TestCase):
    """Run independently of the transport so validation can be checked offline."""

    def setUp(self):
        self.env = {
            'REQUEST_METHOD': 'POST', 'HTTPS': 'on', 'HTTP_X_SYNO_TOKEN': 'valid',
            'HTTP_HOST': 'nas.example:5001', 'HTTP_ORIGIN': 'https://nas.example:5001',
            'HTTP_X_NETBIRD_ACTION': '1', 'HTTP_SEC_FETCH_SITE': 'same-origin',
            'CONTENT_TYPE': 'application/json', 'CONTENT_LENGTH': '20',
        }

    def test_request_validation(self):
        self.assertEqual(control.check_request(self.env), 20)
        for changes, code in (({'REQUEST_METHOD': 'GET'}, 405), ({'REQUEST_METHOD': 'OPTIONS'}, 405),
                              ({'HTTPS': 'off', 'HTTP_X_FORWARDED_PROTO': 'https'}, 403),
                              ({'HTTP_ORIGIN': 'https://evil.example'}, 403),
                              ({'HTTP_ORIGIN': ''}, 403), ({'HTTP_ORIGIN': 'null'}, 403),
                              ({'HTTP_X_SYNO_TOKEN': ''}, 403), ({'HTTP_X_NETBIRD_ACTION': ''}, 403),
                              ({'HTTP_SEC_FETCH_SITE': 'cross-site'}, 403),
                              ({'HTTP_HOST': 'nas.example/evil'}, 403),
                              ({'QUERY_STRING': 'setupKey=secret'}, 403),
                              ({'CONTENT_TYPE': 'text/plain'}, 415),
                              ({'CONTENT_LENGTH': '4097'}, 413), ({'CONTENT_LENGTH': '-1'}, 413)):
            with self.subTest(changes=changes):
                with self.assertRaises(control.ControlError) as error:
                    control.check_request({**self.env, **changes})
                self.assertEqual(error.exception.status, code)

    def test_action_fields_and_json_are_strict(self):
        for action in ('connect', 'disconnect'):
            self.assertEqual(control.parse_request(json.dumps({'action': action}).encode()), {'action': action})
        for raw in (b'[]', b'null', b'{}{}', b'\xff', b'{"action":false}',
                    b'{"action":"connect","action":"disconnect"}',
                    b'{"action":"connect","args":["--foreground-mode"]}',
                    b'{"action":"Logout"}', b'{"action":"$(touch /tmp/unwanted)"}'):
            with self.subTest(raw=raw), self.assertRaises(control.ControlError):
                control.parse_request(raw)

    def test_enrollment_url_and_key_validation(self):
        payload = {'action': 'enroll', 'setupKey': '01234567-89ab-4def-8123-456789abcdef', 'managementUrl': 'https://example.com/'}
        self.assertEqual(control.parse_request(json.dumps(payload).encode())['managementUrl'], 'https://example.com')
        for url in ('http://example.com', 'https://u:p@example.com', 'https://example.com/path',
                    'https://example.com/?token=x', 'https://bad\nhost', 'https://',
                    'https://example.com:70000', 'https://example.com\\@evil.example'):
            with self.subTest(url=url), self.assertRaises(control.ControlError):
                control.parse_request(json.dumps({**payload, 'managementUrl': url}).encode())
        for key in ('', 'short', 'key with spaces 123456', '$(touch /tmp/key)', 'x' * 257):
            with self.subTest(key=key), self.assertRaises(control.ControlError):
                control.parse_request(json.dumps({**payload, 'setupKey': key}).encode())
        self.assertEqual(control.https_origin('https://[2001:db8::1]:8443'), 'https://[2001:db8::1]:8443')

    def test_authentication_failures_and_nonadmins(self):
        valid = subprocess.CompletedProcess([], 0, stdout=b'dsm-admin\n')
        groups = subprocess.CompletedProcess([], 0, stdout=b'users administrators\n')
        with patch.object(control.subprocess, 'run', side_effect=[valid, groups]) as runner:
            control.authenticate(self.env)
            self.assertEqual(runner.call_args_list[1].args[0], [control.IDENTITY, '-nG', '--', 'dsm-admin'])
        for failure in (FileNotFoundError(), subprocess.CalledProcessError(1, 'auth'),
                        subprocess.TimeoutExpired('auth', 5)):
            with patch.object(control.subprocess, 'run', side_effect=failure), self.assertRaises(control.ControlError) as error:
                control.authenticate(self.env)
            self.assertEqual(error.exception.status, 401)
        for output in (b'', b'users\n', b'users notadministrators\n'):
            with patch.object(control.subprocess, 'run', side_effect=[valid, subprocess.CompletedProcess([], 0, stdout=output)]), \
                 self.assertRaises(control.ControlError) as error:
                control.authenticate(self.env)
            self.assertEqual(error.exception.status, 403)

    def test_privileges_are_dropped_and_wrong_account_fails_closed(self):
        account = pwd.struct_passwd(('netbird', 'x', 1234, 5678, '', '/', '/bin/sh'))
        events = []
        with patch.object(control.pwd, 'getpwnam', return_value=account), \
             patch.object(control.os, 'geteuid', side_effect=[0, 1234]), \
             patch.object(control.os, 'getuid', return_value=1234), \
             patch.object(control.os, 'getgid', return_value=5678), \
             patch.object(control.os, 'getegid', return_value=5678), \
             patch.object(control.os, 'setgroups', side_effect=lambda value: events.append(('groups', value))), \
             patch.object(control.os, 'setgid', side_effect=lambda value: events.append(('gid', value))), \
             patch.object(control.os, 'setuid', side_effect=lambda value: events.append(('uid', value))), \
             patch.object(control.os, 'umask'):
            control.become_package_user()
        self.assertEqual(events, [('groups', []), ('gid', 5678), ('uid', 1234)])
        with patch.object(control.pwd, 'getpwnam', return_value=account), \
             patch.object(control.os, 'geteuid', return_value=9000), \
             patch.object(control.os, 'getuid', return_value=9000), \
             self.assertRaises(control.ControlError):
            control.become_package_user()

    def test_request_body_is_bounded_and_truncation_is_rejected(self):
        with tempfile.TemporaryFile() as body:
            body.write(b'{"action":"connect"}')
            body.seek(0)
            self.assertEqual(control.read_body(body, 20), b'{"action":"connect"}')
            body.seek(0)
            with self.assertRaises(control.ControlError):
                control.read_body(body, 21)

    def test_connection_flow_and_enrollment_keep_config_and_secrets_out_of_files(self):
        with tempfile.TemporaryDirectory() as directory:
            var = Path(directory)
            config = var / 'config.json'
            config.write_text('SAVED_ENROLLMENT')
            calls = []
            state = ['Idle']

            def rpc(method, payload=None, timeout=25):
                calls.append((method, payload))
                if method == 'Status':
                    return {'status': state[0]}
                if method == 'Up':
                    state[0] = 'Connected'
                if method in ('Down', 'Login'):
                    state[0] = 'Idle'
                return {}

            with patch.object(control, 'PKGVAR', var), \
                 patch.object(control, 'become_package_user') as identity, \
                 patch.object(control, 'daemon_request', side_effect=rpc):
                self.assertTrue(control.perform({'action': 'connect'})['ok'])
                identity.assert_called_once()
                self.assertEqual(calls, [('Status', None), ('Up', {'async': True}), ('Status', None)])
                calls.clear()
                self.assertTrue(control.perform({'action': 'disconnect'})['ok'])
                self.assertEqual(calls, [('Status', None), ('Down', {}), ('Status', None)])
                state[0] = 'NeedsLogin'
                calls.clear()
                key = '01234567-89ab-4def-8123-456789abcdef'
                result = control.perform({'action': 'enroll', 'setupKey': key, 'managementUrl': 'https://example.com'})
                self.assertTrue(result['ok'])
                self.assertNotIn(key, json.dumps(result))
                self.assertEqual(calls, [('Status', None), ('Login', {
                    'setupKey': key, 'managementUrl': 'https://example.com'}), ('Up', {'async': True}), ('Status', None)])
                calls.clear()
                with self.assertRaises(control.ControlError) as error:
                    control.perform({'action': 'enroll', 'setupKey': key, 'managementUrl': 'https://example.com'})
                self.assertEqual(error.exception.status, 409)
                self.assertEqual(calls, [('Status', None)])
            self.assertEqual(config.read_text(), 'SAVED_ENROLLMENT')
            self.assertEqual({p.name for p in var.iterdir()}, {'config.json', '.ui-action.lock'})

    def test_lock_blocks_overlapping_actions_and_is_released_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            var = Path(directory)
            lock = var / '.ui-action.lock'
            with patch.object(control, 'PKGVAR', var), \
                 patch.object(control, 'become_package_user'), \
                 patch.object(control, 'daemon_state', side_effect=control.ControlError(503, 'not ready')) as daemon:
                with lock.open('w') as held:
                    fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    with self.assertRaises(control.ControlError) as error:
                        control.perform({'action': 'connect'})
                    self.assertEqual(error.exception.status, 409)
                    daemon.assert_not_called()
                with self.assertRaises(control.ControlError) as error:
                    control.perform({'action': 'connect'})
                self.assertEqual(error.exception.status, 503)
                with lock.open('r') as released:
                    fcntl.flock(released, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_lock_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            var = Path(directory)
            config = var / 'config.json'
            config.write_text('SAVED_ENROLLMENT')
            (var / '.ui-action.lock').symlink_to(config)
            with patch.object(control, 'PKGVAR', var), \
                 patch.object(control, 'become_package_user'), \
                 patch.object(control, 'daemon_state') as daemon:
                with self.assertRaises(control.ControlError) as error:
                    control.perform({'action': 'connect'})
                self.assertEqual(error.exception.status, 503)
                daemon.assert_not_called()
            self.assertEqual(config.read_text(), 'SAVED_ENROLLMENT')


if __name__ == '__main__':
    unittest.main()
