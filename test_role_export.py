import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from roles.export_role import export
from roles.containers import entrypoint


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

    def test_container_collector_owns_config_and_preserves_role_arguments(self):
        config = Path(self.temp.name) / 'node.json'
        config.write_text(json.dumps({'environment': {}, 'arguments': ['configured-default']}))
        for arguments, expected in ((['--once'], ['--once']), ([], ['configured-default'])):
            with patch('sys.argv', ['entrypoint.py', 'collector', '--config', str(config), *arguments]), patch.object(entrypoint.os, 'execve') as execute:
                entrypoint.main()
            self.assertEqual(execute.call_args.args[1][1:], ['/app/btc_push.py', *expected])


if __name__ == '__main__':
    unittest.main()
