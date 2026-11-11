"""Canonical display formats.

Narratives may print a figure only through these helpers. The reviewer
accepts a cited token only when it equals the primary display of that fact.
Rounding is half-up, not banker's rounding, so a displayed 1.3 cannot hide
a value that finance would round to 1.2.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def rhu(value: float, places: int) -> Decimal:
    """Round half up to ``places`` decimal places."""
    quant = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)


def display_sign(primary: str) -> int:
    """Sign implied by a canonical signed display. Zero displays have no sign."""
    text = primary.strip()
    if text.startswith("+"):
        return 1
    if text.startswith("-"):
        return -1
    return 0


def _usd_magnitude(mag: float) -> str:
    if mag >= 999_500:
        shown = rhu(mag / 1_000_000, 1)
        return f"${shown:.1f}M"
    if mag >= 999.5:
        shown = rhu(mag / 1_000, 0)
        if shown >= 1000:
            return "$1.0M"
        return f"${int(shown)}K"
    shown = rhu(mag, 0)
    if shown >= 1000:
        return "$1K"
    return f"${int(shown)}"


def format_usd(value: float, *, signed: bool = False, absolute: bool = False) -> str:
    if absolute:
        value = abs(value)
        signed = False
    if value < 0:
        sign = -1
        mag = -value
    elif value > 0:
        sign = 1
        mag = value
    else:
        sign = 0
        mag = 0.0
    body = _usd_magnitude(mag)
    if not signed or sign == 0:
        return f"-{body}" if sign < 0 and not signed else body
    if sign > 0:
        return f"+{body}"
    return f"-{body}"


def format_percent(value: float, *, signed: bool = False, absolute: bool = False) -> str:
    """Format a ratio (0.182) as a percent with one decimal."""
    if absolute:
        value = abs(value)
        signed = False
    shown = rhu(value * 100, 1)
    if absolute:
        shown = abs(shown)
    if signed and shown > 0:
        return f"+{shown:.1f}%"
    if signed and shown == 0:
        return "0.0%"
    return f"{shown:.1f}%"


def format_pp(value: float, *, signed: bool = False, absolute: bool = False) -> str:
    """Format a ratio delta as percentage points with one decimal."""
    if absolute:
        value = abs(value)
        signed = False
    shown = rhu(value * 100, 1)
    if absolute:
        shown = abs(shown)
    if signed and shown > 0:
        return f"+{shown:.1f} pp"
    if signed and shown == 0:
        return "0.0 pp"
    return f"{shown:.1f} pp"


def format_bps(value: float, *, signed: bool = False, absolute: bool = False) -> str:
    """Format a ratio delta as integer basis points."""
    if absolute:
        value = abs(value)
        signed = False
    shown = rhu(value * 10_000, 0)
    if absolute:
        shown = abs(shown)
    if signed and shown > 0:
        return f"+{int(shown)} bps"
    if signed and shown == 0:
        return "0 bps"
    return f"{int(shown)} bps"


def format_days(value: float, *, signed: bool = False, absolute: bool = False) -> str:
    if absolute:
        value = abs(value)
        signed = False
    shown = rhu(value, 1)
    if absolute:
        shown = abs(shown)
    if signed and shown > 0:
        return f"+{shown:.1f} days"
    if signed and shown == 0:
        return "0.0 days"
    return f"{shown:.1f} days"


def format_count(value: float) -> str:
    shown = rhu(value, 0)
    return f"{int(shown)}"
