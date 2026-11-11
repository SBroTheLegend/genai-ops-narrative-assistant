"""Metric engine: formulas, rollups, materiality, and exception bounds."""

from __future__ import annotations

from ops_narrative.metrics.engine import build_sheet
from ops_narrative.policy import (
    breaches_dos,
    breaches_expedite,
    breaches_margin,
    breaches_otif,
    breaches_revenue,
    materiality,
)
from tests.conftest import make_cell, make_pack


def test_margin_dos_and_rates_on_a_single_cell():
    pack = make_pack([make_cell("north", "alpha")], days=30)
    sheet = build_sheet(pack)
    network = sheet.slices["network"].levels
    assert network["gross_profit"].actual == 250
    assert network["gross_margin"].actual == 0.25
    assert network["dos"].actual == 40
    assert network["otif"].actual == 0.97
    assert network["wape"].actual == 0.10
    assert network["forecast_accuracy"].actual == 0.90
    assert network["fill_rate"].actual == 1.0


def test_ratios_are_recomputed_on_the_rollup_not_averaged():
    pack = make_pack(
        [
            make_cell(
                "north",
                "alpha",
                revenue=(100.0, 100.0, 100.0, 100.0),
                cogs=(90.0, 90.0, 90.0, 90.0),
                inventory=(1_000.0, 1_000.0, 1_000.0, 1_000.0),
                units=(100.0, 100.0, 100.0, 100.0),
                abs_unit_error=(10.0, 10.0, 10.0, 10.0),
            ),
            make_cell(
                "south",
                "beta",
                revenue=(300.0, 300.0, 300.0, 300.0),
                cogs=(150.0, 150.0, 150.0, 150.0),
                inventory=(1_000.0, 1_000.0, 1_000.0, 1_000.0),
                units=(300.0, 300.0, 300.0, 300.0),
                abs_unit_error=(90.0, 90.0, 90.0, 90.0),
            ),
        ],
        days=30,
    )
    levels = build_sheet(pack).slices["network"].levels
    assert levels["gross_margin"].actual == 0.40
    assert levels["wape"].actual == 0.25
    assert levels["forecast_accuracy"].actual == 0.75
    # Days of supply uses summed inventory and summed cost, not the mean of the node rates.
    assert levels["dos"].actual == 250
    node_average = (1_000 / (90 / 30) + 1_000 / (150 / 30)) / 2
    assert levels["dos"].actual != node_average


def test_accuracy_floors_at_zero_when_wape_exceeds_one():
    pack = make_pack(
        [make_cell("north", "alpha", units=(100.0, 100.0, 100.0, 100.0), abs_unit_error=(150.0, 10.0, 10.0, 10.0))]
    )
    accuracy = build_sheet(pack).slices["network"].levels["forecast_accuracy"].actual
    assert accuracy == 0.0


def test_zero_revenue_leaves_margin_undefined():
    pack = make_pack(
        [
            make_cell(
                "north",
                "alpha",
                revenue=(0.0, 0.0, 0.0, 0.0),
                cogs=(0.0, 0.0, 0.0, 0.0),
            )
        ]
    )
    sheet = build_sheet(pack)
    assert sheet.slices["network"].levels["gross_margin"].actual is None
    assert "network.gross_margin.actual" not in sheet.facts


def test_materiality_boundaries():
    assert materiality("revenue", 10_200_000, 10_000_000) == "relative"
    assert materiality("revenue", 10_194_000, 10_000_000) is None
    assert materiality("revenue", 101_000_000, 100_000_000) == "absolute"
    assert materiality("revenue", 102_000_000, 100_000_000) == "both"
    assert materiality("gross_margin", 0.245, 0.250) == "absolute"
    assert materiality("gross_margin", 0.2451, 0.250) is None
    assert materiality("dos", 43.0, 40.0) == "absolute"
    assert materiality("dos", 42.94, 40.0) is None


