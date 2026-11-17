#!/bin/sh
# Run only during preparation of the Codex cloud development environment.
set -eu
case "${1:-}" in
  '') ;;
  --help) echo 'Usage: cloud-setup.sh'; exit 0 ;;
  --with-data-service) echo 'Data-service behavior validation NOT_RUN; use task-scoped temporary verification.' >&2; exit 2 ;;
  *) echo 'Usage: cloud-setup.sh' >&2; exit 2 ;;
esac
[ "$#" -eq 0 ] || exit 2

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"
python3.11 -c 'import sys; assert sys.version_info[:2] == (3, 11)'
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r core/btc-core-strategy/service/requirements.txt
.venv/bin/python -B roles/validate_repository.py
echo 'Source export and syntax checked; behavior and Docker/MySQL validation NOT_RUN.'
