#!/usr/bin/env python3
"""Check selected source exports and Python syntax without running business code."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

from export_role import export
from role_support import validate_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--role', choices=('collector', 'analysis', 'all'), default='all')
    parser.add_argument('--with-data-service', action='store_true',
                        help='legacy request; data-service behavior is not checked by this source validator')
    args = parser.parse_args()
    if args.with_data_service:
        parser.error('data-service behavior validation NOT_RUN; use the current task\'s separate temporary verification')
    if sys.version_info < (3, 9):
        parser.error('Python 3.9 or later is required')
    selected = ('collector', 'analysis') if args.role == 'all' else (args.role,)
    results = []
    with tempfile.TemporaryDirectory(prefix='market-role-rebuild-') as directory:
        for role in selected:
            target = Path(directory) / role
            exported = export(role, target)
            results.append(dict(validate_source(target), role=role, files=exported['files']))
    print('MARKET_ROLES_REBUILD_RESULT=' + json.dumps(results, sort_keys=True))
    return 0 if all(result['exit_code'] == 0 for result in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
