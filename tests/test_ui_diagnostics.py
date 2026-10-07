"""Diagnostics filtering, upload consent, private files, and timer recovery."""

import contextlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("diagnostics_control", ROOT / "spk/package/libexec/ui-control.py")
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)
diag = control.diagnostics()


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.var = Path(self.temp.name)
        (self.var / 'run').mkdir(mode=0o700)
        (self.var / 'run/netbird-http.sock').touch()
        self.level = 'INFO'
        self.calls = []
        self.status = {'status': 'Connected', 'fullStatus': {}}
        self.bundle_result = {}
        self.api = control.diagnostics_api()
        self.api.var = self.var
        self.api.rpc = self.rpc
        self.api.lock = contextlib.nullcontext

    def rpc(self, method, payload=None, timeout=25):
        self.calls.append((method, payload))
        if method == 'Status': return self.status
        if method == 'GetLogLevel': return {'level': self.level}
        if method == 'SetLogLevel': self.level = payload['level']; return {}
        if method == 'DebugBundle': return self.bundle_result
        raise AssertionError(method)

    def start_debug(self):
        with patch.object(diag, 'spawn'):
            diag.action({'action': 'debug-start'}, self.api)
        return diag.read_state(self.api, 'debug')

    def bundle_file(self):
        path = Path('/tmp/netbird.debug.{}.zip'.format(uuid.uuid4().int))
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with zipfile.ZipFile(str(path), 'w') as archive:
            archive.writestr('README.txt', 'Anonymized fixture')
        self.addCleanup(lambda: path.unlink() if path.exists() or path.is_symlink() else None)
        return path

    def run_bundle(self, upload=False, **result):
        path = self.bundle_file()
        job = uuid.uuid4().hex
        diag.save_state(self.api, 'bundle', {'id': job, 'state': 'running', 'upload': upload, 'started': time.time()})
        self.bundle_result = {'path': str(path), **result}
        diag.worker('bundle', job, self.api)
        return diag.read_state(self.api, 'bundle')

    def test_only_fixed_diagnostics_actions_and_destinations_are_accepted(self):
        for payload in ({'action': 'debug-start'}, {'action': 'debug-stop'},
                        {'action': 'bundle-create', 'destination': 'support'},
                        {'action': 'bundle-create', 'destination': 'local'},
                        {'action': 'bundle-download', 'id': 'a' * 32}):
            self.assertEqual(control.parse_request(json.dumps(payload).encode()), payload)
        for payload in ({'action': 'SetLogLevel', 'level': 'TRACE'},
                        {'action': 'debug-start', 'seconds': '1'},
                        {'action': 'bundle-create', 'destination': 'https://evil.example'},
                        {'action': 'bundle-create', 'destination': 'support', 'anonymize': 'false'},
                        {'action': 'bundle-download', 'id': '../../config.json'},
                        {'action': 'bundle-download', 'path': '/etc/shadow'}):
            with self.subTest(payload=payload), self.assertRaises(control.ControlError):
                control.parse_request(json.dumps(payload).encode())

    def test_details_only_expose_selected_status_fields(self):
        self.status['fullStatus'] = {
            'managementState': {'URL': 'https://u:secret@server', 'connected': True, 'error': 'PRIVATE_ERROR'},
            'signalState': {'connected': False}, 'privateKey': 'PRIVATE_KEY',
            'relays': [{'available': True, 'URI': 'secret-relay', 'transport': 'quic'}],
            'peers': [{'fqdn': '<img onerror=alert(1)>', 'IP': '100.64.0.2', 'connStatus': 'Connected',
                       'relayed': True, 'bytesRx': '123', 'bytesTx': '456', 'latency': '0.004s',
                       'pubKey': 'PRIVATE_PUBKEY', 'sshHostKey': 'PRIVATE_SSH'}]}
        data = diag.details(self.api)
        self.assertTrue(data['health']['management']['connected'])
        self.assertEqual(data['peers'][0]['connection'], 'Relayed')
        self.assertEqual(data['peers'][0]['received'], '123')
        self.assertEqual(self.calls[0], ('Status', {'getFullPeerStatus': True}))
        for secret in ('PRIVATE_', 'secret-relay', 'u:secret'):
            self.assertNotIn(secret, json.dumps(data))

    def test_peer_lists_and_strings_are_bounded_and_bad_fields_ignored(self):
        self.status['fullStatus'] = {'peers': [None, 'bad'] + [{'fqdn': 'x' * 1024, 'IP': {}, 'bytesTx': -1}] * 501,
                                    'relays': None, 'signalState': 'bad'}
        result = diag.details(self.api)
        self.assertEqual(len(result['peers']), 500)
        self.assertEqual(result['peerTotal'], 501)
        self.assertEqual(len(result['peers'][0]['name']), 256)
        self.assertEqual(result['peers'][0]['ip'], '')
        self.assertEqual(result['peers'][0]['sent'], '')

    def test_bundle_progress_does_not_wait_for_busy_daemon_status(self):
        diag.save_state(self.api, 'bundle', {'id': 'a' * 32, 'state': 'running', 'started': time.time()})
        data = diag.details(self.api)
        self.assertTrue(data['collecting'])
        self.assertEqual(data['bundle']['state'], 'running')
        self.assertEqual(self.calls, [])

    def test_bundle_result_remains_available_when_daemon_stops(self):
        diag.save_state(self.api, 'bundle', {'id': 'a' * 32, 'state': 'complete', 'download': True})
        with patch.object(self.api, 'rpc', side_effect=control.ControlError(503, 'offline')):
            data = diag.details(self.api)
        self.assertTrue(data['unavailable'])
        self.assertTrue(data['bundle']['download'])

    def test_stale_job_is_reported_as_failure_even_if_daemon_is_unavailable(self):
        diag.save_state(self.api, 'bundle', {'id': 'a' * 32, 'state': 'running', 'started': time.time() - 301})
        with patch.object(self.api, 'rpc', side_effect=control.ControlError(503, 'offline')):
            data = diag.details(self.api)
        self.assertEqual(data['bundle']['state'], 'error')

    def test_logs_are_bounded_and_symlinks_are_not_read(self):
        path = self.var / 'netbird.log'
        path.write_text(('INFO ' + 'x' * 4000 + '\n') * 300)
        path.chmod(0o600)
        lines = diag.recent_logs(self.api)
        self.assertLessEqual(len(lines), 200)
        self.assertTrue(all(len(line) <= 2048 for line in lines))
        path.unlink()
        path.symlink_to('/etc/passwd')
        self.assertEqual(diag.recent_logs(self.api), [])

    def test_temporary_debug_restores_previous_level_at_expiry(self):
        self.level = 'WARN'
        current = self.start_debug()
        self.assertEqual(self.level, 'DEBUG')
        self.assertAlmostEqual(current['expires'] - time.time(), 600, delta=3)
        with patch.object(diag.time, 'time', return_value=current['expires'] + 1):
            diag.worker('debug', current['id'], self.api)
        self.assertEqual(self.level, 'WARN')
        self.assertEqual(diag.read_state(self.api, 'debug')['state'], 'restored')

    def test_early_stop_and_duplicate_start(self):
        self.start_debug()
        with self.assertRaises(control.ControlError) as error:
            diag.action({'action': 'debug-start'}, self.api)
        self.assertEqual(error.exception.status, 409)
        diag.action({'action': 'debug-stop'}, self.api)
        self.assertEqual(self.level, 'INFO')

    def test_debug_does_not_change_restarted_daemon_or_external_log_level(self):
        current = self.start_debug()
        with patch.object(diag, 'daemon_identity', return_value=[99, 99]):
            diag.worker('debug', current['id'], self.api)
        self.assertEqual(self.level, 'DEBUG')  # no SetLogLevel for the replacement
        self.assertEqual(diag.read_state(self.api, 'debug')['state'], 'restored')
        self.start_debug()
        self.level = 'ERROR'
        diag.action({'action': 'debug-stop'}, self.api)
        self.assertEqual(self.level, 'ERROR')

    def test_failure_to_spawn_debug_timer_restores_level(self):
        with patch.object(diag, 'spawn', side_effect=OSError('spawn failed')), self.assertRaises(OSError):
            diag.action({'action': 'debug-start'}, self.api)
        self.assertEqual(self.level, 'INFO')
        self.assertEqual(diag.read_state(self.api, 'debug')['state'], 'restored')

    def test_worker_environment_has_no_request_secrets(self):
        with patch.object(diag.subprocess, 'Popen') as start:
            diag.spawn(self.api, 'debug', 'a' * 32)
        args, kwargs = start.call_args
        self.assertEqual(args[0][-3:], ['--worker', 'debug', 'a' * 32])
        self.assertEqual(kwargs['env'], {'PATH': '/usr/bin:/bin'})
        self.assertTrue(kwargs['close_fds'])
        self.assertTrue(kwargs['start_new_session'])

    def test_local_bundle_is_anonymized_and_never_uploads(self):
        result = self.run_bundle()
        self.assertTrue(result['download'])
        self.assertEqual(self.calls, [('DebugBundle', {'anonymize': True, 'anonymizeLevel': 'strict',
                                                      'systemInfo': True, 'logFileCount': 1})])
        self.assertNotIn('supportCode', result)
        download = diag.action({'action': 'bundle-download', 'id': result['id']}, self.api)
        with download['_download'] as file:
            self.assertTrue(zipfile.is_zipfile(file))
        with self.assertRaises(control.ControlError):
            diag.action({'action': 'bundle-download', 'id': 'b' * 32}, self.api)

    def test_support_code_is_only_shown_for_successful_fixed_endpoint_upload(self):
        code = 'a' * 64 + '/' + str(uuid.uuid4())
        result = self.run_bundle(upload=True, uploadedKey=code)
        self.assertEqual(result['supportCode'], code)
        self.assertEqual(self.calls[-1][1]['uploadURL'], diag.SUPPORT_URL)
        self.assertNotIn('uploadInsecure', self.calls[-1][1])

    def test_upload_failure_keeps_download_and_hides_raw_error_and_false_code(self):
        result = self.run_bundle(upload=True, uploadedKey='a/b', uploadFailureReason='PRIVATE_TOKEN_AND_URL')
        self.assertTrue(result['download'])
        self.assertNotIn('supportCode', result)
        self.assertNotIn('PRIVATE_TOKEN', json.dumps(result))
        self.assertIn('could not be confirmed', result['message'])

    def test_invalid_support_code_is_not_rendered(self):
        result = self.run_bundle(upload=True, uploadedKey='<script>alert(1)</script>')
        self.assertNotIn('supportCode', result)
        self.assertTrue(result['download'])

    def test_bundle_request_cannot_overlap_or_leak_previous_result(self):
        diag.save_state(self.api, 'bundle', {'state': 'running', 'started': time.time()})
        with self.assertRaises(control.ControlError) as error:
            diag.action({'action': 'bundle-create', 'destination': 'support'}, self.api)
        self.assertEqual(error.exception.status, 409)
        diag.save_state(self.api, 'bundle', {'state': 'complete', 'supportCode': 'OLD/CODE', 'download': True})
        with patch.object(diag, 'spawn'):
            diag.action({'action': 'bundle-create', 'destination': 'local'}, self.api)
        current = diag.read_state(self.api, 'bundle')
        self.assertNotIn('supportCode', current)
        self.assertNotIn('download', current)
        self.assertFalse(current['upload'])

    def test_arbitrary_paths_symlinks_and_overlarge_archives_are_rejected(self):
        with self.assertRaises(ValueError):
            diag.keep_bundle(self.api, '/etc/shadow')
        path = self.bundle_file()
        path.unlink()
        path.symlink_to('/etc/passwd')
        with self.assertRaises(OSError):
            diag.keep_bundle(self.api, str(path))
        path.unlink()
        path.touch(mode=0o600)
        with path.open('wb') as file:
            file.truncate(diag.MAX_BUNDLE + 1)
        with self.assertRaises(ValueError):
            diag.keep_bundle(self.api, str(path))

    def test_diagnostics_directory_and_files_stay_private(self):
        diag.save_state(self.api, 'bundle', {'state': 'running'})
        folder = diag.directory(self.api)
        self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
        self.assertEqual((folder / 'bundle.json').stat().st_mode & 0o777, 0o600)
        (folder / 'bundle.json').unlink()
        (folder / 'bundle.json').symlink_to('/etc/passwd')
        with self.assertRaises(OSError): diag.read_state(self.api, 'bundle')
        (self.var / 'run').chmod(0o755)
        with self.assertRaises(control.ControlError): diag.directory(self.api)


if __name__ == '__main__':
    unittest.main()
