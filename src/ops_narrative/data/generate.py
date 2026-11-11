"""Deterministic synthetic packs for a fictional wholesaler.

Plan values are the operating plan, including a seasonal shape. Actuals
move off that plan only by a small seeded noise term and by the shocks
below. A shock may carry an operating note. The note is context the
narrative is allowed to quote. It is not a calculated bridge.

History starts a year before the first sample month so every sample pack
has a prior-year baseline that was generated, not typed in.
"""

from __future__ import annotations

import calendar
import hashlib
from dataclasses import dataclass

from ops_narrative.data.store import validate_pack
from ops_narrative.identity import (
    CURRENCY,
    DEFAULT_SEED,
    ENTITY_DISCLAIMER,
    ENTITY_NAME,
    FACILITIES,
    FAMILIES,
    GENERATOR_VERSION,
    HISTORY_END,
    HISTORY_START,
    SAMPLE_PERIODS,
    SCHEMA_VERSION,
)
from ops_narrative.models import ADDITIVE_METRICS, Cell, KpiPack, Measure, OperatingNote

MONTHLY_BASE = 45_000_000.0
SEASON: dict[int, float] = {
    1: 0.94,
    2: 0.93,
    3: 0.98,
    4: 0.99,
    5: 1.00,
    6: 1.02,
    7: 1.01,
    8: 1.02,
    9: 1.04,
    10: 1.06,
    11: 1.12,
    12: 1.16,
}
FACILITY_SHARE: dict[str, float] = {
    "brindle": 0.24,
    "redkiln": 0.28,
    "osier": 0.26,
    "lowwharf": 0.22,
}
FAMILY_SHARE: dict[str, float] = {
    "staples": 0.48,
    "homecare": 0.31,
    "personal": 0.21,
}
FAMILY_MARGIN: dict[str, float] = {
    "staples": 0.22,
    "homecare": 0.28,
    "personal": 0.35,
}
UNIT_PRICE: dict[str, float] = {
    "staples": 8.0,
    "homecare": 14.0,
    "personal": 22.0,
}

PLAN_DOS = 40.0
PLAN_OTIF = 0.972
PLAN_WAPE = 0.12
PLAN_FILL = 0.985
PLAN_EXPEDITE_RATE = 0.0035
UNITS_PER_LINE = 24.0


@dataclass(frozen=True)
class Shock:
    period: str
    facility: str | None = None
    family: str | None = None
    revenue_factor: float = 1.0
    cogs_factor: float = 1.0
    otif_factor: float = 1.0
    expedite_factor: float = 1.0
    inventory_factor: float = 1.0
    forecast_error_factor: float = 1.0
    topic: str = "operations"
    note_id: str | None = None
    note: str | None = None


# Shocks are part of the synthetic design, not observations from a real network.
SHOCKS: tuple[Shock, ...] = (
    Shock(
        period="2025-11",
        family="personal",
        forecast_error_factor=2.1,
        topic="forecast",
        note_id="note.personal.holiday-bias",
        note=(
            "Personal care shipments in this fictional November lagged the demand plan. "
            "The note records the gap. It names no customer and no promotion."
        ),
    ),
    Shock(
        period="2025-12",
        revenue_factor=1.025,
        topic="commercial",
    ),
    Shock(
        period="2026-01",
        facility="lowwharf",
        otif_factor=0.93,
        expedite_factor=2.4,
        topic="service",
        note_id="note.lowwharf.sorter",
        note=(
            "Lowwharf node recorded a two-day sorter outage in week 3. "
            "Orders were re-waved inside the month. The note does not quantify lost sales."
        ),
    ),
    Shock(
        period="2026-02",
        facility="osier",
        inventory_factor=1.22,
        topic="inventory",
        note_id="note.osier.pullin-feb",
        note=(
            "Osier node received an early purchase-order pull-in. "
            "The note records the pull-in. It does not record a demand change."
        ),
    ),
    Shock(
        period="2026-03",
        cogs_factor=0.992,
        topic="commercial",
    ),
    Shock(
        period="2026-03",
        facility="redkiln",
        otif_factor=0.94,
        expedite_factor=1.8,
        topic="service",
        note_id="note.redkiln.inbound",
        note=(
            "Redkiln node logged late inbounds on two staples lanes during week 3. "
            "The note records dwell and a re-wave. It does not record cancellations or a customer concession."
        ),
    ),
    Shock(
        period="2026-03",
        facility="redkiln",
        family="staples",
        revenue_factor=0.93,
        topic="commercial",
    ),
    Shock(
        period="2026-03",
        family="personal",
        forecast_error_factor=3.0,
        topic="forecast",
    ),
    Shock(
        period="2026-03",
        facility="osier",
        inventory_factor=1.30,
        topic="inventory",
        note_id="note.osier.pullin-mar",
        note=(
            "Osier node again received an early purchase-order pull-in. "
            "The note records the pull-in. It is not a write-down proposal."
        ),
    ),
)


