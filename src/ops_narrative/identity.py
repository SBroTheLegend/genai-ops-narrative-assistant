"""Fictional sample entity used by the synthetic packs.

Nothing in this module refers to a real company, site, customer, or person.
"""

from __future__ import annotations

ENTITY_NAME = "Calderwisp Wholesale"
ENTITY_DISCLAIMER = (
    "Calderwisp Wholesale is a fictional wholesaler created for this portfolio sample. "
    "Nodes, categories, operating notes, and figures are synthetic. They do not describe "
    "a real business, person, customer, or site."
)
CURRENCY = "USD"

FACILITIES: tuple[str, ...] = ("brindle", "redkiln", "osier", "lowwharf")
FACILITY_LABELS: dict[str, str] = {
    "brindle": "Brindle node",
    "redkiln": "Redkiln node",
    "osier": "Osier node",
    "lowwharf": "Lowwharf node",
}

FAMILIES: tuple[str, ...] = ("staples", "homecare", "personal")
FAMILY_LABELS: dict[str, str] = {
    "staples": "Staples",
    "homecare": "Home care",
    "personal": "Personal care",
}

HERO_PERIOD = "2026-03"
SAMPLE_PERIODS: tuple[str, ...] = (
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
)
HISTORY_START = "2024-10"
HISTORY_END = "2026-03"
DEFAULT_SEED = 20260311
GENERATOR_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


def facility_label(facility: str) -> str:
    return FACILITY_LABELS.get(facility, facility)


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(family, family)


def slice_label(scope: str, facility: str | None, family: str | None) -> str:
    if scope == "network":
        return "Network"
    if scope == "facility":
        return facility_label(facility or "")
    if scope == "family":
        return family_label(family or "")
    return f"{family_label(family or '')} at {facility_label(facility or '')}"
