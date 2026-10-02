"""Keep reader credentials in the existing native Keychain and sync in Docker."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    sys.path.insert(0, config['reader_code_dir'])
    from bot_client import CredentialVault
    docker = config['docker_service']
    command = [docker['binary'], 'compose', '-p', docker['project'], '--env-file', docker['env_file'],
               '-f', docker['compose_file']]
    for override in docker.get('override_files', []):
        command += ['-f', override]
    def checkpoint():
        saved = subprocess.run(command + ['exec','-T','core','python','-m','btc_node','request'],
            input=json.dumps({'method':'reader.checkpoint'}), text=True, capture_output=True)
        if saved.returncode or not json.loads(saved.stdout).get('ok'):
            raise RuntimeError('reader checkpoint failed; do not acknowledge a newer Telegram offset')
    # getUpdates acknowledges the previous cursor. Persist that state before
    # the one polling request, and persist the new cursor before returning.
    checkpoint()
    result = subprocess.run(command + ['--profile', 'reader', 'run', '--rm', '-T', 'reader', 'reader', 'sync'],
                            input=CredentialVault().bot_token() + '\n', text=True)
    checkpoint()
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
