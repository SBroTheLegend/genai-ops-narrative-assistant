"""Compute the fact sheet the narrative is allowed to cite.

Rates are recomputed from additive inputs at every grain. A node OTIF is
units on time and in full divided by units ordered, not the average of the
category rates underneath it. The same rule is what the reviewer rebuilds.
"""

from __future__ import annotations

from dataclasses import dataclass

from ops_narrative.formatutil import (
    format_bps,
    format_days,
    format_percent,
    format_pp,
    format_usd,
)
from ops_narrative.identity import FAMILIES, FACILITIES, slice_label
from ops_narrative.models import ADDITIVE_METRICS, COUNT_METRICS, MONEY_METRICS, Cell, KpiPack
from ops_narrative.policy import (
    COMMENTARY_SCOPES,
    DOS_CEILING_FACTOR,
    CONCENTRATION_RATIO,
    DRILL_SHARE,
    DRILL_SHARE_CAP,
    EXPEDITE_OVERRUN,
    FILL_RATE_STANDARD,
    FORECAST_ACCURACY_FLOOR,
    MARGIN_SHORTFALL,
    METRIC_TOPIC,
    OTIF_STANDARD,
    REVENUE_SHORTFALL,
    SCORECARD_METRICS,
    VARIANCE_STYLE,
    breaches_dos,
    breaches_expedite,
    breaches_fill_rate,
    breaches_forecast_accuracy,
    breaches_margin,
    breaches_otif,
    breaches_revenue,
    displayed_bps,
    displayed_days,
    displayed_percent,
    materiality,
)

DERIVED_METRICS: tuple[str, ...] = (
    "revenue",
    "gross_profit",
    "gross_margin",
    "inventory",
    "dos",
    "otif",
    "wape",
    "forecast_accuracy",
    "fill_rate",
    "expedite_cost",
)

_BASELINE_TO_SUFFIX = {"plan": "plan", "prior": "prior", "py": "py"}
_SUFFIX_TO_ATTR = {"plan": "plan", "prior": "prior_period", "py": "prior_year"}


@dataclass(frozen=True)
class Fact:
    fact_id: str
    value: float
    primary: str


@dataclass(frozen=True)
class Level:
    actual: float | None
    plan: float | None
    prior_period: float | None
    prior_year: float | None

    def baseline(self, name: str) -> float | None:
        return getattr(self, _SUFFIX_TO_ATTR[name])


@dataclass(frozen=True)
class SliceView:
    slice_id: str
    scope: str
    facility: str | None
    family: str | None
    label: str
    levels: dict[str, Level]


@dataclass(frozen=True)
class MaterialVariance:
    variance_id: str
    slice_id: str
    scope: str
    label: str
    metric: str
    baseline: str
    triggered_by: str
    signed_fact: str
    abs_fact: str
    rank_key: float


@dataclass(frozen=True)
class ExceptionItem:
    exception_id: str
    slice_id: str
    scope: str
    label: str
    metric: str
    rule: str
    actual_fact: str
    comparison_fact: str
    bar_fact: str
    note_ids: tuple[str, ...]
    severity: float


@dataclass(frozen=True)
class Drill:
    parent_slice: str
    cell_slice: str
    cell_label: str
    metric: str
    share_fact: str


@dataclass(frozen=True)
class FactSheet:
    pack: KpiPack
    facts: dict[str, Fact]
    slices: dict[str, SliceView]
    exceptions: tuple[ExceptionItem, ...]
    material: tuple[MaterialVariance, ...]
    broad_metrics: frozenset[str]
    drills: tuple[Drill, ...]

    def cite(self, fact_id: str) -> str:
        try:
            fact = self.facts[fact_id]
        except KeyError as exc:
            raise KeyError(f"Fact {fact_id} is not on the sheet for {self.pack.period}.") from exc
        return f"[{fact.primary}](cite:{fact_id})"


def build_sheet(pack: KpiPack) -> FactSheet:
    views = _views(pack)
    facts: dict[str, Fact] = {}
    facts.update(_policy_facts())
    for view in views.values():
        _add_slice_facts(facts, view)
        if view.levels["dos"].plan is not None:
            ceiling = view.levels["dos"].plan * DOS_CEILING_FACTOR
            fact_id = f"{view.slice_id}.dos.ceiling"
            facts[fact_id] = Fact(fact_id, ceiling, format_days(ceiling))

    material, broad_metrics = _material(views)
    exceptions = _exceptions(pack, views)
    drills = _drills(views, material, facts)
    facts["meta.material_count"] = Fact(
        "meta.material_count", float(len(material)), str(len(material))
    )
    facts["meta.exception_count"] = Fact(
        "meta.exception_count", float(len(exceptions)), str(len(exceptions))
    )
    return FactSheet(
        pack=pack,
        facts=facts,
        slices=views,
        exceptions=exceptions,
        material=material,
        broad_metrics=broad_metrics,
        drills=drills,
    )