def iter_periods(start: str, end: str) -> list[str]:
    year, month = (int(part) for part in start.split("-"))
    end_year, end_month = (int(part) for part in end.split("-"))
    periods: list[str] = []
    while (year, month) <= (end_year, end_month):
        periods.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return periods


def shift_period(period: str, months: int) -> str:
    year, month = (int(part) for part in period.split("-"))
    index = year * 12 + (month - 1) + months
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def days_in_period(period: str) -> int:
    year, month = (int(part) for part in period.split("-"))
    return calendar.monthrange(year, month)[1]


def generate_history(
    *,
    seed: int = DEFAULT_SEED,
    start: str = HISTORY_START,
    end: str = HISTORY_END,
) -> dict[tuple[str, str, str], dict[str, tuple[float, float]]]:
    """Return ``(period, facility, family) -> metric -> (actual, plan)``."""
    history: dict[tuple[str, str, str], dict[str, tuple[float, float]]] = {}
    for period in iter_periods(start, end):
        for facility in FACILITIES:
            for family in FAMILIES:
                history[(period, facility, family)] = _leaf(period, facility, family, seed)
    return history


def generate_pack(
    period: str,
    *,
    seed: int = DEFAULT_SEED,
    history: dict[tuple[str, str, str], dict[str, tuple[float, float]]] | None = None,
) -> KpiPack:
    if period not in SAMPLE_PERIODS and history is None:
        raise ValueError(
            f"{period} is outside the sample window. Pass a history if you need another month."
        )
    built = history if history is not None else generate_history(seed=seed)
    prior_key = shift_period(period, -1)
    py_key = shift_period(period, -12)
    cells: list[Cell] = []
    for facility in FACILITIES:
        for family in FAMILIES:
            current = built[(period, facility, family)]
            prior = built.get((prior_key, facility, family))
            previous_year = built.get((py_key, facility, family))
            measures: dict[str, Measure] = {}
            for name in ADDITIVE_METRICS:
                actual, plan = current[name]
                measures[name] = Measure(
                    actual=actual,
                    plan=plan,
                    prior_period=None if prior is None else prior[name][0],
                    prior_year=None if previous_year is None else previous_year[name][0],
                )
            cells.append(Cell(facility=facility, family=family, measures=measures))
    pack = KpiPack(
        schema_version=SCHEMA_VERSION,
        fictional=True,
        entity_name=ENTITY_NAME,
        entity_disclaimer=ENTITY_DISCLAIMER,
        currency=CURRENCY,
        period=period,
        days_in_period=days_in_period(period),
        seed=seed,
        generator_version=GENERATOR_VERSION,
        cells=tuple(cells),
        notes=tuple(_notes_for(period)),
    )
    validate_pack(pack, full_grid=True)
    return pack


def generate_sample_packs(seed: int = DEFAULT_SEED) -> list[KpiPack]:
    history = generate_history(seed=seed)
    return [generate_pack(period, seed=seed, history=history) for period in SAMPLE_PERIODS]


def _notes_for(period: str) -> list[OperatingNote]:
    notes: list[OperatingNote] = []
    seen: set[str] = set()
    for shock in SHOCKS:
        if shock.period != period or not shock.note or not shock.note_id or shock.note_id in seen:
            continue
        seen.add(shock.note_id)
        notes.append(
            OperatingNote(
                note_id=shock.note_id,
                period=period,
                facility=shock.facility,
                family=shock.family,
                topic=shock.topic,
                text=shock.note,
            )
        )
    return notes


