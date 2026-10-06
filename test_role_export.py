import json
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from roles.export_role import export
from roles.containers import entrypoint, reader_bridge


class RoleExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        (self.root / 'roles').mkdir(parents=True)
        (self.root / 'shared.py').write_text('VALUE = 1\n')
        (self.root / 'private.json').write_text('{"secret":"not exported"}')
        self.destination = Path(self.temp.name) / 'export'

    def manifest(self, value):
        (self.root / 'roles/source-map.json').write_text(json.dumps({'analysis': value}))

    def test_shared_source_is_materialized_without_unlisted_data_or_overwrite(self):
        self.manifest({'telegram_reader/shared.py': 'shared.py'})
        result = export('analysis', self.destination, self.root)
        self.assertEqual(1, result['files'])
        self.assertEqual('VALUE = 1\n', (self.destination / 'telegram_reader/shared.py').read_text())
        self.assertFalse((self.destination / 'private.json').exists())
        with self.assertRaises(FileExistsError):
            export('analysis', self.destination, self.root)

    def test_invalid_paths_and_symlink_sources_do_not_create_destination(self):
        for value in ({'../escape.py': 'shared.py'}, {'shared.py': '../private.json'}):
            self.manifest(value)
            with self.assertRaises(ValueError):
                export('analysis', self.destination, self.root)
            self.assertFalse(self.destination.exists())
        (self.root / 'alias.py').symlink_to('shared.py')
        self.manifest({'shared.py': 'alias.py'})
        with self.assertRaises(ValueError):
            export('analysis', self.destination, self.root)
        self.assertFalse(self.destination.exists())

    def test_analysis_composes_core_owned_manifest_and_rejects_overlap(self):
        self.manifest({'telegram_reader/shared.py': 'shared.py'})
        (self.root / '.gitmodules').write_text('[submodule "core"]\n')
        core = self.root / 'core/btc-core-strategy'; core.mkdir(parents=True)
        (core / 'export-manifest.json').write_text(json.dumps({'files': ['method.md']}))
        (core / 'method.md').write_text('model method')
        export('analysis', self.destination, self.root)
        self.assertEqual((self.destination / 'method.md').read_text(), 'model method')
        self.manifest({'method.md': 'shared.py'})
        with self.assertRaisesRegex(ValueError, 'overlap'):
            export('analysis', self.destination.with_name('other'), self.root)

    def test_missing_core_dependency_has_no_local_skill_fallback(self):
        self.manifest({'telegram_reader/shared.py': 'shared.py'})
        (self.root / '.gitmodules').write_text('[submodule "core"]\n')
        with self.assertRaisesRegex(FileNotFoundError, 'submodule'):
            export('analysis', self.destination, self.root)

    def test_actual_roles_export_the_same_seller_contract(self):
        repository = Path(__file__).resolve().parent
        expected = (repository / 'seller_exhaustion.py').read_bytes()
        for role, relative in (('collector', 'seller_exhaustion.py'),
                               ('analysis', 'telegram_reader/seller_exhaustion.py')):
            target = Path(self.temp.name) / role
            export(role, target, repository)
            self.assertEqual((target / relative).read_bytes(), expected)
            self.assertFalse((target / relative).is_symlink())

    def test_container_reader_forwards_options_and_keeps_default_sync(self):
        for arguments, expected in ((['collector-observations', '--asset', 'all'],
                                    ['collector-observations', '--asset', 'all']), ([], ['sync'])):
            with patch('sys.argv', ['entrypoint.py', 'reader', *arguments]), patch.object(entrypoint.os, 'execve') as execute:
                entrypoint.main()
            self.assertEqual(execute.call_args.args[1][1:], ['/app/telegram_reader/reader.py', *expected])
            self.assertEqual(execute.call_args.args[2]['BTC_READER_TOKEN_STDIN'], '1')

    def test_reader_checkpoint_reports_phase_and_safe_service_failure(self):
        private = 'credential-and-private-path-must-not-appear'
        for error, message, reason in (
            ('Conflict', 'another node writer is active; retry the same operation', 'WRITER_BUSY'),
            ('Conflict', 'source changed during catalog import: '+private, 'SOURCE_CHANGED'),
            ('OperationalError', private, 'SERVICE_REJECTED'),
            (private, private, 'SERVICE_REJECTED'),
        ):
            output = io.StringIO()
            result = SimpleNamespace(returncode=1, stdout=json.dumps(
                {'ok':False,'error':error,'message':message}), stderr=private)
            with patch.object(reader_bridge.subprocess, 'run', return_value=result), patch('sys.stderr', output), \
                    patch.object(reader_bridge.time, 'sleep') as sleep:
                with self.assertRaisesRegex(RuntimeError, 'do not acknowledge'):
                    reader_bridge.checkpoint(['docker'], 'BEFORE_POLL')
            events = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(len(events), 3 if reason == 'WRITER_BUSY' else 1)
            self.assertEqual(sleep.call_count, len(events) - 1)
            self.assertEqual([e['retry'] for e in events], [True]*(len(events)-1)+[False])
            event = events[-1]
            self.assertEqual(event['reason'], reason)
            self.assertEqual(event['phase'], 'BEFORE_POLL')
            self.assertTrue(event['started_at'].endswith('+00:00'))
            self.assertTrue(event['finished_at'].endswith('+00:00'))
            self.assertNotIn(private, output.getvalue())

    def test_reader_checkpoint_rejects_malformed_or_unconfirmed_success(self):
        for value in ('not-json', '[]', '{"ok":true}', '{"ok":true,"result":{"checkpointed":false}}'):
            with patch.object(reader_bridge.subprocess, 'run', return_value=SimpleNamespace(
                    returncode=0, stdout=value, stderr='')), patch('sys.stderr', io.StringIO()):
                with self.assertRaises(RuntimeError):
                    reader_bridge.checkpoint(['docker'], 'AFTER_POLL')
        output = io.StringIO()
        with patch.object(reader_bridge.subprocess, 'run', side_effect=FileNotFoundError(2, 'private path')), patch('sys.stderr', output):
            with self.assertRaises(RuntimeError):
                reader_bridge.checkpoint(['missing-docker'], 'BEFORE_POLL')
        self.assertEqual(json.loads(output.getvalue())['reason'], 'PROCESS_START_FAILED')
        self.assertNotIn('private path', output.getvalue())

    def test_reader_bridge_never_polls_after_failed_checkpoint(self):
        config = Path(self.temp.name)/'node.json'
        config.write_text(json.dumps({'reader_code_dir':str(self.temp.name),'docker_service':{
            'binary':'docker','project':'test','env_file':'node.env','compose_file':'compose.yaml',
            'override_files':['override.json']}}))
        vault = unittest.mock.Mock()
        module = SimpleNamespace(CredentialVault=vault)
        success = SimpleNamespace(returncode=0, stdout='{"ok":true,"result":{"checkpointed":true}}', stderr='')
        failure = SimpleNamespace(returncode=1, stdout='{"ok":false,"error":"Conflict"}', stderr='')
        for responses, calls, token_calls in (([failure], 1, 0), ([success, success, failure], 3, 1),
                                              ([success, success, success], 3, 1)):
            with patch.dict('sys.modules', {'bot_client':module}), patch('sys.argv', ['bridge','--config',str(config)]), \
                    patch.object(reader_bridge.subprocess, 'run', side_effect=responses) as run, \
                    patch('sys.stderr', io.StringIO()), patch.object(reader_bridge.sys, 'path', list(reader_bridge.sys.path)):
                vault.reset_mock(); vault.return_value.bot_token.return_value = 'temporary-test-token'
                if failure in responses:
                    with self.assertRaises(RuntimeError): reader_bridge.main()
                else: self.assertEqual(reader_bridge.main(), 0)
                self.assertEqual(run.call_count, calls)
                self.assertEqual(vault.return_value.bot_token.call_count, token_calls)
                self.assertEqual(run.call_args_list[0].args[0][-7:], ['exec','-T','core','python','-m','btc_node','request'])
                if token_calls:
                    self.assertEqual(run.call_args_list[1].args[0][-8:], ['--profile','reader','run','--rm','-T','reader','reader','sync'])
                    self.assertEqual(run.call_args_list[2].kwargs['input'], '{"method": "reader.checkpoint"}')

    def test_reader_bridge_retries_only_checkpoint_without_repeating_poll(self):
        config = Path(self.temp.name)/'node.json'
        config.write_text(json.dumps({'reader_code_dir':str(self.temp.name),'docker_service':{
            'binary':'docker','project':'test','env_file':'node.env','compose_file':'compose.yaml'}}))
        vault = unittest.mock.Mock()
        vault.return_value.bot_token.return_value = 'temporary-test-token'
        success = SimpleNamespace(returncode=0, stdout='{"ok":true,"result":{"checkpointed":true}}', stderr='')
        busy = SimpleNamespace(returncode=1, stdout=json.dumps({'ok':False,'error':'Conflict',
            'message':'another node writer is active; retry the same operation'}), stderr='')
        # Rejections before/after the sole poll, or exhaustion before it.
        for responses, polls in (([busy, success, success, busy, success], 1),
                                 ([busy, busy, busy], 0)):
            output = io.StringIO()
            with patch.dict('sys.modules', {'bot_client':SimpleNamespace(CredentialVault=vault)}), \
                    patch('sys.argv', ['bridge','--config',str(config)]), \
                    patch.object(reader_bridge.subprocess, 'run', side_effect=responses) as run, \
                    patch.object(reader_bridge.time, 'sleep'), patch('sys.stderr', output), \
                    patch.object(reader_bridge.sys, 'path', list(reader_bridge.sys.path)):
                vault.reset_mock()
                if polls: self.assertEqual(reader_bridge.main(), 0)
                else:
                    with self.assertRaises(RuntimeError): reader_bridge.main()
                self.assertEqual(vault.return_value.bot_token.call_count, polls)
                calls = run.call_args_list
                self.assertEqual(sum(c.args[0][-2:] == ['reader','sync'] for c in calls), polls)
                for call in calls:
                    if call.args[0][-1] == 'request':
                        self.assertEqual(json.loads(call.kwargs['input']), {'method':'reader.checkpoint'})
            events = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(sum(e['ok'] for e in events), 2 if polls else 0)
            self.assertTrue(all(e['phase'] == 'BEFORE_POLL' for e in events[:2]))
            if polls: self.assertEqual([e['phase'] for e in events[2:]], ['AFTER_POLL']*2)

    def test_container_collector_owns_config_and_preserves_role_arguments(self):
        config = Path(self.temp.name) / 'node.json'
        config.write_text(json.dumps({'environment': {}, 'arguments': ['configured-default']}))
        for arguments, expected in ((['--once'], ['--once']), ([], ['configured-default'])):
            with patch('sys.argv', ['entrypoint.py', 'collector', '--config', str(config), *arguments]), patch.object(entrypoint.os, 'execve') as execute:
                entrypoint.main()
            self.assertEqual(execute.call_args.args[1][1:], ['/app/btc_push.py', *expected])

    def test_cloud_offline_preparation_does_not_require_docker_or_claim_its_validation(self):
        root=Path(self.temp.name)/'cloud'; (root/'roles').mkdir(parents=True)
        script=root/'roles/cloud-setup.sh'
        shutil.copy2(Path(__file__).parent/'roles/cloud-setup.sh',script)
        binary=root/'bin';binary.mkdir();(root/'.venv/bin').mkdir(parents=True)
        python=binary/'python3.11';python.write_text('#!/bin/sh\nexit 0\n');python.chmod(0o755)
        local=root/'.venv/bin/python';local.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CHECK_ARGUMENTS"\n');local.chmod(0o755)
        docker=binary/'docker';docker.write_text('#!/bin/sh\nexit 23\n');docker.chmod(0o755)
        arguments=root/'arguments'
        environment=dict(os.environ,PATH=str(binary)+':/usr/bin:/bin',CHECK_ARGUMENTS=str(arguments))
        result=subprocess.run(['/bin/sh',str(script)],env=environment,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('NOT_RUN',result.stdout)
        self.assertNotIn('--with-data-service',arguments.read_text())
        result=subprocess.run(['/bin/sh',str(script),'--with-data-service'],env=environment,capture_output=True,text=True)
        self.assertEqual(result.returncode,23)
        self.assertNotIn('passed',result.stdout)

    def test_native_analysis_entrypoints_load_shared_helper(self):
        root = Path(__file__).parent
        for name in ('analysis_role.py','build_analysis_reference.py','verify_analysis_reference.py'):
            result = subprocess.run([sys.executable,'-B',str(root/'analysis/roles'/name),'--help'],
                                    capture_output=True,text=True,cwd=self.temp.name)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('usage:',result.stdout)

    def test_collector_cannot_silently_skip_requested_data_service_validation(self):
        root = Path(__file__).parent
        result = subprocess.run([sys.executable,'-B',str(root/'roles/validate_repository.py'),
            '--role','collector','--with-data-service'],capture_output=True,text=True,cwd=self.temp.name)
        self.assertEqual(result.returncode,2)
        self.assertIn('NOT_RUN',result.stderr)
        self.assertNotIn('MARKET_ROLES_REBUILD_RESULT=',result.stdout)


if __name__ == '__main__':
    unittest.main()
