"""Streamlit workbench for the deterministic brief.

Run from the repository root after installing the package:

    streamlit run src/ops_narrative/app.py --server.port 8741
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from ops_narrative import __version__
from ops_narrative.charts import write_figures
from ops_narrative.data.store import load_pack
from ops_narrative.identity import ENTITY_NAME
from ops_narrative.metrics.engine import build_sheet
from ops_narrative.narrative.compose import compose
from ops_narrative.narrative.templates import SPECS, active_template, canonicalize_kind
from ops_narrative.paths import repo_root, synthetic_dir
from ops_narrative.policy import METRIC_LABELS, SCORECARD_METRICS
from ops_narrative.review.faithfulness import format_report, review_markdown

DEFECT_SENTENCE = (
    "\n\nAn uncited upside of 123.4% was assumed for the close.\n"
)
_MACHINE_HEADER = re.compile(r"<!--\s*ops-narrative\b.*?-->\n*", re.DOTALL)


def display_markdown(narrative: str) -> str:
    """Hide the machine-readable header. Streamlit would otherwise print it."""
    return _MACHINE_HEADER.sub("", narrative, count=1)


def list_packs(root: Path | None = None) -> list[Path]:
    directory = synthetic_dir(root or repo_root())
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.json") if path.name != "manifest.json")


def main() -> None:
    st.set_page_config(page_title="Ops Narrative", page_icon="▣", layout="wide")
    _css()
    root = repo_root()
    packs = list_packs(root)
    st.sidebar.markdown("### Ops Narrative")
    st.sidebar.caption(f"Version {__version__} · deterministic engine")
    if not packs:
        st.sidebar.warning("No packs found.")
        st.info(
            "No synthetic packs are in `data/synthetic`. From the repository root run "
            "`ops-narrative samples`, then reload this page."
        )
        return

    labels = [path.stem for path in packs]
    selected = st.sidebar.selectbox("Period pack", labels, index=labels.index("2026-03") if "2026-03" in labels else 0)
    kind_label = st.sidebar.radio(
        "Brief",
        ["Month-end", "Variance commentary", "Exception brief"],
        index=0,
    )
    kind = {"Month-end": "month-end", "Variance commentary": "variance", "Exception brief": "exceptions"}[kind_label]
    versions = [spec.template_id for spec in SPECS if spec.kind == canonicalize_kind(kind)]
    default_version = active_template(kind).template_id
    template_id = st.sidebar.selectbox("Template", versions, index=versions.index(default_version))
    inject_defect = st.sidebar.checkbox("Inject an uncited figure", value=False)
    st.sidebar.caption("The inject control is a reviewer demo. It is not part of the brief.")

    pack = load_pack(next(path for path in packs if path.stem == selected))
    sheet = build_sheet(pack)
    narrative = compose(pack, template_id=template_id)
    if inject_defect:
        narrative = narrative + DEFECT_SENTENCE
    report = review_markdown(narrative, pack, template_id=template_id)

    st.markdown(f"# {ENTITY_NAME}")
    st.markdown("Evidence-backed month-end commentary from a structured KPI pack. Draft only. A person closes it.")
    st.info(pack.entity_disclaimer)

    tiles = st.columns(4)
    for column, metric in zip(tiles, ("revenue", "gross_margin", "otif", "forecast_accuracy")):
        fact = sheet.facts[f"network.{metric}.actual"]
        column.metric(METRIC_LABELS[metric], fact.primary)

    status = "Gate passed" if report.passed else "Gate failed"
    if report.passed:
        st.success(f"{status}. {format_report(report)}")
    else:
        st.error(f"{status}. {format_report(report)}")

    brief_tab, review_tab, figure_tab = st.tabs(["Brief", "Review", "Figures"])
    with brief_tab:
        st.markdown(display_markdown(narrative))
        st.download_button(
            "Download markdown",
            data=narrative,
            file_name=f"{pack.period}-{canonicalize_kind(kind)}.md",
            mime="text/markdown",
        )
    with review_tab:
        left, right = st.columns(2)
        left.metric("Faithfulness", f"{report.faithfulness_score:.2f}")
        right.metric("Coverage", f"{report.coverage_score:.2f}")
        st.caption(
            "Faithfulness requires every cited token to match the metric engine, "
            "no leftover numeral, a matching variance sign, and no causal connector. "
            "Coverage depends on the template version."
        )
        if report.findings:
            for finding in report.findings:
                st.markdown(f"- **{finding.code}.** {finding.detail}")
        else:
            st.markdown("No findings. The brief stayed inside the fact sheet and the template's coverage profile.")
        scorecard_rows = []
        for metric in SCORECARD_METRICS:
            scorecard_rows.append(
                {
                    "Metric": METRIC_LABELS[metric],
                    "Actual": sheet.facts[f"network.{metric}.actual"].primary,
                    "Plan": sheet.facts[f"network.{metric}.plan"].primary,
                }
            )
        st.dataframe(scorecard_rows, hide_index=True, use_container_width=True)
    with figure_tab:
        figure_dir = Path(tempfile.mkdtemp(prefix="ops-narrative-"))
        paths = write_figures(pack, figure_dir)
        columns = st.columns(3)
        captions = (
            "Revenue versus plan. Descriptive.",
            "OTIF against the standard. A miss is a breach, not a cause.",
            "Forecast accuracy against the floor.",
        )
        for column, path, caption in zip(columns, paths, captions):
            column.image(str(path), caption=caption, use_container_width=True)


def _css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f4f1ea; color: #243027; }
        [data-testid="stSidebar"] { background: #ebe4d8; }
        h1, h2, h3 { font-family: Georgia, "Iowan Old Style", serif; letter-spacing: -0.02em; }
        [data-testid="stMetric"] {
            background: #fffdf8;
            border: 1px solid #e0d8cc;
            padding: 0.6rem 0.8rem;
            border-radius: 2px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
