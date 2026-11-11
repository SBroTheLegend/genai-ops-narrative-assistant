"""Materiality and exception policy.

The narrative and the reviewer both import this module. A threshold that
lives only in a sentence would let the prose and the gate drift apart.

Comparisons use the same displayed precision as the brief, so a figure that
prints as 95.0% is not also described as a breach of a 95.0% standard.
"""

from __future__ import annotations

from dataclasses import dataclass

from ops_narrative.formatutil import rhu

# Service and demand standards. Equal to the bar is acceptable.
OTIF_STANDARD = 0.95
FORECAST_ACCURACY_FLOOR = 0.80
FILL_RATE_STANDARD = 0.97

# Inclusive breach bars versus plan.
DOS_CEILING_FACTOR = 1.15
MARGIN_SHORTFALL = 0.005  # -50 bps versus plan breaches
REVENUE_SHORTFALL = 0.03  # -3.0% versus plan breaches
EXPEDITE_OVERRUN = 0.25  # +25.0% versus plan breaches

# A cell is named only when it holds this share of the parent plan variance,
# and not when offsets push the share above the whole parent gap.
DRILL_SHARE = 0.60
DRILL_SHARE_CAP = 1.0

# A node or category that moves with the network, but not this many times
# harder, is the same story. It stays off the variance table.
CONCENTRATION_RATIO = 1.5

# Narrative grain. Cells are used to audit rollups and, rarely, one drill sentence.
COMMENTARY_SCOPES: frozenset[str] = frozenset({"network", "facility", "family"})

SCORECARD_METRICS: tuple[str, ...] = (
    "revenue",
    "gross_margin",
    "otif",
    "forecast_accuracy",
    "dos",
    "fill_rate",
    "expedite_cost",
    "inventory",
)

# How a plan variance is spoken in prose and on the scorecard.
VARIANCE_STYLE: dict[str, str] = {
    "revenue": "pct",
    "gross_profit": "pct",
    "inventory": "pct",
    "expedite_cost": "pct",
    "gross_margin": "bps",
    "otif": "pp",
    "forecast_accuracy": "pp",
    "fill_rate": "pp",
    "dos": "days",
    "wape": "pp",
}

RATIO_METRICS: frozenset[str] = frozenset(
    {"gross_margin", "otif", "forecast_accuracy", "fill_rate", "wape"}
)
USD_METRICS: frozenset[str] = frozenset(
    {"revenue", "cogs", "gross_profit", "inventory", "expedite_cost"}
)

# Topics an operating note is allowed to sit beside. A service note is not
# quoted under a revenue breach.
METRIC_TOPIC: dict[str, str] = {
    "revenue": "commercial",
    "gross_profit": "commercial",
    "gross_margin": "commercial",
    "inventory": "inventory",
    "dos": "inventory",
    "otif": "service",
    "fill_rate": "service",
    "expedite_cost": "service",
    "forecast_accuracy": "forecast",
    "wape": "forecast",
}

METRIC_LABELS: dict[str, str] = {
    "revenue": "Net revenue",
    "gross_profit": "Gross profit",
    "gross_margin": "Gross margin",
    "inventory": "Ending inventory",
    "dos": "Days of supply",
    "otif": "OTIF",
    "forecast_accuracy": "Forecast accuracy",
    "fill_rate": "Line fill rate",
    "expedite_cost": "Expedite cost",
    "wape": "Forecast WAPE",
}


@dataclass(frozen=True)
class MaterialityRule:
    """A movement is material when any configured test fires.

    Ratio metrics use an absolute gap only. A percent-of-a-percent test
    would call a 2% relative move on a 27% margin material even when the
    gap is a few basis points.
    """

    abs_usd: float | None = None
    rel: float | None = None
    abs_ratio: float | None = None
    abs_days: float | None = None


