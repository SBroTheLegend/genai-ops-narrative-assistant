"""Regenerate the committed sample packs, briefs, and figures.

Equivalent to ``ops-narrative samples``. Run it from the repository root
after installing the package, or directly with this file on PYTHONPATH.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ops_narrative.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["samples"]))
