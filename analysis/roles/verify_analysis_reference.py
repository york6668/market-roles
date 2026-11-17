#!/usr/bin/env python3
"""Check an analysis source reference's format, paths and Python syntax."""
import argparse
import json
from pathlib import Path
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
        checked = role_support.validate_source(root, args.python)
        result = {'format': data['format'], 'role': data['role'], 'version': data['version'],
                  'files': unpacked['files'], 'source_check': checked}
        print('ANALYSIS_REFERENCE_VERIFIED=' + json.dumps(result, sort_keys=True))
        return checked['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