def _views(pack: KpiPack) -> dict[str, SliceView]:
    cells = list(pack.cells)
    views: dict[str, SliceView] = {}
    groups: list[tuple[str, str | None, str | None, list[Cell]]] = [
        ("network", None, None, cells)
    ]
    facilities = _preferred([cell.facility for cell in cells], FACILITIES)
    families = _preferred([cell.family for cell in cells], FAMILIES)
    for facility in facilities:
        groups.append(("facility", facility, None, [cell for cell in cells if cell.facility == facility]))
    for family in families:
        groups.append(("family", None, family, [cell for cell in cells if cell.family == family]))
    for cell in sorted(cells, key=lambda item: (facilities.index(item.facility) if item.facility in facilities else 99, item.family)):
        groups.append(("cell", cell.facility, cell.family, [cell]))

    for scope, facility, family, group in groups:
        slice_id = _slice_id(scope, facility, family)
        levels = _levels(group, pack.days_in_period)
        views[slice_id] = SliceView(
            slice_id=slice_id,
            scope=scope,
            facility=facility,
            family=family,
            label=slice_label(scope, facility, family),
            levels=levels,
        )
    return views


def _levels(group: list[Cell], days: int) -> dict[str, Level]:
    by_baseline: dict[str, dict[str, float | None]] = {}
    for key in ("actual", "plan", "prior_period", "prior_year"):
        by_baseline[key] = _derive(_sum_inputs(group, key), days)
    levels: dict[str, Level] = {}
    for metric in DERIVED_METRICS:
        levels[metric] = Level(
            actual=by_baseline["actual"][metric],
            plan=by_baseline["plan"][metric],
            prior_period=by_baseline["prior_period"][metric],
            prior_year=by_baseline["prior_year"][metric],
        )
    return levels


def _sum_inputs(group: list[Cell], key: str) -> dict[str, float] | None:
    totals = {name: 0.0 for name in ADDITIVE_METRICS}
    for cell in group:
        for name in ADDITIVE_METRICS:
            value = cell.measures[name].value(key)
            if value is None:
                return None
            totals[name] += value
    for name in MONEY_METRICS:
        totals[name] = round(totals[name], 2)
    for name in COUNT_METRICS:
        totals[name] = float(round(totals[name]))
    return totals


def _derive(totals: dict[str, float] | None, days: int) -> dict[str, float | None]:
    empty = {metric: None for metric in DERIVED_METRICS}
    if totals is None:
        return empty
    revenue = totals["revenue"]
    cogs = totals["cogs"]
    gross_profit = revenue - cogs
    ordered = totals["units_ordered"]
    units = totals["units"]
    lines = totals["lines_ordered"]
    wape = (totals["abs_unit_error"] / units) if units else None
    return {
        "revenue": revenue,
        "gross_profit": gross_profit,
        "gross_margin": (gross_profit / revenue) if revenue else None,
        "inventory": totals["inventory"],
        "dos": (totals["inventory"] / (cogs / days)) if cogs else None,
        "otif": (totals["units_otif"] / ordered) if ordered else None,
        "wape": wape,
        "forecast_accuracy": None if wape is None else max(0.0, 1.0 - wape),
        "fill_rate": (totals["lines_filled"] / lines) if lines else None,
        "expedite_cost": totals["expedite_cost"],
    }


def _add_slice_facts(facts: dict[str, Fact], view: SliceView) -> None:
    for metric, level in view.levels.items():
        for field, value in (
            ("actual", level.actual),
            ("plan", level.plan),
            ("prior_period", level.prior_period),
            ("prior_year", level.prior_year),
        ):
            if value is None:
                continue
            fact_id = f"{view.slice_id}.{metric}.{field}"
            facts[fact_id] = Fact(fact_id, value, _format_level(metric, value))
        for baseline in ("plan", "prior", "py"):
            base = level.baseline(baseline)
            if level.actual is None or base is None:
                continue
            _add_variance(facts, view.slice_id, metric, baseline, level.actual, base)


