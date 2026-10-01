#!/bin/sh
# Run only during preparation of the Codex cloud development environment.
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_root"
python3.11 -c 'import sys; assert sys.version_info[:2] == (3, 11)'
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B roles/validate_repository.py
