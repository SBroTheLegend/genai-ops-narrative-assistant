"""Template registry.

A template id is the unit a run pins. The active id for a kind can move
forward. Older ids stay callable so a saved brief does not change shape
just because the default moved.
"""

from __future__ import annotations

from dataclasses import dataclass

from ops_narrative.errors import TemplateError


@dataclass(frozen=True)
class CoverageProfile:
    """What a faithful brief of this template must still mention.

    Version 0.9 is a scorecard. It does not claim to cover exceptions.
    Reviewing it against the version 1 profile fails on purpose.
    """

    exceptions: bool
    material_plan: bool
    network_scorecard: bool


@dataclass(frozen=True)
class TemplateSpec:
    template_id: str
    kind: str
    version: str
    status: str
    title: str
    summary: str
    coverage: CoverageProfile


_FULL = CoverageProfile(exceptions=True, material_plan=True, network_scorecard=True)
_VARIANCE = CoverageProfile(exceptions=False, material_plan=True, network_scorecard=False)
_EXCEPTION = CoverageProfile(exceptions=True, material_plan=False, network_scorecard=False)
_SCORECARD_ONLY = CoverageProfile(exceptions=False, material_plan=False, network_scorecard=True)

SPECS: tuple[TemplateSpec, ...] = (
    TemplateSpec(
        template_id="month_end.v1.0.0",
        kind="month_end",
        version="1.0.0",
        status="active",
        title="month-end brief",
        summary="Network scorecard, material plan variances, exception prose, and reviewer questions.",
        coverage=_FULL,
    ),
    TemplateSpec(
        template_id="month_end.v0.9.0",
        kind="month_end",
        version="0.9.0",
        status="retired",
        title="month-end scorecard",
        summary="Retired scorecard-only brief. Kept so a pinned id does not silently grow a section.",
        coverage=_SCORECARD_ONLY,
    ),
    TemplateSpec(
        template_id="variance.v1.0.0",
        kind="variance",
        version="1.0.0",
        status="active",
        title="variance commentary",
        summary="Material plan variances only. Immaterial movements are omitted, not described as flat.",
        coverage=_VARIANCE,
    ),
    TemplateSpec(
        template_id="exception.v1.0.0",
        kind="exception",
        version="1.0.0",
        status="active",
        title="exception brief",
        summary="Policy breaches, quoted notes where they exist, and an explicit gap where they do not.",
        coverage=_EXCEPTION,
    ),
)

KIND_ALIASES: dict[str, str] = {
    "month-end": "month_end",
    "month_end": "month_end",
    "variance": "variance",
    "exception": "exception",
    "exceptions": "exception",
}


def canonicalize_kind(kind: str) -> str:
    try:
        return KIND_ALIASES[kind]
    except KeyError as exc:
        known = ", ".join(sorted(set(KIND_ALIASES)))
        raise TemplateError(f"Unknown narrative kind {kind!r}. Expected one of: {known}.") from exc


def get_template(template_id: str) -> TemplateSpec:
    for spec in SPECS:
        if spec.template_id == template_id:
            return spec
    known = ", ".join(spec.template_id for spec in SPECS)
    raise TemplateError(f"Unknown template {template_id!r}. Known templates: {known}.")


def active_template(kind: str) -> TemplateSpec:
    canonical = canonicalize_kind(kind)
    matches = [spec for spec in SPECS if spec.kind == canonical and spec.status == "active"]
    if len(matches) != 1:
        raise TemplateError(f"Kind {canonical} does not have exactly one active template.")
    return matches[0]


def resolve_template(template_id: str | None, kind: str | None) -> TemplateSpec:
    if template_id:
        spec = get_template(template_id)
        if kind is not None and spec.kind != canonicalize_kind(kind):
            raise TemplateError(
                f"Template {spec.template_id} is a {spec.kind} brief, not {canonicalize_kind(kind)}."
            )
        return spec
    if kind is None:
        raise TemplateError("Provide a template id or a narrative kind.")
    return active_template(kind)