def _add_variance(
    facts: dict[str, Fact],
    slice_id: str,
    metric: str,
    baseline: str,
    actual: float,
    base: float,
) -> None:
    delta = actual - base
    style = VARIANCE_STYLE[metric]
    if style == "pct":
        _put_usd_variance(facts, slice_id, metric, baseline, delta)
        if base != 0:
            _put_pair(
                facts,
                f"{slice_id}.{metric}.var_{baseline}_pct",
                delta / base,
                lambda value, signed: format_percent(value, signed=signed),
                lambda value, signed: format_percent(value, signed=signed, absolute=True),
            )
    elif style in {"pp", "bps"}:
        _put_pair(
            facts,
            f"{slice_id}.{metric}.var_{baseline}_pp",
            delta,
            lambda value, signed: format_pp(value, signed=signed),
            lambda value, signed: format_pp(value, signed=signed, absolute=True),
        )
        _put_pair(
            facts,
            f"{slice_id}.{metric}.var_{baseline}_bps",
            delta,
            lambda value, signed: format_bps(value, signed=signed),
            lambda value, signed: format_bps(value, signed=signed, absolute=True),
        )
    elif style == "days":
        _put_pair(
            facts,
            f"{slice_id}.{metric}.var_{baseline}_days",
            delta,
            lambda value, signed: format_days(value, signed=signed),
            lambda value, signed: format_days(value, signed=signed, absolute=True),
        )
    else:
        raise KeyError(style)


def _put_usd_variance(facts: dict[str, Fact], slice_id: str, metric: str, baseline: str, delta: float) -> None:
    _put_pair(
        facts,
        f"{slice_id}.{metric}.var_{baseline}_usd",
        delta,
        lambda value, signed: format_usd(value, signed=signed),
        lambda value, signed: format_usd(value, signed=signed, absolute=True),
    )


def _put_pair(facts, stem: str, value: float, signed_fmt, abs_fmt) -> None:
    facts[f"{stem}_signed"] = Fact(f"{stem}_signed", value, signed_fmt(value, True))
    facts[f"{stem}_abs"] = Fact(f"{stem}_abs", abs(value), abs_fmt(value, False))


def _format_level(metric: str, value: float) -> str:
    if metric in {"revenue", "gross_profit", "inventory", "expedite_cost"}:
        return format_usd(value)
    if metric == "dos":
        return format_days(value)
    return format_percent(value)


def _policy_facts() -> dict[str, Fact]:
    rows = {
        "policy.otif_standard": (OTIF_STANDARD, format_percent(OTIF_STANDARD)),
        "policy.forecast_accuracy_floor": (
            FORECAST_ACCURACY_FLOOR,
            format_percent(FORECAST_ACCURACY_FLOOR),
        ),
        "policy.fill_rate_standard": (FILL_RATE_STANDARD, format_percent(FILL_RATE_STANDARD)),
        "policy.revenue_shortfall": (
            -REVENUE_SHORTFALL,
            format_percent(-REVENUE_SHORTFALL, signed=True),
        ),
        "policy.expedite_overrun": (
            EXPEDITE_OVERRUN,
            format_percent(EXPEDITE_OVERRUN, signed=True),
        ),
        "policy.margin_shortfall": (
            -MARGIN_SHORTFALL,
            format_bps(-MARGIN_SHORTFALL, signed=True),
        ),
        "policy.dos_headroom": (DOS_CEILING_FACTOR - 1.0, format_percent(DOS_CEILING_FACTOR - 1.0)),
        "policy.drill_share": (DRILL_SHARE, format_percent(DRILL_SHARE)),
    }
    return {fact_id: Fact(fact_id, value, primary) for fact_id, (value, primary) in rows.items()}


def _material(views: dict[str, SliceView]) -> tuple[tuple[MaterialVariance, ...], frozenset[str]]:
    found: list[MaterialVariance] = []
    for metric in SCORECARD_METRICS:
        for view in views.values():
            if view.scope not in COMMENTARY_SCOPES:
                continue
            level = view.levels[metric]
            triggered = materiality(metric, level.actual, level.plan)
            if triggered is None or level.actual is None or level.plan is None:
                continue
            style = VARIANCE_STYLE[metric]
            signed = f"{view.slice_id}.{metric}.var_plan_{style}_signed"
            absolute = f"{view.slice_id}.{metric}.var_plan_{style}_abs"
            found.append(
                MaterialVariance(
                    variance_id=f"mat.{view.slice_id}.{metric}.plan",
                    slice_id=view.slice_id,
                    scope=view.scope,
                    label=view.label,
                    metric=metric,
                    baseline="plan",
                    triggered_by=triggered,
                    signed_fact=signed,
                    abs_fact=absolute,
                    rank_key=abs(level.actual - level.plan),
                )
            )
    kept = _drop_echoes(views, found)
    order = {metric: index for index, metric in enumerate(SCORECARD_METRICS)}
    kept.sort(key=lambda item: (order[item.metric], -item.rank_key, item.variance_id))
    network_metrics = {item.metric for item in kept if item.slice_id == "network"}
    raw_local = {item.metric for item in found if item.slice_id != "network"}
    kept_local = {item.metric for item in kept if item.slice_id != "network"}
    broad = frozenset(metric for metric in network_metrics if metric in raw_local and metric not in kept_local)
    return tuple(kept), broad


