"""Briefs stay inside the fact sheet, and the gate notices when they do not."""

from __future__ import annotations

from ops_narrative.data.generate import generate_pack
from ops_narrative.identity import DEFAULT_SEED, HERO_PERIOD
from ops_narrative.narrative.claims import BANNED_PHRASES
from ops_narrative.narrative.compose import compose
from ops_narrative.narrative.prompts import PROMPTS
from ops_narrative.narrative.templates import SPECS, active_template
from ops_narrative.review.faithfulness import review_markdown
from tests.conftest import make_cell, make_pack


def _hero():
    return generate_pack(HERO_PERIOD, seed=DEFAULT_SEED)


def test_active_templates_have_prompts_and_one_active_per_kind():
    ids = {spec.template_id for spec in SPECS}
    assert set(PROMPTS) == ids
    assert active_template("month-end").template_id == "month_end.v1.0.0"
    for prompt in PROMPTS.values():
        lowered = prompt.lower()
        assert "do not add" in lowered
        assert "number" in lowered


def test_hero_briefs_pass_their_own_gates():
    pack = _hero()
    for kind in ("month-end", "variance", "exceptions"):
        text = compose(pack, kind=kind)
        report = review_markdown(text, pack)
        assert report.passed, report.findings[:8]
        assert report.faithfulness_score == 1
        assert "fictional" in text.lower()
        for phrase in BANNED_PHRASES:
            assert phrase not in text.lower()


def test_retired_scorecard_is_a_different_contract():
    pack = _hero()
    current = compose(pack, template_id="month_end.v1.0.0")
    retired = compose(pack, template_id="month_end.v0.9.0")
    assert current != retired
    assert review_markdown(retired, pack).passed
    judged_as_current = review_markdown(retired, pack, template_id="month_end.v1.0.0")
    assert not judged_as_current.passed
    assert any(item.startswith("exc.") for item in judged_as_current.missing)


def test_hero_month_names_concentrated_breaches_and_not_every_echo():
    pack = _hero()
    sheet = __import__("ops_narrative.metrics.engine", fromlist=["build_sheet"]).build_sheet(pack)
    ids = {item.variance_id for item in sheet.material}
    assert "mat.facility.redkiln.otif.plan" in ids
    assert "mat.facility.redkiln.revenue.plan" in ids
    assert "mat.family.personal.forecast_accuracy.plan" in ids
    assert "mat.facility.osier.dos.plan" in ids
    assert "mat.network.gross_margin.plan" in ids
    assert "mat.network.revenue.plan" not in ids
    assert "mat.facility.brindle.gross_margin.plan" not in ids
    assert "gross_margin" in sheet.broad_metrics
    assert len(sheet.material) < 16
    text = compose(pack, kind="month-end")
    assert "sits inside the materiality bar" in text
    assert "Network Net revenue" not in text
    assert "104." not in text
    assert "The move shows up across nodes and categories." in text


def test_month_end_states_the_seasonality_rule_and_quotes_only_its_notes():
    pack = _hero()
    text = compose(pack, kind="month-end")
    assert "The plan already carries the seasonal shape" in text
    assert "week 3" in text
    assert "holiday" not in text.lower()
    assert "sorter" not in text.lower()
    assert "A cause is not assigned." in text
    assert "Recorded context only." in text


def test_direction_language_has_to_match_the_sign():
    pack = make_pack([make_cell("north", "alpha", revenue=(900.0, 1_000.0, 950.0, 1_100.0))])
    text = compose(pack, kind="month-end")
    report = review_markdown(text, pack)
    assert report.passed, report.findings[:6]
    assert "below plan" in text
    flipped = text.replace(" below plan", " above plan", 1)
    failed = review_markdown(flipped, pack)
    assert not failed.direction_ok
    assert any(item.code == "direction" for item in failed.findings)


def test_uncited_numeral_and_wrong_citation_fail():
    pack = _hero()
    text = compose(pack, kind="month-end")
    dirty = text + "\n\nAn uncited upside of 123.4% was assumed for the close.\n"
    uncited = review_markdown(dirty, pack)
    assert uncited.ungrounded_count > 0
    assert not uncited.faithful
    mismatched = text.replace("](cite:", "ZZ](cite:", 1)
    # The replacement above corrupts the link. Change the visible token instead.
    start = text.find("[")
    end = text.find("]", start)
    forged = text[: start + 1] + "999.9%" + text[end:]
    forged_report = review_markdown(forged, pack)
    assert forged_report.bad_citations >= 1
    del mismatched


def test_a_digit_copied_out_of_a_note_is_not_covered_by_the_quote():
    pack = _hero()
    text = compose(pack, kind="month-end")
    leaked = text + "\n\nSee week 3.\n"
    report = review_markdown(leaked, pack)
    assert report.ungrounded_count > 0


def test_causal_connector_fails_the_gate():
    pack = _hero()
    text = compose(pack, kind="variance")
    report = review_markdown(text + "\n\nThe gap opened because the plan was soft.\n", pack)
    assert not report.attribution_ok
    assert not report.passed


def test_unknown_template_is_rejected():
    pack = _hero()
    try:
        compose(pack, template_id="month_end.v9.9.9")
    except Exception as exc:
        assert "Unknown template" in str(exc)
    else:
        raise AssertionError("unknown template should fail")
