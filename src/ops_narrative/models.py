"""KPI pack model.

A pack stores additive inputs at the node-by-category grain. Rates, profit,
days of supply, and every rollup are computed later so a stored ratio cannot
disagree with the inputs underneath it.
"""

from __future__ import annotations

from dataclasses import dataclass

ADDITIVE_METRICS: tuple[str, ...] = (
    "revenue",
    "cogs",
    "inventory",
    "units",
    "units_forecast",
    "abs_unit_error",
    "units_ordered",
    "units_otif",
    "lines_ordered",
    "lines_filled",
    "expedite_cost",
)

MONEY_METRICS: frozenset[str] = frozenset({"revenue", "cogs", "inventory", "expedite_cost"})
COUNT_METRICS: frozenset[str] = frozenset(
    {
        "units",
        "units_forecast",
        "abs_unit_error",
        "units_ordered",
        "units_otif",
        "lines_ordered",
        "lines_filled",
    }
)

BASELINE_KEYS: tuple[str, ...] = ("actual", "plan", "prior_period", "prior_year")


@dataclass(frozen=True)
class Measure:
    actual: float
    plan: float
    prior_period: float | None = None
    prior_year: float | None = None

    def value(self, key: str) -> float | None:
        if key not in BASELINE_KEYS:
            raise KeyError(key)
        return getattr(self, key)


@dataclass(frozen=True)
class Cell:
    facility: str
    family: str
    measures: dict[str, Measure]


@dataclass(frozen=True)
class OperatingNote:
    note_id: str
    period: str
    facility: str | None
    family: str | None
    topic: str
    text: str


@dataclass(frozen=True)
class KpiPack:
    schema_version: str
    fictional: bool
    entity_name: str
    entity_disclaimer: str
    currency: str
    period: str
    days_in_period: int
    seed: int
    generator_version: str
    cells: tuple[Cell, ...]
    notes: tuple[OperatingNote, ...]

    def cell_id(self, cell: Cell) -> str:
        return f"cell.{cell.facility}.{cell.family}"
