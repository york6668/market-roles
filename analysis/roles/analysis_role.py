#!/usr/bin/env python3
"""Local analysis-role paths and native entrypoints; never schedules a model."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

import role_support


def machine_config(path):
    value = role_support.config(path)
    if value['role'] != 'analysis':
        raise ValueError('analysis machine configuration required')
    for key in ('project_dir', 'skill_dir', 'reader_data_dir', 'reader_evidence_path'):
        role_support.local_path(value[key])
    if not 0 <= value.get('reader_minute', 10) <= 59:
        raise ValueError('reader_minute must be within the hour')
    return value


def configure_paths(value):
    project = role_support.local_path(value['project_dir'])
    skill = role_support.local_path(value['skill_dir'])
    reader = role_support.local_path(value['code_dir']) / role_support.relative_path(value['entrypoint'])
    os.environ['BTC_COLLECTOR_CONTRACT_PATH'] = str(reader.parent / 'btc_evidence.py')
    os.environ['BTC_READER_DATA_DIR'] = value['reader_data_dir']
    os.environ['BTC_READER_EVIDENCE_PATH'] = value['reader_evidence_path']
    if value.get('frozen_market_python'):
        os.environ['BTC_FROZEN_MARKET_PYTHON'] = str(role_support.local_path(value['frozen_market_python']))
    sys.path[:0] = [str(skill / 'scripts'), str(reader.parent)]
    return project, skill, reader


def check(value):
    project, skill, reader = configure_paths(value)
    result = role_support.check(value)
    result['checks'].update({
        'strategy_entrypoint': (skill / 'scripts/strategy_v4.py').is_file(),
        'revision5_method': (skill / 'references/market-state.md').is_file(),
        'reader_contract': (reader.parent / 'btc_evidence.py').is_file(),
        'fact_files_present': all((project / n).is_file() for n in ('资产配置.md', '操作记录.md', '纠正记录.md')),
    })
    result['ready'] = all(result['checks'].values())
    result['analysis_scheduler'] = 'Codex local automation; managed separately'
    result['credentials'] = 'local Keychain btc.telegram.reader / bot_token; never exported'
    return result


def render_reader(config_path, destination):
    value = machine_config(config_path)
    # The common helper owns candidate rendering. The analysis adapter only
    # preserves this existing reader's calendar schedule and local path binding.
    result = role_support.render_service(config_path, destination)
    path = Path(destination)
    candidate = plistlib.loads(path.read_bytes())
    for key in ('RunAtLoad', 'KeepAlive', 'StartInterval'):
        candidate.pop(key, None)
    candidate['StartCalendarInterval'] = {'Minute': value.get('reader_minute', 10)}
    candidate['EnvironmentVariables'] = dict(value.get('environment', {}),
        BTC_READER_DATA_DIR=value['reader_data_dir'], BTC_READER_EVIDENCE_PATH=value['reader_evidence_path'])
    candidate['StandardOutPath'] = value.get('reader_stdout', candidate['StandardOutPath'])
    candidate['StandardErrorPath'] = value.get('reader_stderr', candidate['StandardErrorPath'])
    path.write_bytes(plistlib.dumps(candidate))
    return result


def link_project(value):
    project, skill, reader = configure_paths(value)
    reader_link = project / 'telegram_reader'
    reader_code = reader.parent
    links = {
        reader_link: reader_code,
        project / '策略证据.md': Path(value['reader_evidence_path']),
        project / '策略状态.md': project / '.strategy/v4/current/state.md',
        project / '当前预期计划.md': project / '.strategy/v4/current/plan.md',
    }
    for link, target in links.items():
        if link == target:
            continue
        if link.is_symlink() and link.resolve() == target.resolve():
            continue
        if link.exists() or link.is_symlink():
            raise ValueError('existing project content must be reviewed before linking: ' + str(link))
    for link, target in links.items():
        if link == target or link.is_symlink():
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
    return {'links': len(links), 'services_started': False}


def recovery_inputs(value):
    """List external local file references only; never return JSON payload bodies."""
    project = role_support.local_path(value['project_dir'])
    root = project / '.strategy/v4'
    state_roots = [role_support.local_path(x).resolve() for x in value.get('state_paths', {}).values()]
    code_roots = [role_support.local_path(value[k]).resolve() for k in ('code_dir','skill_dir')]
    found = set()
    def visit(item):
        if isinstance(item, dict):
            for child in item.values(): visit(child)
        elif isinstance(item, list):
            for child in item: visit(child)
        elif isinstance(item, str) and item.startswith('/') and len(item) < 4096 and '\n' not in item:
            path = Path(item.split('#', 1)[0])
            if path.suffix not in ('.jsonl','.json','.md','.txt'):
                return
            resolved = path.resolve()
            if any(resolved == base or base in resolved.parents for base in state_roots + code_roots):
                return
            found.add(str(path))
    for name in ('research','outbox','main','deep','runtime','runs'):
        for path in (root / name).rglob('*.json'):
            if path.is_file() and path.stat().st_size <= 16 * 1024 * 1024:
                visit(role_support.read_json(path))
    references = [{'path': path, 'present': Path(path).is_file()} for path in sorted(found)]
    return {'external_file_references': references, 'missing': sum(not row['present'] for row in references),
            'contents_exported': False, 'state_config_modified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    sub.add_parser('link-project')
    sub.add_parser('recovery-inputs')
    p = sub.add_parser('render-reader'); p.add_argument('destination')
    for name in ('strategy', 'reader'):
        p = sub.add_parser(name); p.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    value = machine_config(args.config)
    if args.command == 'check':
        result = check(value)
    elif args.command == 'render-reader':
        result = render_reader(args.config, args.destination)
    elif args.command == 'link-project':
        result = link_project(value)
    elif args.command == 'recovery-inputs':
        result = recovery_inputs(value)
    else:
        project, skill, reader_path = configure_paths(value)
        tail = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
        if args.command == 'strategy':
            import strategy_v4
            return strategy_v4.main(['--project', str(project), '--root', str(project / '.strategy/v4'), *tail])
        import reader
        return reader.main(tail)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if args.command == 'check' and not result['ready'] else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}), file=sys.stderr)
        sys.exit(1)