MATERIALITY: dict[str, MaterialityRule] = {
    # Absolute dollars are a backstop for a large sum that is still under the
    # rate bar. On a network near $44M, a 2% revenue miss is about $0.9M, so
    # the $1M backstop does not reclassify a 1% miss as material.
    "revenue": MaterialityRule(abs_usd=1_000_000, rel=0.02),
    "gross_profit": MaterialityRule(abs_usd=500_000, rel=0.02),
    "inventory": MaterialityRule(abs_usd=2_000_000, rel=0.10),
    "expedite_cost": MaterialityRule(abs_usd=50_000, rel=0.15),
    "gross_margin": MaterialityRule(abs_ratio=0.005),
    "otif": MaterialityRule(abs_ratio=0.01),
    "forecast_accuracy": MaterialityRule(abs_ratio=0.02),
    "fill_rate": MaterialityRule(abs_ratio=0.01),
    "dos": MaterialityRule(abs_days=3.0),
    "wape": MaterialityRule(abs_ratio=0.02),
}


def displayed_percent(ratio: float) -> float:
    return float(rhu(ratio * 100, 1))


def displayed_bps(delta_ratio: float) -> int:
    return int(rhu(delta_ratio * 10_000, 0))


def displayed_days(value: float) -> float:
    return float(rhu(value, 1))


def breaches_otif(actual: float) -> bool:
    return displayed_percent(actual) < displayed_percent(OTIF_STANDARD)


def breaches_forecast_accuracy(actual: float) -> bool:
    return displayed_percent(actual) < displayed_percent(FORECAST_ACCURACY_FLOOR)


def breaches_fill_rate(actual: float) -> bool:
    return displayed_percent(actual) < displayed_percent(FILL_RATE_STANDARD)


def breaches_dos(actual: float, plan: float) -> bool:
    ceiling = displayed_days(plan * DOS_CEILING_FACTOR)
    return displayed_days(actual) > ceiling


def breaches_margin(actual: float, plan: float) -> bool:
    return displayed_bps(actual - plan) <= -50


def breaches_revenue(actual: float, plan: float) -> bool:
    if plan == 0:
        return False
    return displayed_percent((actual - plan) / plan) <= displayed_percent(-REVENUE_SHORTFALL)


def breaches_expedite(actual: float, plan: float) -> bool:
    if plan == 0:
        return False
    return displayed_percent((actual - plan) / plan) >= displayed_percent(EXPEDITE_OVERRUN)


def materiality(
    metric: str, actual: float | None, baseline: float | None
) -> str | None:
    """Return ``absolute``, ``relative``, or ``both`` when the gap clears the bar."""
    if actual is None or baseline is None:
        return None
    rule = MATERIALITY[metric]
    reasons: set[str] = set()
    delta = actual - baseline
    if rule.abs_usd is not None and abs(delta) >= rule.abs_usd:
        reasons.add("absolute")
    if rule.abs_days is not None and abs(displayed_days(delta)) >= rule.abs_days:
        reasons.add("absolute")
    if rule.abs_ratio is not None and _ratio_gap_is_material(metric, delta, rule.abs_ratio):
        reasons.add("absolute")
    if rule.rel is not None and baseline != 0:
        if abs(displayed_percent(delta / baseline)) >= displayed_percent(rule.rel):
            reasons.add("relative")
    if not reasons:
        return None
    if reasons == {"absolute", "relative"}:
        return "both"
    return next(iter(reasons))


def _ratio_gap_is_material(metric: str, delta: float, bar: float) -> bool:
    """Match the unit the brief actually prints.

    Margin is judged in basis points. A 49 bps gap must not become material
    just because it rounds to 0.5 percentage points.
    """
    if VARIANCE_STYLE[metric] == "bps":
        return abs(displayed_bps(delta)) >= abs(displayed_bps(bar))
    return abs(displayed_percent(delta)) >= displayed_percent(bar)


def trigger_phrase(triggered_by: str) -> str:
    if triggered_by == "both":
        return "clears the absolute and relative bars"
    if triggered_by == "absolute":
        return "clears the absolute bar"
    if triggered_by == "relative":
        return "clears the relative bar"
    raise ValueError(f"unknown materiality trigger {triggered_by!r}")
