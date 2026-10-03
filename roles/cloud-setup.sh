#!/bin/sh
# Run only during preparation of the Codex cloud development environment.
set -eu
with_data_service=false
case "${1:-}" in
  '') ;;
  --with-data-service) with_data_service=true; shift ;;
  --help) echo 'Usage: cloud-setup.sh [--with-data-service]'; exit 0 ;;
  *) echo 'Usage: cloud-setup.sh [--with-data-service]' >&2; exit 2 ;;
esac
[ "$#" -eq 0 ] || exit 2

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"
python3.11 -c 'import sys; assert sys.version_info[:2] == (3, 11)'
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r core/btc-core-strategy/service/requirements.txt
if [ "$with_data_service" = true ]; then
  docker version
  docker compose version
  .venv/bin/python -B roles/validate_repository.py --with-data-service
else
  .venv/bin/python -B roles/validate_repository.py
  echo 'Offline preparation passed; Docker/MySQL data-service validation NOT_RUN.'
fi
