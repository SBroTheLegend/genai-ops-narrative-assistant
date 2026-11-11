"""Synthetic history is deterministic, fictional, and internally tied."""

from __future__ import annotations

import re

from ops_narrative.data.generate import (
    FACILITY_SHARE,
    FAMILY_SHARE,
    generate_history,
    generate_pack,
    generate_sample_packs,
)
from ops_narrative.data.store import pack_to_dict
from ops_narrative.identity import DEFAULT_SEED, FACILITIES, FAMILIES, HERO_PERIOD

_CONTACT = re.compile(r"https?://|www\.|@", re.IGNORECASE)
_PHONE = re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")


def test_sample_pack_is_a_full_fictional_grid():
    pack = generate_pack(HERO_PERIOD, seed=DEFAULT_SEED)
    assert pack.fictional is True
    assert "fictional" in pack.entity_disclaimer.lower()
    assert len(pack.cells) == len(FACILITIES) * len(FAMILIES)
    assert abs(sum(FACILITY_SHARE.values()) - 1) < 1e-9
    assert abs(sum(FAMILY_SHARE.values()) - 1) < 1e-9
    blob = pack.entity_disclaimer + " ".join(note.text for note in pack.notes)
    assert _CONTACT.search(blob) is None
    assert _PHONE.search(blob) is None


def test_generation_is_deterministic_and_seeded():
    first = pack_to_dict(generate_pack(HERO_PERIOD, seed=DEFAULT_SEED))
    second = pack_to_dict(generate_pack(HERO_PERIOD, seed=DEFAULT_SEED))
    other = pack_to_dict(generate_pack(HERO_PERIOD, seed=DEFAULT_SEED + 1))
    assert first == second
    assert first["cells"][0]["measures"]["revenue"]["actual"] != other["cells"][0]["measures"]["revenue"]["actual"]


def test_prior_period_is_the_prior_month_actual():
    history = generate_history(seed=DEFAULT_SEED)
    march = generate_pack(HERO_PERIOD, seed=DEFAULT_SEED, history=history)
    february = generate_pack("2026-02", seed=DEFAULT_SEED, history=history)
    march_cell = march.cells[0]
    february_cell = next(
        cell
        for cell in february.cells
        if cell.facility == march_cell.facility and cell.family == march_cell.family
    )
    assert march_cell.measures["revenue"].prior_period == february_cell.measures["revenue"].actual
    assert march_cell.measures["revenue"].prior_year is not None


def test_every_sample_period_loads():
    packs = generate_sample_packs(seed=DEFAULT_SEED)
    assert [pack.period for pack in packs] == [
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
    ]