def _drop_echoes(views: dict[str, SliceView], found: list[MaterialVariance]) -> list[MaterialVariance]:
    """Keep a local slice when it is the story, not a copy of the network gap."""
    network_by_metric = {item.metric: item for item in found if item.slice_id == "network"}
    kept: list[MaterialVariance] = []
    for item in found:
        if item.slice_id == "network" or item.metric not in network_by_metric:
            kept.append(item)
            continue
        local_delta = _plan_delta(views[item.slice_id], item.metric)
        network_delta = _plan_delta(views["network"], item.metric)
        local_gap = _comparable_gap(views[item.slice_id].levels[item.metric], item.metric)
        network_gap = _comparable_gap(views["network"].levels[item.metric], item.metric)
        same_direction = (
            local_delta is not None
            and network_delta is not None
            and local_delta * network_delta > 0
        )
        if (
            same_direction
            and local_gap is not None
            and network_gap is not None
            and network_gap > 0
            and local_gap < CONCENTRATION_RATIO * network_gap
        ):
            continue
        kept.append(item)
    return kept


def _comparable_gap(level: Level, metric: str) -> float | None:
    if level.actual is None or level.plan is None:
        return None
    delta = level.actual - level.plan
    style = VARIANCE_STYLE[metric]
    if style == "pct":
        if level.plan == 0:
            return abs(delta)
        return abs(displayed_percent(delta / level.plan))
    if style == "bps":
        return float(abs(displayed_bps(delta)))
    if style == "pp":
        return abs(displayed_percent(delta))
    if style == "days":
        return abs(displayed_days(delta))
    raise KeyError(style)


def _exceptions(pack: KpiPack, views: dict[str, SliceView]) -> tuple[ExceptionItem, ...]:
    found: list[ExceptionItem] = []
    for view in views.values():
        if view.scope not in COMMENTARY_SCOPES:
            continue
        found.extend(_slice_exceptions(pack, view))
    found.sort(key=lambda item: (-item.severity, item.exception_id))
    return tuple(found)


def _slice_exceptions(pack: KpiPack, view: SliceView) -> list[ExceptionItem]:
    items: list[ExceptionItem] = []
    otif = view.levels["otif"].actual
    if otif is not None and breaches_otif(otif):
        items.append(
            _exception(
                pack,
                view,
                "otif",
                "below_standard",
                "policy.otif_standard",
                abs(displayed_percent(otif) - displayed_percent(OTIF_STANDARD)),
            )
        )
    accuracy = view.levels["forecast_accuracy"].actual
    if accuracy is not None and breaches_forecast_accuracy(accuracy):
        items.append(
            _exception(
                pack,
                view,
                "forecast_accuracy",
                "below_floor",
                "policy.forecast_accuracy_floor",
                abs(displayed_percent(accuracy) - displayed_percent(FORECAST_ACCURACY_FLOOR)),
            )
        )
    fill = view.levels["fill_rate"].actual
    if fill is not None and breaches_fill_rate(fill):
        items.append(
            _exception(
                pack,
                view,
                "fill_rate",
                "below_standard",
                "policy.fill_rate_standard",
                abs(displayed_percent(fill) - displayed_percent(FILL_RATE_STANDARD)),
            )
        )
    dos = view.levels["dos"]
    if dos.actual is not None and dos.plan is not None and breaches_dos(dos.actual, dos.plan):
        items.append(
            _exception(
                pack,
                view,
                "dos",
                "above_ceiling",
                f"{view.slice_id}.dos.ceiling",
                abs(dos.actual - dos.plan * DOS_CEILING_FACTOR),
            )
        )
    margin = view.levels["gross_margin"]
    if margin.actual is not None and margin.plan is not None and breaches_margin(margin.actual, margin.plan):
        items.append(
            _exception(
                pack,
                view,
                "gross_margin",
                "below_plan",
                "policy.margin_shortfall",
                abs(margin.actual - margin.plan),
                comparison_fact=f"{view.slice_id}.gross_margin.var_plan_bps_signed",
            )
        )
    revenue = view.levels["revenue"]
    if (
        revenue.actual is not None
        and revenue.plan is not None
        and breaches_revenue(revenue.actual, revenue.plan)
    ):
        gap = abs((revenue.actual - revenue.plan) / revenue.plan) if revenue.plan else 0.0
        items.append(
            _exception(
                pack,
                view,
                "revenue",
                "below_plan",
                "policy.revenue_shortfall",
                gap,
                comparison_fact=f"{view.slice_id}.revenue.var_plan_pct_signed",
            )
        )
    expedite = view.levels["expedite_cost"]
    if (
        expedite.actual is not None
        and expedite.plan is not None
        and breaches_expedite(expedite.actual, expedite.plan)
    ):
        gap = abs((expedite.actual - expedite.plan) / expedite.plan) if expedite.plan else 0.0
        items.append(
            _exception(
                pack,
                view,
                "expedite_cost",
                "above_plan",
                "policy.expedite_overrun",
                gap,
                comparison_fact=f"{view.slice_id}.expedite_cost.var_plan_pct_signed",
            )
        )
    return items


