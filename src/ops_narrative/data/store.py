"""Read and write KPI packs.

The JSON file is the contract a reviewer can open without the narrator.
Rollups are not stored. If a rate ever appears in a file, the loader rejects
the pack rather than letting it disagree with the additive inputs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ops_narrative.errors import PackValidationError
from ops_narrative.identity import FACILITIES, FAMILIES
from ops_narrative.models import (
    ADDITIVE_METRICS,
    BASELINE_KEYS,
    Cell,
    KpiPack,
    Measure,
    OperatingNote,
)

_CONTACT_RE = re.compile(r"https?://|www\.|@", re.IGNORECASE)
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b")


def validate_pack(pack: KpiPack, *, full_grid: bool = False) -> None:
    if pack.fictional is not True:
        raise PackValidationError("Pack must be marked fictional.")
    if not pack.entity_name.strip():
        raise PackValidationError("Pack is missing an entity name.")
    if not pack.entity_disclaimer.strip():
        raise PackValidationError("Pack is missing a fictional-data disclaimer.")
    if pack.days_in_period < 28 or pack.days_in_period > 31:
        raise PackValidationError("days_in_period must be a calendar month.")
    if not pack.cells:
        raise PackValidationError("Pack has no cells.")

    seen: set[tuple[str, str]] = set()
    for cell in pack.cells:
        key = (cell.facility, cell.family)
        if key in seen:
            raise PackValidationError(f"Duplicate cell {cell.facility}/{cell.family}.")
        seen.add(key)
        missing = set(ADDITIVE_METRICS) - set(cell.measures)
        extra = set(cell.measures) - set(ADDITIVE_METRICS)
        if missing or extra:
            raise PackValidationError(
                f"Cell {cell.facility}/{cell.family} has measures missing={sorted(missing)} extra={sorted(extra)}."
            )
        for name, measure in cell.measures.items():
            for baseline in ("actual", "plan"):
                value = measure.value(baseline)
                if value is None or value < 0:
                    raise PackValidationError(f"{name}.{baseline} must be zero or positive.")
            for baseline in ("prior_period", "prior_year"):
                value = measure.value(baseline)
                if value is not None and value < 0:
                    raise PackValidationError(f"{name}.{baseline} must be zero or positive when present.")
        _check_bounds(cell, "actual")
        _check_bounds(cell, "plan")

    if full_grid:
        for facility in FACILITIES:
            for family in FAMILIES:
                if (facility, family) not in seen:
                    raise PackValidationError(f"Full grid is missing {facility}/{family}.")

    texts = [pack.entity_name, pack.entity_disclaimer]
    note_ids: set[str] = set()
    for note in pack.notes:
        if note.note_id in note_ids:
            raise PackValidationError(f"Duplicate note id {note.note_id}.")
        note_ids.add(note.note_id)
        if note.period != pack.period:
            raise PackValidationError(f"Note {note.note_id} is not in the pack period.")
        texts.extend((note.note_id, note.text, note.topic))
    for text in texts:
        if _CONTACT_RE.search(text) or _PHONE_RE.search(text):
            raise PackValidationError(
                "Pack text contains a link, email, or phone pattern. Sample data does not carry those."
            )


def _check_bounds(cell: Cell, baseline: str) -> None:
    measures = cell.measures
    ordered = measures["units_ordered"].value(baseline)
    otif = measures["units_otif"].value(baseline)
    lines = measures["lines_ordered"].value(baseline)
    filled = measures["lines_filled"].value(baseline)
    if ordered is None or otif is None or lines is None or filled is None:
        return
    if otif - ordered > 1e-6:
        raise PackValidationError(
            f"{cell.facility}/{cell.family} {baseline} OTIF units exceed units ordered."
        )
    if filled - lines > 1e-6:
        raise PackValidationError(
            f"{cell.facility}/{cell.family} {baseline} filled lines exceed lines ordered."
        )


def pack_to_dict(pack: KpiPack) -> dict:
    cells = []
    for cell in pack.cells:
        measures = {}
        for name in ADDITIVE_METRICS:
            measure = cell.measures[name]
            measures[name] = {key: measure.value(key) for key in BASELINE_KEYS}
        cells.append(
            {
                "facility": cell.facility,
                "family": cell.family,
                "measures": measures,
            }
        )
    notes = [
        {
            "note_id": note.note_id,
            "period": note.period,
            "facility": note.facility,
            "family": note.family,
            "topic": note.topic,
            "text": note.text,
        }
        for note in pack.notes
    ]
    return {
        "schema_version": pack.schema_version,
        "fictional": pack.fictional,
        "entity_name": pack.entity_name,
        "entity_disclaimer": pack.entity_disclaimer,
        "currency": pack.currency,
        "period": pack.period,
        "days_in_period": pack.days_in_period,
        "seed": pack.seed,
        "generator_version": pack.generator_version,
        "cells": cells,
        "notes": notes,
    }


def pack_from_dict(payload: dict) -> KpiPack:
    try:
        cells = []
        for raw in payload["cells"]:
            measures = {}
            for name in ADDITIVE_METRICS:
                raw_measure = raw["measures"][name]
                measures[name] = Measure(
                    actual=float(raw_measure["actual"]),
                    plan=float(raw_measure["plan"]),
                    prior_period=_optional_float(raw_measure.get("prior_period")),
                    prior_year=_optional_float(raw_measure.get("prior_year")),
                )
            cells.append(Cell(facility=raw["facility"], family=raw["family"], measures=measures))
        notes = tuple(
            OperatingNote(
                note_id=raw["note_id"],
                period=raw["period"],
                facility=raw.get("facility"),
                family=raw.get("family"),
                topic=raw["topic"],
                text=raw["text"],
            )
            for raw in payload.get("notes", [])
        )
        pack = KpiPack(
            schema_version=str(payload["schema_version"]),
            fictional=bool(payload["fictional"]),
            entity_name=str(payload["entity_name"]),
            entity_disclaimer=str(payload["entity_disclaimer"]),
            currency=str(payload["currency"]),
            period=str(payload["period"]),
            days_in_period=int(payload["days_in_period"]),
            seed=int(payload["seed"]),
            generator_version=str(payload["generator_version"]),
            cells=tuple(cells),
            notes=notes,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PackValidationError(f"Pack JSON is not a valid KPI pack: {exc}") from exc
    validate_pack(pack)
    return pack


def dump_pack(pack: KpiPack, path: Path) -> None:
    validate_pack(pack)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pack_to_dict(pack), indent=2) + "\n", encoding="utf-8")


def load_pack(path: Path) -> KpiPack:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PackValidationError("Pack JSON must be an object.")
    return pack_from_dict(payload)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)  # type: ignore[arg-type]
