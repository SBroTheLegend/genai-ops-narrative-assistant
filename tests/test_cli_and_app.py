"""CLI and workbench smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ops_narrative.cli import main
from ops_narrative.data.generate import generate_pack
from ops_narrative.data.store import dump_pack
from ops_narrative.identity import HERO_PERIOD


def test_help_exits_cleanly():
    completed = subprocess.run(
        [sys.executable, "-m", "ops_narrative.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "deterministic" in completed.stdout


def test_narrate_and_review_round_trip(tmp_path: Path):
    pack_path = tmp_path / "pack.json"
    brief_path = tmp_path / "brief.md"
    dump_pack(generate_pack(HERO_PERIOD), pack_path)
    assert main(["narrate", "--pack", str(pack_path), "--kind", "month-end", "--out", str(brief_path), "--review"]) == 0
    assert brief_path.is_file()
    assert main(["review", "--pack", str(pack_path), "--narrative", str(brief_path)]) == 0
    brief_path.write_text(brief_path.read_text(encoding="utf-8") + "\nLoose figure 42.0%.\n", encoding="utf-8")
    assert main(["review", "--pack", str(pack_path), "--narrative", str(brief_path)]) == 1


def test_samples_command_writes_a_passing_review(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPS_NARRATIVE_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "src" / "ops_narrative").mkdir(parents=True)
    assert main(["samples"]) == 0
    review = json.loads((tmp_path / "samples" / "outputs" / f"{HERO_PERIOD}-review.json").read_text(encoding="utf-8"))
    assert review["passed"] is True
    assert review["faithfulness_score"] == 1
    assert (tmp_path / "samples" / "figures" / f"{HERO_PERIOD}-otif.png").stat().st_size > 1000
    assert (tmp_path / "data" / "synthetic" / f"{HERO_PERIOD}.json").is_file()


def test_charts_are_pngs(tmp_path: Path):
    from ops_narrative.charts import write_figures

    paths = write_figures(generate_pack(HERO_PERIOD), tmp_path)
    assert len(paths) == 3
    for path in paths:
        assert path.read_bytes().startswith(b"\x89PNG")


def test_app_imports_and_lists_packs(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OPS_NARRATIVE_HOME", str(tmp_path))
    pack_dir = tmp_path / "data" / "synthetic"
    pack_dir.mkdir(parents=True)
    dump_pack(generate_pack(HERO_PERIOD), pack_dir / f"{HERO_PERIOD}.json")
    from ops_narrative.app import list_packs

    found = list_packs(tmp_path)
    assert [path.name for path in found] == [f"{HERO_PERIOD}.json"]


def test_streamlit_smoke(tmp_path: Path, monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("OPS_NARRATIVE_HOME", str(tmp_path))
    pack_dir = tmp_path / "data" / "synthetic"
    pack_dir.mkdir(parents=True)
    dump_pack(generate_pack(HERO_PERIOD), pack_dir / f"{HERO_PERIOD}.json")
    app_path = Path("src/ops_narrative/app.py").resolve()
    app_test = AppTest.from_file(str(app_path), default_timeout=90)
    app_test.run()
    assert not app_test.exception
    assert len(app_test.markdown) > 0