def _exception(
    pack: KpiPack,
    view: SliceView,
    metric: str,
    rule: str,
    bar_fact: str,
    severity: float,
    comparison_fact: str | None = None,
) -> ExceptionItem:
    actual_fact = f"{view.slice_id}.{metric}.actual"
    return ExceptionItem(
        exception_id=f"exc.{view.slice_id}.{metric}.{rule}",
        slice_id=view.slice_id,
        scope=view.scope,
        label=view.label,
        metric=metric,
        rule=rule,
        actual_fact=actual_fact,
        comparison_fact=comparison_fact or actual_fact,
        bar_fact=bar_fact,
        note_ids=tuple(note.note_id for note in _matching_notes(pack, view, metric)),
        severity=severity,
    )


def _matching_notes(pack: KpiPack, view: SliceView, metric: str):
    topic = METRIC_TOPIC[metric]
    matched = []
    for note in pack.notes:
        if note.period != pack.period or note.topic != topic:
            continue
        if view.scope == "network" and note.facility is None and note.family is None:
            matched.append(note)
        elif view.scope == "facility" and note.facility == view.facility and note.family is None:
            matched.append(note)
        elif view.scope == "family" and note.family == view.family and note.facility is None:
            matched.append(note)
    return matched


def _drills(
    views: dict[str, SliceView],
    material: tuple[MaterialVariance, ...],
    facts: dict[str, Fact],
) -> tuple[Drill, ...]:
    cells = [view for view in views.values() if view.scope == "cell"]
    drills: list[Drill] = []
    parents = {item.slice_id + "|" + item.metric: item for item in material}
    # Also allow a drill under a parent that is itself material.
    for item in material:
        parent = views[item.slice_id]
        delta = _plan_delta(parent, item.metric)
        if delta is None or delta == 0:
            continue
        best: tuple[float, SliceView] | None = None
        for cell in cells:
            if not _cell_under(parent, cell):
                continue
            cell_delta = _plan_delta(cell, item.metric)
            if cell_delta is None:
                continue
            share = cell_delta / delta
            if share > 0 and (best is None or share > best[0]):
                best = (share, cell)
        if best is None:
            continue
        share, cell = best
        shown_share = displayed_percent(share)
        if shown_share < displayed_percent(DRILL_SHARE) or shown_share > displayed_percent(DRILL_SHARE_CAP):
            continue
        fact_id = f"{cell.slice_id}.{item.metric}.share_of.{parent.slice_id}.var_plan"
        facts[fact_id] = Fact(fact_id, share, format_percent(share))
        drills.append(
            Drill(
                parent_slice=parent.slice_id,
                cell_slice=cell.slice_id,
                cell_label=cell.label,
                metric=item.metric,
                share_fact=fact_id,
            )
        )
    del parents
    return tuple(drills)


def _plan_delta(view: SliceView, metric: str) -> float | None:
    level = view.levels[metric]
    if level.actual is None or level.plan is None:
        return None
    return level.actual - level.plan


def _cell_under(parent: SliceView, cell: SliceView) -> bool:
    if parent.scope == "network":
        return True
    if parent.scope == "facility":
        return cell.facility == parent.facility
    if parent.scope == "family":
        return cell.family == parent.family
    return False


def _slice_id(scope: str, facility: str | None, family: str | None) -> str:
    if scope == "network":
        return "network"
    if scope == "facility":
        return f"facility.{facility}"
    if scope == "family":
        return f"family.{family}"
    return f"cell.{facility}.{family}"


def _preferred(values: list[str], preferred: tuple[str, ...]) -> list[str]:
    present = set(values)
    ordered = [item for item in preferred if item in present]
    ordered.extend(sorted(item for item in present if item not in ordered))
    return ordered
