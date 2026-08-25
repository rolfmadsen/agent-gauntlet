#!/usr/bin/env python3
"""Convenience CLI wrapper for computing source tree hash and git state."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from agent_gauntlet.features.evidence.source_state import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(ROOT))
