#!/usr/bin/env python3
"""Export one role's explicit source set into a new local directory.

This materializes shared repository sources at the role's existing relative
paths. It never copies runtime state, installs services, or contacts a node.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

try:
    from .role_support import relative_path
except ImportError:
    from role_support import relative_path


ROOT = Path(__file__).resolve().parents[1]


def export(role, destination, root=ROOT):
    root = Path(root).resolve()
    entries = json.loads((root / 'roles/source-map.json').read_text())[role]
    entries = dict(entries)
    dependency = root / 'core/btc-core-strategy'
    if role == 'analysis' and (root / '.gitmodules').is_file():
        manifest = dependency / 'export-manifest.json'
        if not manifest.is_file():
            raise FileNotFoundError('initialize pinned core: git submodule update --init core/btc-core-strategy')
        for name in json.loads(manifest.read_text())['files']:
            name = str(relative_path(name))
            if name in entries:
                raise ValueError('core and reader export destinations overlap: ' + name)
            entries[name] = 'core/btc-core-strategy/' + name
    if not entries:
        raise ValueError('role source set is empty')
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    sources = []
    for target, source in entries.items():
        target = relative_path(target)
        source = root / relative_path(source)
        if source.is_symlink() or root not in source.resolve().parents or not source.is_file():
            raise ValueError('source must be a regular repository file')
        sources.append((target, source))
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.role-source-', dir=destination.parent))
    try:
        for target, source in sources:
            output = stage / target
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)
        # Fail if the destination was created while staging; never merge it.
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        os.rename(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {'role': role, 'destination': str(destination), 'files': len(sources)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role', choices=('collector', 'analysis'))
    parser.add_argument('destination')
    args = parser.parse_args()
    print(json.dumps(export(args.role, args.destination), ensure_ascii=False))


if __name__ == '__main__':
    main()
