#!/usr/bin/env python3
"""Build an explicit source allowlist; runtime data is never traversed."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import role_support


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--skill', required=True)
    parser.add_argument('--manifest', default=str(Path(__file__).with_name('analysis-source-files.json')))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    roots = {'project': Path(args.project).resolve(), 'skill': Path(args.skill).resolve()}
    manifest = role_support.read_json(args.manifest)
    entries = manifest['files']
    destinations = [row['destination'] for row in entries]
    if len(destinations) != len(set(destinations)):
        raise ValueError('duplicate source destination')
    with tempfile.TemporaryDirectory(prefix='analysis-source-stage-') as directory:
        stage = Path(directory)
        for row in entries:
            root = roots[row['source_root']]
            source = root / role_support.relative_path(row['path'])
            if source.is_symlink() or root not in source.resolve().parents:
                raise ValueError('source must be a regular file within its configured root')
            destination = stage / role_support.relative_path(row['destination'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        result = role_support.package(stage, destinations, args.output, 'analysis')
    raw = Path(args.output).read_bytes()
    result.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
