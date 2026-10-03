"""Build role images from the existing source allowlists; never copy node data."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'roles'))
from export_role import export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role', choices=('collector', 'reader'))
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--tag', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='btc-role-image-') as directory:
        tree = Path(directory) / 'source'
        export('analysis' if args.role == 'reader' else 'collector', tree)
        def git(*arguments):
            return subprocess.check_output(['git', '-C', str(ROOT), *arguments], text=True).strip()
        revision = git('rev-parse', 'HEAD')
        (tree / 'ROLE_RELEASE.json').write_text(json.dumps({'role':args.role,
            'roles_commit':revision, 'core_commit':git('rev-parse', 'HEAD:core/btc-core-strategy'),
            'working_tree_modified':bool(git('status', '--porcelain'))}, sort_keys=True)+'\n')
        # Core's service-only build filter is not the reader/collector filter.
        # This entire temporary tree already comes from the role allowlist.
        (tree / '.dockerignore').unlink(missing_ok=True)
        (tree / 'roles/containers').mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'roles/containers/entrypoint.py', tree / 'roles/containers/entrypoint.py')
        if not (tree / 'requirements.txt').is_file():
            shutil.copy2(ROOT / 'requirements.txt', tree / 'requirements.txt')
        subprocess.run([args.docker, 'build', '--tag', args.tag,
                        '--label', 'org.opencontainers.image.revision='+revision, '-f',
                        str(ROOT / 'roles/containers/Dockerfile'), str(tree)], check=True)


if __name__ == '__main__':
    main()
