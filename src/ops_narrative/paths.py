"""Locate the repository root whether the package is installed or run from source."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    override = os.environ.get("OPS_NARRATIVE_HOME")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "ops_narrative").is_dir():
            return candidate
    return Path.cwd().resolve()


def synthetic_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "data" / "synthetic"


def sample_output_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "samples" / "outputs"


def sample_figure_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "samples" / "figures"
