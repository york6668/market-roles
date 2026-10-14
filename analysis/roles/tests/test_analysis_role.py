"""Rebuild/recover synthetic analysis state through the actual native entrypoint."""
import contextlib
from copy import deepcopy
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skill/btc-core-strategy'
if not SKILL.is_dir():
    raise FileNotFoundError('bundled analysis skill is required')
sys.path[:0] = [str(ROOT / 'roles'), str(SKILL / 'scripts'), str(ROOT / 'telegram_reader'),
               str(ROOT / 'telegram_reader/tests')]
import analysis_role
import role_support
import btc_evidence
from btc_evidence_reader import EvidenceReader
from models import ReaderConfig
from store import MessageStore
from sync_engine import synchronize
from test_evidence_v2 import generated
from v4 import common, run_flow, collector, research, storage, sensing, market_state
import market_observation


def seed(project):
    fixture = role_support.read_json(Path(os.environ['BTC_ANALYSIS_TEST_FIXTURE']))
    project.mkdir()
    for name in ('资产配置.md', '操作记录.md', '纠正记录.md'):
        (project / name).write_text(fixture['facts'][name])
    (project / '价值因子.md').write_text('Synthetic method guidance. No real assets.\n')
    root = project / '.strategy/v4'
    for identity, value in fixture['versions'].items():
        directory = root / 'versions' / identity
        common.create(directory / 'decision.json', value['decision'])
        for name, body in value['views'].items():
            common.create(directory / name, body.encode())
    for identity, value in fixture['evidence'].items():
        directory = root / 'evidence' / identity
        common.create(directory / 'evidence.json', value['bundle'])
        for name, raw in value['raw'].items():
            common.create(directory / 'raw' / name, raw)
    for name, value in fixture['outbox'].items():
        common.create(root / name, value)
    for name, value in fixture['delivery_baselines'].items():
        common.create(root / name, value)
    for name, value in fixture['research'].items():
        common.create(root / name, value)
    (root / 'current').symlink_to('versions/' + fixture['decision']['decision_id'])
    common.create(root / 'write-policy.json', {'minimum_assessment_revision': 5})
    common.create(project / 'frozen-market.json', fixture['market'])
    return fixture


class AnalysisRoleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='analysis-role-synthetic-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / 'project'
        self.fixture = seed(self.project)
        self.reader_data = self.base / 'reader-data'
        self.reader_data.mkdir()
        self.reader_evidence = self.base / 'evidence.md'
        self.reader_evidence.write_text('Synthetic auxiliary snapshot.\n')
        self.memory = self.base / 'memory.md'; self.memory.write_text('Synthetic pending context.\n')
        self.value = {'role': 'analysis', 'machine': 'synthetic.local', 'python': sys.executable,
            'code_dir': str(ROOT), 'entrypoint': 'telegram_reader/reader.py',
            'arguments': ['sync'], 'service_label': 'local.btc.telegram-reader', 'reader_minute': 10,
            'log_dir': str(self.base / 'logs'), 'project_dir': str(self.project), 'skill_dir': str(SKILL),
            'reader_data_dir': str(self.reader_data), 'reader_evidence_path': str(self.reader_evidence),
            'environment': {}, 'state_paths': {
                'strategy': str(self.project / '.strategy'), 'reader_data': str(self.reader_data),
                'reader_evidence': str(self.reader_evidence), 'automation_memory': str(self.memory),
                **{str(i): str(self.project / name) for i, name in enumerate(('资产配置.md','操作记录.md','纠正记录.md'))}},
            'writer_locks': []}
        self.config = self.base / 'machine.json'; role_support.write_json(self.config, self.value)
        self.environ = mock.patch.dict(os.environ, {}, clear=False); self.environ.start(); self.addCleanup(self.environ.stop)
        analysis_role.configure_paths(self.value)
        (self.project / 'telegram_reader').symlink_to(ROOT / 'telegram_reader')
        def denied(*_args, **_kwargs):
            raise AssertionError('real network or credentials forbidden in isolation')
        for name in ('connect', 'connect_ex'):
            p = mock.patch.object(socket.socket, name, denied); p.start(); self.addCleanup(p.stop)
        p = mock.patch('bot_client.CredentialVault.bot_token', side_effect=denied); p.start(); self.addCleanup(p.stop)
        p = mock.patch('market_observation.time.time', return_value=1898604000); p.start(); self.addCleanup(p.stop)
        for name in ('common','run_flow','collector','research','sensing','storage','evidence','reporting','report_care','market_state'):
            module = importlib.import_module('v4.' + name)
            if hasattr(module, 'now'):
                p = mock.patch.object(module, 'now', return_value='2030-03-01T14:00:00+00:00')
                p.start(); self.addCleanup(p.stop)
        self.seed_reader()

    def seed_reader(self, holdings_only=False, start_id=100):
        updates, documents = [], {}
        for index, asset in enumerate(('BTC','QQQ','VOO')):
            parent = start_id + index * 2
            bundle, text = generated(asset, etf_holdings=holdings_only)
            raw = btc_evidence.encode_bundle(bundle); documents[str(parent)] = raw
            chat = {'id': -100123, 'type': 'channel'}
            updates.extend([
                {'update_id': parent, 'channel_post': {'chat': chat, 'message_id': parent, 'date': 100, 'text': text}},
                {'update_id': parent + 1, 'channel_post': {'chat': chat, 'message_id': parent + 1, 'date': 100,
                    'reply_to_message': {'message_id': parent},
                    'document': {'file_id': str(parent), 'file_name': asset + '.json', 'file_size': len(raw)}}}])
        class Source:
            def get_updates(self, *, offset=None): return updates
            def download_document(self, file): return documents[file]
        config = ReaderConfig(chat_id=-100123, reader_bot_id=42, configured_at_utc='2030-03-01T13:00:00Z')
        with MessageStore(self.reader_data / 'messages.sqlite3') as store:
            store.save_config(config)
            synchronize(store=store, source=Source(), config=config)

    def test_bitbo_holdings_reach_btc_analysis_without_current_flows(self):
        self.seed_reader(holdings_only=True, start_id=1100)
        captured = collector.capture(self.project)
        collector.validate(captured)
        btc = captured['assets']['BTC']
        self.assertEqual('AUXILIARY', btc['status'])
        self.assertAlmostEqual(12.00000012, btc['datasets']['etf']['values']['holdings_btc'])
        self.assertIsNone(btc['datasets']['etf']['values']['flow_1d_usd'])
        self.assertEqual('Bitbo', btc['sources']['public_etf']['venue'])
        self.assertNotIn('public_etf_history', btc['sources'])

    def native(self, *args):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            status = analysis_role.main(['--config', str(self.config), 'strategy', '--', *map(str, args)])
        self.assertEqual(status, 0, buffer.getvalue())
        return json.loads(buffer.getvalue())

    def prep(self, original_revision=None):
        if original_revision is not None:
            analysis_role.configure_paths(self.value)
            run_flow.prepare(self.project/'.strategy/v4',self.project,'SYNTHETIC_ROLE_RUN',
                self.project/'.strategy/v4/role-run',self.project/'frozen-market.json',
                agent_id='SYNTHETIC_MAIN',workflow_revision=original_revision)
        return self.native('run-prepare', '--run-ref', 'SYNTHETIC_ROLE_RUN', '--agent', 'SYNTHETIC_MAIN',
                           '--directory', self.project / '.strategy/v4/role-run', '--market', self.project / 'frozen-market.json')

    def observe(self, prepared):
        value = common.read(prepared['market_template'])
        value['market_review'] = {'assessment_summary': 'Synthetic unchanged raw evidence remains independently limited.',
            'changes_since_hour': [], 'changes_since_deep': [],
            'deep_review': {'required': False, 'reasons': []}, 'patterns': []}
        value.update(market_assessment=self.fixture['decision']['assessment']['outlook']['market_assessment'],
            dispute_zones=self.fixture['decision']['assessment']['outlook']['dispute_zones'],
            factor_checks={'items': [], 'summary': 'Synthetic factor interpretation remains limited.'})
        from test_closed_loop import forward
        for item in value['market_assessment']['markets']:
            for horizon in item['horizons']:
                horizon['forward'] = forward(item['as_of'])
        if common.read(prepared['context'])['revision']>=8:
            from test_investment import public_research
            public_research({'market_assessment':value['market_assessment']})
        directory = Path(prepared['run']).parent
        market_file = directory / 'market-authored.json'; common.create(market_file, value)
        candidate = self.native('run-advance', '--run', prepared['run'], '--stage', 'market',
                                '--template', prepared['market_template'], '--answers', market_file, '--check-only')
        # Generated authorship tests the real candidate binding, not model semantics.
        self.assertEqual(common.read(candidate['market_candidate'])['payload'], value)
        public = self.native('run-advance', '--run', prepared['run'], '--stage', 'market',
                             '--input', candidate['market_candidate'])
        personal = {'recommendation_checks': [{
            'side': side, 'findings': ['NO_MATERIAL_CHANGE'], 'refs': ['windows.4h.binance_spot_1h'],
            'explanation': 'Synthetic checks leave the recorded response unchanged.'}
            for side in ('upper_short','lower_spot')], 'main_evaluation': {'required': False, 'reasons': []}}
        portfolio = common.read(public['portfolio_context'])
        personal['allocation_review'] = {'market_result_hash': public['market_result_hash'],
            'portfolio_risk_hash': None, 'strategy_advice_hash': None, 'fact_version': portfolio['fact_version'],
            'outcome': 'EVIDENCE_LIMITED', 'material': False,
            'explanation': 'Legacy report prose is not a newly assessed asset risk result.',
            'limitations': ['A real revision seven asset risk assessment is pending.']}
        if common.read(prepared['context'])['revision']>=8:
            personal['allocation_review'].update(investment_decision_hash=None,issue_reviews=deepcopy(portfolio['open_investment_issues']))
            personal['main_evaluation']={'required':True,'reasons':['Synthetic original upstream must complete the missing portfolio judgement.']}
        personal_file = directory / 'portfolio-authored.json'; common.create(personal_file, personal)
        output = self.native('run-advance', '--run', prepared['run'], '--stage', 'observe',
                             '--template', public['observation_template'], '--answers', personal_file)
        replay = ('run-advance', '--run', prepared['run'], '--stage', 'observe',
                  '--template', public['observation_template'], '--answers', personal_file)
        return output, replay

    def test_revision8_prepare_preserves_revision5_owners_and_report_identity(self):
        original = common.facts(self.project)
        prepared = self.prep()
        ctx = common.read(prepared['context'])
        self.assertEqual(ctx['revision'], 8)
        self.assertEqual(ctx['collector_observations']['assets']['BTC']['transport']['text_message_id'], 100)
        self.assertFalse(ctx['collector_observations']['assets']['VOO']['datasets']['stock_1h']['analysis_eligible'])
        self.assertNotIn('confirmed_account_facts', ctx)
        self.assertEqual(prepared, self.prep())
        self.assertEqual(original, common.facts(self.project))
        self.assertEqual(self.native('--full', 'pin')['assessment']['revision'], 5)

    def test_restore_preserves_native_run_cursor_baselines_pending_unknown_and_delivered(self):
        prepared = self.prep(original_revision=7)
        self.assertEqual(common.read(prepared['context'])['revision'],7)
        observed, replay = self.observe(prepared)
        report = common.read(observed['report_context'])
        self.assertIsNone(report['portfolio_risk'])
        self.assertNotIn('allocation_decision', report)
        self.assertEqual(report['applicability']['portfolio']['outcome'], 'EVIDENCE_LIMITED')
        run = common.read(prepared['run'])
        evidence = common.read(Path(run['evidence']) / 'evidence.json')
        source = next(s for s in evidence['sources'] if s['trust'] == 'PUBLIC_RAW')
        payload = common.read(Path(run['evidence']) / 'raw' / (source['raw_hash'][7:] + '.json'))
        field = next(iter(payload))
        request = research.request(self.project / '.strategy/v4', self.project, {
            'issue_key': 'SYNTHETIC_ROLE_PENDING', 'scope': ['/outlook'],
            'question': 'Synthetic independent pending research question.',
            'decision_id': storage.current(self.project / '.strategy/v4')['decision_id'],
            'evidence_id': evidence['evidence_id'], 'change': {'kind': 'INITIAL_QUESTION',
                'reason': 'Synthetic still unresolved issue.',
                'refs': [{'source_id': source['id'], 'pointer': '/' + field.replace('~','~0').replace('/','~1'),
                          'value_hash': common.digest(payload[field])}],
                'reopen_condition': None}, 'reopen_conditions': ['Synthetic new public evidence.']})
        baseline = self.native('recover')
        state_before = {q: q.read_bytes() for q in (self.project / '.strategy/v4/outbox').rglob('*.json')}
        backup = self.base / 'backup'; role_support.snapshot(self.value, backup)
        retired = self.base / 'retired'; retired.mkdir()
        for key, name in self.value['state_paths'].items():
            path = Path(name); path.rename(retired / key)
        role_support.restore(backup, self.value)
        after = self.native('recover')
        self.assertEqual(baseline, after)
        recovered = self.native(*replay)
        self.assertTrue(recovered['replayed'])
        self.assertEqual(recovered['observation_id'], observed['observation_id'])
        self.assertEqual(state_before, {q: q.read_bytes() for q in (self.project / '.strategy/v4/outbox').rglob('*.json')})
        root = self.project / '.strategy/v4'
        self.assertTrue((root / request['independent_input_path']).is_file())
        states = {x['state'] for x in after['outbox']}
        self.assertEqual(states, {'UNKNOWN','DELIVERED','PENDING'})
        self.assertEqual(len(after['attempt_recovery']), 1)
        with MessageStore(self.reader_data / 'messages.sqlite3') as store:
            self.assertEqual(store.get_last_update_id(), 105)
        self.assertTrue((root / 'current').is_symlink())
        self.assertEqual(storage.current(root)['assessment']['revision'], 5)

    def test_reader_candidate_keeps_minute10_without_model_scheduler(self):
        destination = self.base / 'reader.plist'
        analysis_role.render_reader(self.config, destination)
        import plistlib
        value = plistlib.loads(destination.read_bytes())
        self.assertEqual(value['StartCalendarInterval'], {'Minute': 10})
        self.assertNotIn('RunAtLoad', value); self.assertNotIn('KeepAlive', value)
        self.assertNotIn('strategy_v4.py', json.dumps(value))

    def test_state_wal_and_absolute_internal_links_restore_to_new_root(self):
        root = self.base / 'small'; root.mkdir()
        target = root / 'versions/a'; target.mkdir(parents=True); (target / 'context.json').write_text('synthetic')
        (root / 'current').symlink_to(target)
        conn = sqlite3.connect(root / 'reader.sqlite3'); self.addCleanup(conn.close)
        conn.execute('PRAGMA journal_mode=WAL'); conn.execute('CREATE TABLE cursor(value)')
        conn.execute('INSERT INTO cursor VALUES(987)'); conn.commit()
        value = {'role':'analysis','state_paths':{'context':str(root)},'writer_locks':[]}
        before = (root / 'reader.sqlite3-wal').read_bytes()
        backup = self.base / 'small-backup'; role_support.snapshot(value, backup)
        self.assertEqual(before, (root / 'reader.sqlite3-wal').read_bytes())
        restored = self.base / 'small-restored'
        role_support.restore(backup, dict(value, state_paths={'context':str(restored)}))
        self.assertEqual((restored / 'current').resolve(), (restored / 'versions/a').resolve())
        with sqlite3.connect(restored / 'reader.sqlite3') as db:
            self.assertEqual(db.execute('SELECT value FROM cursor').fetchone()[0], 987)

    def test_revision8_native_public_and_personal_stage_preserves_original_owner(self):
        prepared=self.prep()
        observed,_=self.observe(prepared)
        context=common.read(observed['report_context'])
        self.assertTrue(observed['main_eligible'])
        self.assertIsNone(context['investment_decision'])
        self.assertEqual(context['applicability']['portfolio']['outcome'],'REVISE')
        self.assertEqual(self.native('--full','pin')['assessment']['revision'],5)
        self.assertNotIn('recorded_policy_inputs',common.read(prepared['context']))
        self.assertNotIn('investment_feedback',common.read(prepared['context']))


if __name__ == '__main__':
    unittest.main()
