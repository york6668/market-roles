#!/usr/bin/env python3
"""Build an explicit source allowlist; runtime data is never traversed."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import role_support
import sys

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / 'roles'))
from export_role import export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', help='legacy argument; data is never collected')
    parser.add_argument('--skill', help='legacy argument; core comes from the pinned submodule')
    parser.add_argument('--repository', default=str(REPOSITORY))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='analysis-source-stage-') as directory:
        stage = Path(directory) / 'analysis'
        export('analysis', stage, root=Path(args.repository))
        destinations = sorted(str(path.relative_to(stage)) for path in stage.rglob('*') if path.is_file())
        result = role_support.package(stage, destinations, args.output, 'analysis')
    raw = Path(args.output).read_bytes()
    result.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
