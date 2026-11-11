"""Canonical rounding. Half-up, including on negative gaps."""

from __future__ import annotations

from ops_narrative.formatutil import (
    display_sign,
    format_bps,
    format_days,
    format_percent,
    format_pp,
    format_usd,
    rhu,
)


def test_half_up_not_bankers():
    assert rhu(1.25, 1) == rhu(1.25, 1)
    assert str(rhu(1.25, 1)) == "1.3"
    assert str(rhu(-1.25, 1)) == "-1.3"
    assert str(rhu(1.35, 1)) == "1.4"


def test_money_scales():
    assert format_usd(1_840_000) == "$1.8M"
    assert format_usd(860_000) == "$860K"
    assert format_usd(-860_000) == "-$860K"
    assert format_usd(860_000, signed=True) == "+$860K"
    assert format_usd(-860_000, signed=True) == "-$860K"
    assert format_usd(0, signed=True) == "$0"
    assert format_usd(-400, absolute=True) == "$400"
    assert format_usd(999_600) == "$1.0M"


def test_rates_and_days():
    assert format_percent(0.95) == "95.0%"
    assert format_percent(-0.018, signed=True) == "-1.8%"
    assert format_percent(0.018, signed=True) == "+1.8%"
    assert format_percent(0.018, absolute=True) == "1.8%"
    assert format_pp(-0.014) == "-1.4 pp"
    assert format_pp(0, signed=True) == "0.0 pp"
    assert format_bps(-0.004) == "-40 bps"
    assert format_bps(0.0044, signed=True) == "+44 bps"
    assert format_bps(-0.0045, absolute=True) == "45 bps"
    assert format_days(40) == "40.0 days"
    assert format_days(-1.5, signed=True) == "-1.5 days"
    assert display_sign("-$0.9M") == -1
    assert display_sign("+$0.9M") == 1
    assert display_sign("$0.0M") == 0
    assert display_sign("0 bps") == 0
