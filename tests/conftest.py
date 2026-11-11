"""Pack fixtures small enough to calculate by hand."""

from __future__ import annotations

import pytest

from ops_narrative.models import Cell, KpiPack, Measure, OperatingNote

DEFAULTS: dict[str, tuple[float, float, float, float]] = {
    "revenue": (1_000.0, 1_000.0, 900.0, 800.0),
    "cogs": (750.0, 750.0, 680.0, 600.0),
    "inventory": (1_000.0, 1_000.0, 900.0, 800.0),
    "units": (100.0, 100.0, 90.0, 80.0),
    "units_forecast": (110.0, 112.0, 99.0, 88.0),
    "abs_unit_error": (10.0, 12.0, 9.0, 8.0),
    "units_ordered": (100.0, 100.0, 90.0, 80.0),
    "units_otif": (97.0, 97.0, 88.0, 78.0),
    "lines_ordered": (10.0, 10.0, 9.0, 8.0),
    "lines_filled": (10.0, 10.0, 9.0, 8.0),
    "expedite_cost": (5.0, 5.0, 4.0, 4.0),
}


def make_cell(facility: str, family: str, **overrides: tuple[float, float, float, float]) -> Cell:
    measures: dict[str, Measure] = {}
    for name, default in DEFAULTS.items():
        actual, plan, prior, prior_year = overrides.get(name, default)
        measures[name] = Measure(actual, plan, prior, prior_year)
    return Cell(facility=facility, family=family, measures=measures)


def make_pack(
    cells: list[Cell],
    *,
    period: str = "2026-03",
    days: int = 30,
    notes: tuple[OperatingNote, ...] = (),
) -> KpiPack:
    return KpiPack(
        schema_version="1.0.0",
        fictional=True,
        entity_name="Fixture Wholesale",
        entity_disclaimer="Fixture data for tests. Fictional. Not a real business.",
        currency="USD",
        period=period,
        days_in_period=days,
        seed=1,
        generator_version="test",
        cells=tuple(cells),
        notes=notes,
    )


@pytest.fixture
def two_cell_pack() -> KpiPack:
    return make_pack(
        [
            make_cell("north", "alpha"),
            make_cell("south", "beta"),
        ]
    )
