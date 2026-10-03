#!/usr/bin/env python3
"""Rebuild selected roles from this checkout and run their offline suites."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

from export_role import export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=('collector', 'analysis', 'all'), default='all')
    parser.add_argument('--with-data-service', action='store_true', help='also require real MySQL/Docker/CLI/MCP recovery tests')
    parser.add_argument('--docker', default='docker')
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        parser.error('Python 3.9 or later is required')
    selected = ('collector', 'analysis') if args.role == 'all' else (args.role,)
    environment = dict(os.environ, BOT_TOKEN='', CHAT_ID='', PYTHONDONTWRITEBYTECODE='1')
    environment.pop('PYTHONPATH', None)
    results = []
    repository = Path(__file__).resolve().parents[1]
    tools_check = subprocess.run([sys.executable, '-B', str(repository / 'roles/offline_tests.py'),
                                  'test_role_export'], cwd=repository, env=environment)
    results.append({'role': 'framework', 'entrypoint': 'test_role_export',
                    'exit_code': tools_check.returncode})
    with tempfile.TemporaryDirectory(prefix='market-role-rebuild-') as directory:
        for role in selected:
            target = Path(directory) / role
            exported = export(role, target)
            entries = ('roles/offline_tests.py',) if role == 'collector' else (
                'telegram_reader/run_offline_tests.py', 'roles/run_isolated_tests.py', 'scripts/run_tests.py')
            for entry in entries:
                command = [sys.executable, '-B', str(target / entry)]
                if entry == 'scripts/run_tests.py':
                    command.extend(['--reader', str(target / 'telegram_reader')])
                result = subprocess.run(command,
                                        cwd=target, env=environment)
                results.append({'role': role, 'entrypoint': entry,
                                'files': exported['files'], 'exit_code': result.returncode})
            if role == 'analysis' and args.with_data_service:
                image = 'btc-reader-contract:' + uuid.uuid4().hex[:12]
                try:
                    subprocess.run([sys.executable, '-B', str(repository/'roles/containers/build.py'),
                                    'reader', '--docker', args.docker, '--tag', image], check=True, env=environment)
                    result = subprocess.run([sys.executable, '-B', str(target / 'service/check.py'),
                        '--docker', args.docker, '--reader-image', image], cwd=target, env=environment)
                finally:
                    subprocess.run([args.docker, 'image', 'rm', image], env=environment, check=False)
                results.append({'role': role, 'entrypoint': 'service/check.py', 'exit_code': result.returncode})
    print('MARKET_ROLES_REBUILD_RESULT=' + json.dumps(results, sort_keys=True))
    return 0 if all(result['exit_code'] == 0 for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
