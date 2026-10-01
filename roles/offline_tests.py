#!/usr/bin/env python3
"""Use the collector-owned offline harness for this repository's export tests."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'core/market-collector/roles/offline_tests.py'
if not source.is_file():
    raise FileNotFoundError('initialize pinned collector: git submodule update --init core/market-collector')
spec = importlib.util.spec_from_file_location('collector_offline', source)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
sys.path.insert(0, str(ROOT))
if not sys.argv[1:]:
    sys.argv.append('test_role_export')
if __name__ == '__main__':
    raise SystemExit(harness.main())
