"""Keep reader credentials in the existing native Keychain and sync in Docker."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time


def _checkpoint_attempt(command, phase):
    """Expose safe diagnostics without copying service output or credentials."""
    event = {'event': 'reader.checkpoint', 'phase': phase,
             'started_at': datetime.now(timezone.utc).isoformat()}
    try:
        saved = subprocess.run(command + ['exec', '-T', 'core', 'python', '-m', 'btc_node', 'request'],
            input=json.dumps({'method': 'reader.checkpoint'}), text=True, capture_output=True)
    except OSError as exc:
        event.update(ok=False, reason='PROCESS_START_FAILED', errno=exc.errno)
    else:
        event['returncode'] = saved.returncode
        try:
            response = json.loads(saved.stdout)
        except ValueError:
            response = None
        valid = isinstance(response, dict)
        result = response.get('result') if valid else None
        event['ok'] = (saved.returncode == 0 and valid and response.get('ok') is True
                       and isinstance(result, dict) and result.get('checkpointed') is True)
        if not event['ok']:
            error = response.get('error') if valid else None
            # Error names and free text are also untrusted. Keep only known classes
            # and classifications; never emit raw stdout/stderr, paths or settings.
            known = {'Conflict', 'ValueError', 'KeyError', 'TypeError', 'OperationalError',
                     'IntegrityError', 'DatabaseError', 'PermissionError', 'FileNotFoundError',
                     'ConnectionRefusedError', 'TimeoutError', 'OSError', 'RuntimeError'}
            event['service_error'] = error if isinstance(error, str) and error in known else 'UNCLASSIFIED'
            message = response.get('message') if valid else None
            reason = 'SERVICE_REJECTED' if valid and response.get('ok') is False else 'INVALID_RESPONSE'
            if error == 'Conflict' and isinstance(message, str):
                if message == 'another node writer is active; retry the same operation':
                    reason = 'WRITER_BUSY'
                elif message == 'reader checkpoint requires the active Docker writer':
                    reason = 'WRITER_NOT_DOCKER'
                elif message.startswith('source changed during catalog import: '):
                    reason = 'SOURCE_CHANGED'
            if not valid and saved.returncode:
                reason = 'PROCESS_FAILED'
            event['reason'] = reason
    event['finished_at'] = datetime.now(timezone.utc).isoformat()
    return event


def checkpoint(command, phase):
    # A normal analysis stage can outlast the core's 30-second writer admission.
    # Retry only that explicit rejection, within this same scheduled phase.
    # Neither a failed poll nor an unconfirmed response permits another poll.
    for attempt in range(1, 4):
        event = _checkpoint_attempt(command, phase)
        retry = event.get('reason') == 'WRITER_BUSY' and attempt < 3
        event.update(attempt=attempt, retry=retry)
        print(json.dumps(event, sort_keys=True), file=sys.stderr, flush=True)
        if event['ok']:
            return
        if not retry:
            raise RuntimeError('reader checkpoint failed; do not acknowledge a newer Telegram offset')
        time.sleep(5)


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
    # getUpdates acknowledges the previous cursor. Persist that state before
    # the one polling request, and persist the new cursor before returning.
    checkpoint(command, 'BEFORE_POLL')
    result = subprocess.run(command + ['--profile', 'reader', 'run', '--rm', '-T', 'reader', 'reader', 'sync'],
                            input=CredentialVault().bot_token() + '\n', text=True)
    checkpoint(command, 'AFTER_POLL')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
