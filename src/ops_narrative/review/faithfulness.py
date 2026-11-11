"""Independent review of a brief against the pack.

The reviewer rebuilds the fact sheet and does not trust the narrator's
word that a figure was copied correctly. A cited token must equal the
canonical display of that fact. Any other numeral, outside a masked year,
template version, or full operating-note quote, is ungrounded.

Direction language is checked only where the brief uses the canonical
pattern: an absolute variance citation immediately followed by below,
above, or in line with. The sign has to match the signed sibling fact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ops_narrative.formatutil import display_sign
from ops_narrative.metrics.engine import FactSheet, build_sheet
from ops_narrative.models import KpiPack
from ops_narrative.narrative.claims import BANNED_PHRASES
from ops_narrative.narrative.templates import TemplateSpec, get_template
from ops_narrative.policy import SCORECARD_METRICS, VARIANCE_STYLE

CITE_RE = re.compile(r"\[([^\]]+)\]\(cite:([a-z0-9_.]+)\)")
HEADER_RE = re.compile(r"<!--\s*ops-narrative\b.*?-->", re.DOTALL)
VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
PERIOD_RE = re.compile(r"\b20\d{2}-\d{2}\b")
YEAR_RE = re.compile(r"\b20\d{2}\b")
TEMPLATE_RE = re.compile(r"^template:\s*(\S+)\s*$", re.MULTILINE)
DIRECTION_RE = re.compile(
    r"\(cite:([a-z0-9_.]+\.var_(?:plan|prior|py)_(?:usd|pct|pp|bps|days)_abs)\) "
    r"(below|above|in line with)"
)
_WORD_PHRASE = [phrase for phrase in BANNED_PHRASES if " " not in phrase]
_MULTI_PHRASE = [phrase for phrase in BANNED_PHRASES if " " in phrase]


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str


@dataclass(frozen=True)
class ReviewReport:
    template_id: str
    citation_count: int
    bad_citations: int
    ungrounded_count: int
    direction_failures: int
    attribution_hits: tuple[str, ...]
    missing: tuple[str, ...]
    findings: tuple[Finding, ...]

    @property
    def direction_ok(self) -> bool:
        return self.direction_failures == 0

    @property
    def attribution_ok(self) -> bool:
        return not self.attribution_hits

    @property
    def faithful(self) -> bool:
        return (
            self.citation_count > 0
            and self.bad_citations == 0
            and self.ungrounded_count == 0
            and self.direction_ok
            and self.attribution_ok
        )

    @property
    def coverage_complete(self) -> bool:
        return not self.missing

    @property
    def passed(self) -> bool:
        return self.faithful and self.coverage_complete

    @property
    def faithfulness_score(self) -> float:
        defects = self.bad_citations + self.ungrounded_count + self.direction_failures
        if self.attribution_hits:
            defects += len(self.attribution_hits)
        denom = self.citation_count + self.ungrounded_count + self.direction_failures
        if self.attribution_hits:
            denom += len(self.attribution_hits)
        if denom == 0:
            return 0.0
        return max(0.0, 1.0 - defects / denom)

    @property
    def coverage_score(self) -> float:
        if not self.missing and self.citation_count == 0:
            return 0.0
        required = self.citation_count + len(self.missing)
        if required == 0:
            return 0.0
        return 1.0 - len(self.missing) / required


def review_markdown(
    markdown: str,
    pack: KpiPack,
    *,
    template_id: str | None = None,
    sheet: FactSheet | None = None,
) -> ReviewReport:
    spec = get_template(template_id or _template_from_header(markdown))
    built = sheet or build_sheet(pack)
    findings: list[Finding] = []
    links = CITE_RE.findall(markdown)
    bad = 0
    for text, fact_id in links:
        fact = built.facts.get(fact_id)
        if fact is None:
            bad += 1
            findings.append(Finding("unknown_cite", f"{fact_id} is not on the fact sheet."))
            continue
        if text != fact.primary:
            bad += 1
            findings.append(
                Finding(
                    "cite_mismatch",
                    f"{fact_id} prints {text!r}; the canonical display is {fact.primary!r}.",
                )
            )
    ungrounded = _ungrounded_snippets(markdown, pack)
    for snippet in ungrounded:
        findings.append(Finding("ungrounded_numeral", snippet))
    direction_failures = _direction_failures(markdown, built, findings)
    hits = tuple(_attribution_hits(markdown))
    for phrase in hits:
        findings.append(Finding("causal_language", f"Banned connector {phrase!r} is in the brief."))
    missing = tuple(_missing_coverage(markdown, built, spec, {fact_id for _, fact_id in links}))
    for item in missing:
        findings.append(Finding("coverage", f"Missing required item {item}."))
    return ReviewReport(
        template_id=spec.template_id,
        citation_count=len(links),
        bad_citations=bad,
        ungrounded_count=len(ungrounded),
        direction_failures=direction_failures,
        attribution_hits=hits,
        missing=missing,
        findings=tuple(findings),
    )


def format_report(report: ReviewReport) -> str:
    status = "PASS" if report.passed else "FAIL"
    return (
        f"{status}  template {report.template_id}  "
        f"faithfulness {report.faithfulness_score:.2f}  "
        f"coverage {report.coverage_score:.2f}  "
        f"citations {report.citation_count}  "
        f"ungrounded {report.ungrounded_count}  "
        f"direction {'ok' if report.direction_ok else 'FAIL'}  "
        f"attribution {'ok' if report.attribution_ok else 'FAIL'}"
    )


def _template_from_header(markdown: str) -> str:
    match = TEMPLATE_RE.search(markdown)
    if not match:
        raise ValueError("Brief has no ops-narrative template header.")
    return match.group(1)


def _ungrounded_snippets(markdown: str, pack: KpiPack) -> list[str]:
    text = HEADER_RE.sub("«HDR»", markdown)
    for note in sorted(pack.notes, key=lambda item: len(item.text), reverse=True):
        text = text.replace(note.text, "«NOTE»")
        text = text.replace(note.note_id, "«ID»")
    text = CITE_RE.sub("«C»", text)
    text = VERSION_RE.sub("«V»", text)
    text = PERIOD_RE.sub("«P»", text)
    text = YEAR_RE.sub("«Y»", text)
    snippets: list[str] = []
    for match in re.finditer(r"\d", text):
        start = max(0, match.start() - 24)
        end = min(len(text), match.end() + 24)
        snippets.append(text[start:end].replace("\n", " "))
        if len(snippets) >= 8:
            break
    return snippets


def _direction_failures(markdown: str, sheet: FactSheet, findings: list[Finding]) -> int:
    expected = {"below": -1, "above": 1, "in line with": 0}
    failures = 0
    for fact_id, word in DIRECTION_RE.findall(markdown):
        signed_id = fact_id[: -len("_abs")] + "_signed"
        fact = sheet.facts.get(signed_id)
        if fact is None:
            failures += 1
            findings.append(Finding("direction", f"No signed sibling for {fact_id}."))
            continue
        sign = display_sign(fact.primary)
        if sign != expected[word]:
            failures += 1
            findings.append(
                Finding(
                    "direction",
                    f"{fact_id} is followed by {word!r}, but {signed_id} displays {fact.primary!r}.",
                )
            )
    return failures


def _attribution_hits(markdown: str) -> list[str]:
    lowered = markdown.lower()
    hits: list[str] = []
    for phrase in _MULTI_PHRASE:
        if phrase in lowered:
            hits.append(phrase)
    for phrase in _WORD_PHRASE:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            hits.append(phrase)
    return hits


def _missing_coverage(
    markdown: str,
    sheet: FactSheet,
    spec: TemplateSpec,
    cites: set[str],
) -> list[str]:
    missing: list[str] = []
    profile = spec.coverage
    if profile.exceptions:
        for item in sheet.exceptions:
            if item.exception_id not in markdown:
                missing.append(item.exception_id)
            for fact_id in (item.actual_fact, item.comparison_fact, item.bar_fact):
                if fact_id in sheet.facts and fact_id not in cites:
                    missing.append(fact_id)
    if profile.material_plan:
        for item in sheet.material:
            if item.signed_fact in sheet.facts and item.signed_fact not in cites:
                missing.append(item.signed_fact)
    if profile.network_scorecard:
        for metric in SCORECARD_METRICS:
            style = VARIANCE_STYLE[metric]
            for fact_id in (
                f"network.{metric}.actual",
                f"network.{metric}.plan",
                f"network.{metric}.prior_year",
                f"network.{metric}.var_plan_{style}_signed",
                f"network.{metric}.var_py_{style}_signed",
            ):
                if fact_id in sheet.facts and fact_id not in cites:
                    missing.append(fact_id)
    return missing
