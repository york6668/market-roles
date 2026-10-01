#!/usr/bin/env python3
"""Run native analysis/recovery tests with temporary synthetic state only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from urllib.parse import unquote, urlsplit


def main():
    root = Path(__file__).resolve().parents[1]
    skill = root / 'skill/btc-core-strategy'
    if not skill.is_dir():
        raise FileNotFoundError('analysis source is incomplete: bundled skill is required')
    reader = root / 'telegram_reader'
    os.environ['BTC_COLLECTOR_CONTRACT_PATH'] = str(reader / 'btc_evidence.py')
    os.environ.update(BOT_TOKEN='', CHAT_ID='')
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root / 'roles'), str(root / 'roles/tests'), str(skill / 'scripts'),
                   str(skill / 'tests'), str(reader), str(reader / 'tests')]
    counts = {name: 0 for name in ('network_attempts', 'credential_attempts', 'process_attempts',
        'non_temporary_db_attempts', 'non_temporary_write_attempts', 'real_fact_read_attempts')}
    with tempfile.TemporaryDirectory(prefix='btc-analysis-offline-') as directory:
        sandbox = Path(directory).resolve()
        tempfile.tempdir = str(sandbox)
        for name in ('资产配置.md', '操作记录.md', '纠正记录.md'):
            (sandbox / name).write_text('SYNTHETIC TEST FACTS ONLY\n', encoding='utf-8')
        config = sandbox / 'node.json'
        config.write_text(json.dumps({'schema': 'BTC_NODE_CONFIG_V1',
            'project_dir': str(sandbox), 'legacy_revision2_dir': str(sandbox / 'legacy'),
            'python': sys.executable, 'frozen_market_python': sys.executable}))
        os.environ['BTC_NODE_CONFIG'] = str(config)
        subprocess.run([sys.executable, '-B', str(root / 'scripts/build_synthetic_fixtures.py'),
                        '--output-dir', str(sandbox / 'legacy')], check=True)
        def temporary(path):
            return isinstance(path, int) or Path(os.fsdecode(path)).resolve().is_relative_to(sandbox)
        def audit(event, args):
            if event.startswith('socket.'):
                counts['network_attempts'] += 1
                raise AssertionError('analysis_offline_network_denied')
            if event in ('subprocess.Popen','os.system','os.posix_spawn','os.spawn'):
                counts['process_attempts'] += 1
                raise AssertionError('analysis_offline_process_denied')
            if event == 'sqlite3.connect':
                path = os.fsdecode(args[0])
                if path == ':memory:': return
                if path.startswith('file:'): path = unquote(urlsplit(path).path)
                if not temporary(path):
                    counts['non_temporary_db_attempts'] += 1
                    raise AssertionError('analysis_offline_database_denied')
            if event == 'open':
                path, mode, flags = args
                writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
                if not temporary(path):
                    if writing:
                        counts['non_temporary_write_attempts'] += 1
                        raise AssertionError('analysis_offline_write_denied')
                    if not isinstance(path, int) and Path(os.fsdecode(path)).name in ('资产配置.md','操作记录.md','纠正记录.md'):
                        counts['real_fact_read_attempts'] += 1
                        raise AssertionError('analysis_offline_real_facts_denied')
        def no_credentials(*args, **kwargs):
            counts['credential_attempts'] += 1
            raise AssertionError('analysis_offline_credentials_denied')
        sys.addaudithook(audit)
        sys.modules['keyring'] = types.SimpleNamespace(get_password=no_credentials)
        suite = unittest.defaultTestLoader.loadTestsFromNames(['test_analysis_role','test_collector_provenance'])
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        summary = {'tests_run': result.testsRun, 'failures': len(result.failures),
            'errors': len(result.errors), 'skipped': len(result.skipped), 'guards': counts}
        print('BTC_ANALYSIS_OFFLINE_RESULT=' + json.dumps(summary, sort_keys=True))
        return 0 if result.wasSuccessful() and not result.skipped and not any(counts.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