def _leaf(period: str, facility: str, family: str, seed: int) -> dict[str, tuple[float, float]]:
    year, month = (int(part) for part in period.split("-"))
    days = calendar.monthrange(year, month)[1]
    shocks = [
        shock
        for shock in SHOCKS
        if shock.period == period
        and (shock.facility is None or shock.facility == facility)
        and (shock.family is None or shock.family == family)
    ]
    revenue_factor = _product(shock.revenue_factor for shock in shocks)
    cogs_factor = _product(shock.cogs_factor for shock in shocks)
    otif_factor = _product(shock.otif_factor for shock in shocks)
    expedite_factor = _product(shock.expedite_factor for shock in shocks)
    inventory_factor = _product(shock.inventory_factor for shock in shocks)
    forecast_factor = _product(shock.forecast_error_factor for shock in shocks)

    revenue_plan = round(
        MONTHLY_BASE * SEASON[month] * FACILITY_SHARE[facility] * FAMILY_SHARE[family],
        2,
    )
    revenue_actual = round(
        revenue_plan * revenue_factor * _amp(seed, period, facility, family, "revenue", amplitude=0.004),
        2,
    )
    margin = FAMILY_MARGIN[family]
    cogs_plan = round(revenue_plan * (1.0 - margin), 2)
    cogs_actual = round(
        revenue_actual
        * (1.0 - margin)
        * cogs_factor
        * _amp(seed, period, facility, family, "cogs", amplitude=0.002),
        2,
    )
    inventory_plan = round(PLAN_DOS * (cogs_plan / days), 2)
    inventory_scale = 1.0 if cogs_plan == 0 else cogs_actual / cogs_plan
    inventory_actual = round(
        inventory_plan
        * inventory_scale
        * inventory_factor
        * _amp(seed, period, facility, family, "inventory", amplitude=0.01),
        2,
    )

    price = UNIT_PRICE[family]
    units_plan = max(1, round(revenue_plan / price))
    units_actual = max(1, round(revenue_actual / price))
    error_plan = max(0, round(units_plan * PLAN_WAPE))
    error_rate = PLAN_WAPE * forecast_factor * _amp(
        seed, period, facility, family, "forecast", amplitude=0.05
    )
    error_actual = min(int(units_actual * 0.95), max(0, round(units_actual * error_rate)))
    forecast_plan = units_plan + error_plan
    forecast_actual = units_actual + error_actual

    ordered_plan = max(1, round(units_plan * 1.01))
    ordered_actual = max(1, round(units_actual * 1.01))
    rate_actual = min(
        1.0,
        max(0.0, PLAN_OTIF * otif_factor + (_signed_unit(seed, period, facility, family, "otif") * 0.003)),
    )
    otif_plan_units = min(ordered_plan, max(0, round(PLAN_OTIF * ordered_plan)))
    otif_actual_units = min(ordered_actual, max(0, round(rate_actual * ordered_actual)))

    lines_plan = max(1, round(ordered_plan / UNITS_PER_LINE))
    lines_actual = max(1, round(ordered_actual / UNITS_PER_LINE))
    fill_rate = min(
        1.0,
        max(0.0, PLAN_FILL + (_signed_unit(seed, period, facility, family, "fill") * 0.002)),
    )
    filled_plan = min(lines_plan, max(0, round(PLAN_FILL * lines_plan)))
    filled_actual = min(lines_actual, max(0, round(fill_rate * lines_actual)))

    expedite_plan = round(revenue_plan * PLAN_EXPEDITE_RATE, 2)
    expedite_actual = round(
        revenue_actual
        * PLAN_EXPEDITE_RATE
        * expedite_factor
        * _amp(seed, period, facility, family, "expedite", amplitude=0.02),
        2,
    )

    pairs = {
        "revenue": (float(revenue_actual), float(revenue_plan)),
        "cogs": (float(cogs_actual), float(cogs_plan)),
        "inventory": (float(inventory_actual), float(inventory_plan)),
        "units": (float(units_actual), float(units_plan)),
        "units_forecast": (float(forecast_actual), float(forecast_plan)),
        "abs_unit_error": (float(error_actual), float(error_plan)),
        "units_ordered": (float(ordered_actual), float(ordered_plan)),
        "units_otif": (float(otif_actual_units), float(otif_plan_units)),
        "lines_ordered": (float(lines_actual), float(lines_plan)),
        "lines_filled": (float(filled_actual), float(filled_plan)),
        "expedite_cost": (float(expedite_actual), float(expedite_plan)),
    }
    return pairs


def _product(values) -> float:
    total = 1.0
    for value in values:
        total *= value
    return total


def _unit(*parts: object) -> float:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _signed_unit(*parts: object) -> float:
    return _unit(*parts) * 2.0 - 1.0


def _amp(*parts: object, amplitude: float) -> float:
    return 1.0 + _signed_unit(*parts) * amplitude
