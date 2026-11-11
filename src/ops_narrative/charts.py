"""Figures for a pack.

Charts describe the same rollups as the brief. They are not a second
analysis, and the captions say so. A threshold line is the published
standard, not a trend the data was fitted to.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ops_narrative.identity import FACILITIES, facility_label
from ops_narrative.metrics.engine import build_sheet
from ops_narrative.models import KpiPack
from ops_narrative.policy import OTIF_STANDARD

INK = "#243027"
PAPER = "#f4f1ea"
ACTUAL = "#1f4d3a"
PLAN = "#b7ad9e"
ALERT = "#8c3a32"
MUTED = "#5c6560"


def write_figures(pack: KpiPack, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [
        out_dir / f"{pack.period}-revenue-vs-plan.png",
        out_dir / f"{pack.period}-otif.png",
        out_dir / f"{pack.period}-forecast-accuracy.png",
    ]
    sheet = build_sheet(pack)
    _revenue(pack, sheet, paths[0])
    _otif(pack, sheet, paths[1])
    _accuracy(pack, sheet, paths[2])
    return paths


def _style(ax, title: str, pack: KpiPack) -> None:
    ax.set_title(title, loc="left", color=INK, fontsize=13, pad=12)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#d9d3c7")
    ax.set_facecolor(PAPER)
    ax.yaxis.grid(True, color="#e4ded3", linewidth=0.8)
    ax.set_axisbelow(True)
    caption = f"{pack.entity_name} · {pack.period} · fictional synthetic pack · not a causal chart"
    ax.figure.text(0.01, 0.01, caption, color=MUTED, fontsize=8)


def _revenue(pack: KpiPack, sheet, path: Path) -> None:
    labels = [facility_label(facility) for facility in FACILITIES]
    actual = [sheet.slices[f"facility.{facility}"].levels["revenue"].actual / 1_000_000 for facility in FACILITIES]
    plan = [sheet.slices[f"facility.{facility}"].levels["revenue"].plan / 1_000_000 for facility in FACILITIES]
    fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=140, facecolor=PAPER)
    positions = range(len(labels))
    width = 0.36
    ax.bar([item - width / 2 for item in positions], plan, width=width, color=PLAN, label="Plan")
    ax.bar([item + width / 2 for item in positions], actual, width=width, color=ACTUAL, label="Actual")
    ax.set_xticks(list(positions), labels)
    ax.set_ylabel("Net revenue ($ millions)", color=MUTED)
    ax.legend(frameon=False, loc="upper right")
    _style(ax, "Net revenue versus plan by node", pack)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)


def _otif(pack: KpiPack, sheet, path: Path) -> None:
    labels = [facility_label(facility) for facility in FACILITIES]
    values = [sheet.slices[f"facility.{facility}"].levels["otif"].actual * 100 for facility in FACILITIES]
    colors = [ALERT if value < OTIF_STANDARD * 100 else ACTUAL for value in values]
    fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=140, facecolor=PAPER)
    ax.bar(labels, values, color=colors)
    ax.axhline(OTIF_STANDARD * 100, color=ALERT, linestyle="--", linewidth=1.2)
    ax.set_ylabel("OTIF (%)", color=MUTED)
    ax.set_ylim(80, 100)
    _style(ax, "OTIF by node. Dashed line is the 95% standard.", pack)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)


def _accuracy(pack: KpiPack, sheet, path: Path) -> None:
    from ops_narrative.identity import FAMILIES, family_label
    from ops_narrative.policy import FORECAST_ACCURACY_FLOOR

    labels = [family_label(family) for family in FAMILIES]
    values = [sheet.slices[f"family.{family}"].levels["forecast_accuracy"].actual * 100 for family in FAMILIES]
    colors = [ALERT if value < FORECAST_ACCURACY_FLOOR * 100 else ACTUAL for value in values]
    fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=140, facecolor=PAPER)
    ax.bar(labels, values, color=colors)
    ax.axhline(FORECAST_ACCURACY_FLOOR * 100, color=ALERT, linestyle="--", linewidth=1.2)
    ax.set_ylabel("Forecast accuracy (%)", color=MUTED)
    ax.set_ylim(50, 100)
    _style(ax, "Forecast accuracy by category. Dashed line is the 80% floor.", pack)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, facecolor=PAPER)
    plt.close(fig)
