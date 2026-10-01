import json
from pathlib import Path
import tempfile
import unittest

from roles.export_role import export


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

    def test_reader_export_needs_no_core_checkout_or_test_data(self):
        self.manifest({'telegram_reader/shared.py': 'shared.py',
                       'roles/deployment.py': 'shared.py'})
        (self.root / '.gitmodules').write_text('[submodule "core"]\n')
        result = export('reader', self.destination, self.root)
        self.assertEqual(1, result['files'])
        self.assertEqual(['shared.py'], [p.name for p in self.destination.iterdir()])

    def test_collector_uses_its_own_manifest_and_rejects_missing_dependency(self):
        with self.assertRaisesRegex(FileNotFoundError, 'collector'):
            export('collector', self.destination, self.root)
        collector = self.root / 'core/market-collector'
        (collector / 'roles').mkdir(parents=True)
        (collector / 'source.py').write_text('SOURCE = 1\n')
        (collector / 'private.json').write_text('local data')
        (collector / 'roles/collector-source-files.json').write_text(json.dumps(['source.py']))
        result = export('collector', self.destination, self.root)
        self.assertEqual(1, result['files'])
        self.assertFalse((self.destination / 'private.json').exists())


if __name__ == '__main__':
    unittest.main()