def test_exception_boundaries_use_displayed_precision():
    assert breaches_otif(0.949) is True
    assert breaches_otif(0.950) is False
    assert breaches_revenue(9_700, 10_000) is True
    assert breaches_revenue(9_710, 10_000) is False
    assert breaches_expedite(125, 100) is True
    assert breaches_expedite(124, 100) is False
    assert breaches_margin(0.245, 0.250) is True
    assert breaches_margin(0.2451, 0.250) is False
    assert breaches_dos(46.1, 40.0) is True
    assert breaches_dos(46.0, 40.0) is False


def test_otif_exception_fires_on_the_displayed_rate():
    low = make_pack([make_cell("north", "alpha", units_otif=(949.0, 972.0, 970.0, 960.0), units_ordered=(1_000.0, 1_000.0, 1_000.0, 1_000.0))])
    ok = make_pack([make_cell("north", "alpha", units_otif=(950.0, 972.0, 970.0, 960.0), units_ordered=(1_000.0, 1_000.0, 1_000.0, 1_000.0))])
    low_ids = [item.exception_id for item in build_sheet(low).exceptions]
    ok_ids = [item.exception_id for item in build_sheet(ok).exceptions]
    assert "exc.network.otif.below_standard" in low_ids
    assert "exc.network.otif.below_standard" not in ok_ids


def test_cell_grain_is_not_an_exception_scope():
    pack = make_pack(
        [
            make_cell(
                "north",
                "alpha",
                units_otif=(80.0, 97.0, 97.0, 97.0),
                units_ordered=(100.0, 100.0, 100.0, 100.0),
            ),
            make_cell(
                "north",
                "beta",
                units_otif=(970.0, 972.0, 970.0, 960.0),
                units_ordered=(1_000.0, 1_000.0, 1_000.0, 1_000.0),
            ),
        ]
    )
    sheet = build_sheet(pack)
    assert all(item.scope != "cell" for item in sheet.exceptions)
    assert "exc.network.otif.below_standard" not in {item.exception_id for item in sheet.exceptions}
    assert sheet.slices["cell.north.alpha"].levels["otif"].actual == 0.80


def test_same_direction_echoes_are_not_narrated_as_separate_stories():
    pack = make_pack(
        [
            make_cell("north", "alpha", revenue=(1_020.0, 1_000.0, 1_000.0, 1_000.0)),
            make_cell("south", "beta", revenue=(1_060.0, 1_000.0, 1_000.0, 1_000.0)),
        ]
    )
    sheet = build_sheet(pack)
    revenue_ids = {item.variance_id for item in sheet.material if item.metric == "revenue"}
    assert "mat.network.revenue.plan" in revenue_ids
    assert "mat.facility.north.revenue.plan" not in revenue_ids
    assert "mat.facility.south.revenue.plan" in revenue_ids
    assert "revenue" not in sheet.broad_metrics


def test_a_uniform_move_is_marked_broad():
    pack = make_pack(
        [
            make_cell("north", "alpha", revenue=(1_020.0, 1_000.0, 1_000.0, 1_000.0)),
            make_cell("south", "beta", revenue=(1_020.0, 1_000.0, 1_000.0, 1_000.0)),
        ]
    )
    sheet = build_sheet(pack)
    revenue_ids = {item.variance_id for item in sheet.material if item.metric == "revenue"}
    assert revenue_ids == {"mat.network.revenue.plan"}
    assert "revenue" in sheet.broad_metrics


def test_variance_sign_and_percent():
    pack = make_pack(
        [make_cell("north", "alpha", revenue=(900.0, 1_000.0, 950.0, 1_100.0))]
    )
    facts = build_sheet(pack).facts
    assert facts["network.revenue.var_plan_pct_signed"].primary == "-10.0%"
    assert facts["network.revenue.var_plan_pct_abs"].primary == "10.0%"
    assert facts["network.revenue.var_plan_usd_signed"].primary.startswith("-")
