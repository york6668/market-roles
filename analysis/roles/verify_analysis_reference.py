#!/usr/bin/env python3
"""Unpack an analysis source reference and run its isolated native tests."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import role_support


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference')
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    data = role_support.read_json(args.reference)
    if data.get('role') != 'analysis' or data.get('version') != role_support.VERSION:
        raise ValueError('analysis reference version mismatch')
    with tempfile.TemporaryDirectory(prefix='btc-analysis-reference-') as directory:
        root = Path(directory) / 'reference'
        unpacked = role_support.unpack(args.reference, root)
        results = []
        for name in ('telegram_reader/run_offline_tests.py', 'roles/run_isolated_tests.py'):
            process = subprocess.run([args.python, '-B', str(root / name)], cwd=root,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(process.stdout, end='')
            print(process.stderr, end='', file=sys.stderr)
            results.append({'entrypoint': name, 'exit_code': process.returncode})
        result = {'format': data['format'], 'role': data['role'], 'version': data['version'],
                  'files': unpacked['files'], 'tests': results}
        print('ANALYSIS_REFERENCE_VERIFIED=' + json.dumps(result, sort_keys=True))
        return 0 if all(row['exit_code'] == 0 for row in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
