"""Use the shared helper when invoking an analysis CLI from its source checkout."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from roles.role_support import *  # noqa: F401,F403
