"""Render a brief from a fact sheet.

Every numeral in the body is produced by FactSheet.cite. Prose around those
citations is selected from the policy result (material or not, breach or
not, note present or not). The wording does not introduce a driver.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ops_narrative.formatutil import display_sign
from ops_narrative.metrics.engine import Drill, ExceptionItem, FactSheet, build_sheet
from ops_narrative.models import KpiPack
from ops_narrative.narrative.claims import CLAIMS_BOUNDARY, count_words
from ops_narrative.narrative.templates import TemplateSpec, resolve_template
from ops_narrative.policy import (
    METRIC_LABELS,
    SCORECARD_METRICS,
    VARIANCE_STYLE,
    materiality,
    trigger_phrase,
)

_MONTHS = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

def compose(
    pack: KpiPack,
    *,
    template_id: str | None = None,
    kind: str | None = None,
    engine: str = "deterministic",
) -> str:
    spec = resolve_template(template_id, kind)
    sheet = build_sheet(pack)
    if spec.template_id == "month_end.v1.0.0":
        body = _month_end(pack, sheet, spec, engine)
    elif spec.template_id == "month_end.v0.9.0":
        body = _month_end_scorecard(pack, sheet, spec, engine)
    elif spec.template_id == "variance.v1.0.0":
        body = _variance(pack, sheet, spec, engine)
    elif spec.template_id == "exception.v1.0.0":
        body = _exceptions_brief(pack, sheet, spec, engine)
    else:
        raise AssertionError(f"Unhandled template {spec.template_id}")
    return body.rstrip() + "\n"


def stamp_engine(markdown: str, engine: str) -> str:
    updated = re.sub(r"^engine:.*$", f"engine: {engine}", markdown, count=1, flags=re.MULTILINE)
    updated = updated.replace("Engine `deterministic`", f"Engine `{engine}`", 1)
    return updated


def _month_end(pack: KpiPack, sheet: FactSheet, spec: TemplateSpec, engine: str) -> str:
    parts = [
        _header(pack, spec, engine),
        "## Headline",
        "",
        _headline(sheet),
        "",
        "## Network scorecard",
        "",
        _scorecard(sheet),
        "",
        _prior_period_note(sheet),
        "",
        "## Material plan variances",
        "",
        (
            "Rows below clear the materiality bar. A node or category that only repeats "
            "the network movement is omitted, so the table names concentration rather than every echo."
        ),
        "",
        _material_table(sheet),
        "",
        "## Commercial",
        "",
        _metric_block(sheet, "revenue"),
        "",
        "## Margin",
        "",
        (
            f"Gross profit was {sheet.cite('network.gross_profit.actual')} "
            f"on net revenue of {sheet.cite('network.revenue.actual')}."
        ),
        "",
        _metric_block(sheet, "gross_margin"),
        "",
        "No cost, price, or mix bridge was supplied. The margin movement is not attributed.",
        "",
        "## Service",
        "",
        _metric_block(sheet, "otif"),
        "",
        _metric_block(sheet, "fill_rate"),
        "",
        _metric_block(sheet, "expedite_cost"),
        "",
        "Expedite cost sits beside service. The pack contains no bridge from freight cost to OTIF, and this brief does not invent one.",
        "",
        "## Inventory",
        "",
        _metric_block(sheet, "inventory"),
        "",
        _metric_block(sheet, "dos"),
        "",
        "Days of supply is ending inventory divided by cost of goods sold per day in the period. It is not an average of the node-level days figures.",
        "",
        "## Demand plan",
        "",
        _metric_block(sheet, "forecast_accuracy"),
        "",
        (
            "Forecast accuracy is one minus WAPE. WAPE is absolute unit error divided by actual units, "
            "taken on the rollup rather than averaged across nodes or categories. "
            "Accuracy is floored at zero when WAPE exceeds one. The statistic is not extended into a new forecast."
        ),
        "",
        "## Exceptions",
        "",
        _exception_section(pack, sheet),
        "",
        "## Reviewer questions",
        "",
        _questions(sheet),
        "",
        CLAIMS_BOUNDARY.rstrip(),
        "",
    ]
    body = "\n".join(parts)
    return body + "\n" + _fact_index(body)


def _month_end_scorecard(pack: KpiPack, sheet: FactSheet, spec: TemplateSpec, engine: str) -> str:
    parts = [
        _header(pack, spec, engine),
        "## Headline",
        "",
        _headline(sheet),
        "",
        "## Network scorecard",
        "",
        _scorecard(sheet),
        "",
        "This retired template stops at the network scorecard. It does not list node exceptions.",
        "",
        CLAIMS_BOUNDARY.rstrip(),
        "",
    ]
    body = "\n".join(parts)
    return body + "\n" + _fact_index(body)


def _variance(pack: KpiPack, sheet: FactSheet, spec: TemplateSpec, engine: str) -> str:
    count = len(sheet.material)
    words = count_words(count)
    if words is None:
        count_text = sheet.cite("meta.material_count")
    else:
        count_text = words
    intro = (
        f"This variance commentary covers {count_text} material plan variances "
        "at network, node, and category. Immaterial movements are omitted. "
        "Omission is not a claim that those movements were flat."
    )
    blocks = [intro, "", _material_table(sheet), ""]
    seen: set[str] = set()
    for item in sheet.material:
        if item.metric in seen:
            continue
        seen.add(item.metric)
        blocks.extend([f"### {METRIC_LABELS[item.metric]}", "", _metric_block(sheet, item.metric), ""])
    if not sheet.material:
        blocks.extend(["No plan variance cleared the materiality bar.", ""])
    blocks.extend(
        [
            "Node and category lines are versus plan. Prior year is not re-judged in this commentary.",
            "",
            CLAIMS_BOUNDARY.rstrip(),
            "",
        ]
    )
    body = _header(pack, spec, engine) + "\n" + "\n".join(blocks)
    return body + "\n" + _fact_index(body)


def _exceptions_brief(pack: KpiPack, sheet: FactSheet, spec: TemplateSpec, engine: str) -> str:
    count = len(sheet.exceptions)
    words = count_words(count)
    count_text = words if words is not None else sheet.cite("meta.exception_count")
    intro = (
        f"This exception brief covers {count_text} policy breaches. "
        "A breach is a break of a published standard or plan bar. "
        "It is not, by itself, a cause."
    )
    parts = [
        _header(pack, spec, engine),
        intro,
        "",
        _exception_section(pack, sheet),
        "",
        "## Reviewer questions",
        "",
        _questions(sheet),
        "",
        CLAIMS_BOUNDARY.rstrip(),
        "",
    ]
    body = "\n".join(parts)
    return body + "\n" + _fact_index(body)


def _header(pack: KpiPack, spec: TemplateSpec, engine: str) -> str:
    return "\n".join(
        [
            "<!-- ops-narrative",
            f"kind: {spec.kind}",
            f"template: {spec.template_id}",
            f"period: {pack.period}",
            f"engine: {engine}",
            "-->",
            "",
            f"# {pack.entity_name} — {_period_label(pack.period)} {spec.title}",
            "",
            (
                f"Fictional synthetic pack. Template `{spec.template_id}`. "
                f"Engine `{engine}`. Currency {pack.currency}."
            ),
            "",
            f"> {pack.entity_disclaimer}",
            "",
        ]
    )


def _headline(sheet: FactSheet) -> str:
    revenue_plan = _movement(sheet, "network", "revenue", "plan", "plan")
    revenue_py = _movement(sheet, "network", "revenue", "py", "the prior year")
    margin_plan = _movement(sheet, "network", "gross_margin", "plan", "plan")
    sentences = [
        (
            f"Net revenue closed at {sheet.cite('network.revenue.actual')}, "
            f"{revenue_plan}, and {revenue_py}."
        ),
        _bar_sentence(sheet, "network", "revenue", "The revenue plan variance"),
        (
            f"Gross margin was {sheet.cite('network.gross_margin.actual')}, {margin_plan}."
        ),
        _bar_sentence(sheet, "network", "gross_margin", "The margin plan variance"),
        _otif_headline(sheet),
    ]
    return " ".join(sentences)


def _otif_headline(sheet: FactSheet) -> str:
    actual = sheet.cite("network.otif.actual")
    standard = sheet.cite("policy.otif_standard")
    breaches = [item for item in sheet.exceptions if item.metric == "otif"]
    network_breach = any(item.slice_id == "network" for item in breaches)
    if network_breach:
        return f"Network OTIF of {actual} misses the standard of {standard}."
    if breaches:
        names = _and_join(item.label for item in breaches)
        return (
            f"Network OTIF of {actual} meets the standard of {standard}. "
            f"The service breach sits at {names}."
        )
    return f"Network OTIF of {actual} meets the standard of {standard}."


def _scorecard(sheet: FactSheet) -> str:
    rows = [
        "| Metric | Actual | Plan | Vs plan | Prior year | Vs prior year |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for metric in SCORECARD_METRICS:
        style = VARIANCE_STYLE[metric]
        rows.append(
            "| {label} | {actual} | {plan} | {vs_plan} | {prior_year} | {vs_py} |".format(
                label=METRIC_LABELS[metric],
                actual=sheet.cite(f"network.{metric}.actual"),
                plan=sheet.cite(f"network.{metric}.plan"),
                vs_plan=sheet.cite(f"network.{metric}.var_plan_{style}_signed"),
                prior_year=sheet.cite(f"network.{metric}.prior_year"),
                vs_py=sheet.cite(f"network.{metric}.var_py_{style}_signed"),
            )
        )
    return "\n".join(rows)


def _prior_period_note(sheet: FactSheet) -> str:
    clause = _movement(sheet, "network", "revenue", "prior", "the prior period")
    return (
        f"Network net revenue was {clause}. "
        "Prior period is context. The plan already carries the seasonal shape, "
        "so a step-up or step-down from the prior month is not a second performance verdict."
    )


def _material_table(sheet: FactSheet) -> str:
    if not sheet.material:
        return "No plan variance at network, node, or category clears the materiality bar."
    rows = [
        "| Where | Metric | Vs plan | Why it is listed |",
        "| --- | --- | --- | --- |",
    ]
    for item in sheet.material:
        rows.append(
            f"| {item.label} | {METRIC_LABELS[item.metric]} | "
            f"{sheet.cite(item.signed_fact)} | {trigger_phrase(item.triggered_by)} |"
        )
    return "\n".join(rows)


def _metric_block(sheet: FactSheet, metric: str) -> str:
    label = METRIC_LABELS[metric]
    move = _movement(sheet, "network", metric, "plan", "plan")
    sentences = [
        (
            f"{label} was {sheet.cite(f'network.{metric}.actual')} "
            f"against a plan of {sheet.cite(f'network.{metric}.plan')}, {move}."
        ),
        _bar_sentence(sheet, "network", metric, "That plan variance"),
    ]
    local = [item for item in sheet.material if item.metric == metric and item.slice_id != "network"]
    if local:
        top = max(local, key=lambda item: item.rank_key)
        top_move = _movement(sheet, top.slice_id, metric, "plan", "plan")
        sentences.append(f"The concentrated movement is {top.label}, {top_move}.")
        drill = _drill_for(sheet, top.slice_id, metric)
        if drill is not None:
            sentences.append(_share_sentence(sheet, drill, "that plan variance"))
    elif metric in sheet.broad_metrics:
        sentences.append(
            "The move shows up across nodes and categories. None is concentrated enough to narrate on its own."
        )
    else:
        sentences.append("No node or category movement versus plan clears the materiality bar.")
    network_drill = _drill_for(sheet, "network", metric)
    if network_drill is not None:
        sentences.append(_share_sentence(sheet, network_drill, "the network plan variance"))
    related = [item for item in sheet.exceptions if item.metric == metric]
    if related:
        ids = ", ".join(f"`{item.exception_id}`" for item in related)
        sentences.append(f"Open exception ids: {ids}.")
    else:
        sentences.append("No policy exception is open on this metric.")
    return " ".join(sentences)


def _exception_section(pack: KpiPack, sheet: FactSheet) -> str:
    if not sheet.exceptions:
        return "No policy exception fired for this period."
    rows = [
        "| Id | Where | Metric | Reading | Bar | Rule |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in sheet.exceptions:
        rows.append(
            f"| `{item.exception_id}` | {item.label} | {METRIC_LABELS[item.metric]} | "
            f"{sheet.cite(item.comparison_fact)} | {sheet.cite(item.bar_fact)} | `{item.rule}` |"
        )
    blocks = ["\n".join(rows), ""]
    quoted: set[str] = set()
    for item in sheet.exceptions:
        prose, used = _exception_prose(pack, sheet, item, quoted)
        quoted.update(used)
        blocks.append(prose)
        blocks.append("")
    return "\n".join(blocks).rstrip()


def _share_sentence(sheet: FactSheet, drill: Drill, parent_phrase: str) -> str:
    return (
        f"{drill.cell_label} holds {sheet.cite(drill.share_fact)} of {parent_phrase}. "
        "The share is arithmetic, not a cause."
    )


def _exception_prose(
    pack: KpiPack,
    sheet: FactSheet,
    item: ExceptionItem,
    already_quoted: set[str],
) -> tuple[str, set[str]]:
    level = sheet.cite(item.actual_fact)
    bar = sheet.cite(item.bar_fact)
    if item.comparison_fact == item.actual_fact:
        reading = f"actual {level}"
    else:
        reading = f"actual {level}, a plan gap of {sheet.cite(item.comparison_fact)}"
    lead = (
        f"{item.label} is an exception `{item.exception_id}` on {METRIC_LABELS[item.metric]}: "
        f"{reading}. The bar is {bar} (`{item.rule}`)."
    )
    notes = [note for note in pack.notes if note.note_id in item.note_ids]
    if not notes:
        return lead + " No operating note is attached. A cause is not assigned.", set()
    fresh = [note for note in notes if note.note_id not in already_quoted]
    if not fresh:
        return (
            lead + " The operating note on this slice is already quoted above. It is not a quantified bridge.",
            set(),
        )
    quotes = "\n\n".join(f"> {note.text}" for note in fresh)
    return (
        f"{lead}\n\n{quotes}\n\nRecorded context only. The note is not a quantified bridge.",
        {note.note_id for note in fresh},
    )


def _questions(sheet: FactSheet) -> str:
    questions: list[str] = []
    otif = [item for item in sheet.exceptions if item.metric == "otif"]
    network_otif = any(item.slice_id == "network" for item in otif)
    local_otif = [item for item in otif if item.slice_id != "network"]
    if local_otif and not network_otif:
        names = _and_join(item.label for item in local_otif)
        questions.append(
            f"Does the service breach at {names} qualify the network month, "
            "even though network OTIF still meets the standard?"
        )
    if network_otif:
        questions.append(
            "Network OTIF misses the standard. Is the close commentary ready, "
            "or does service need a quantified bridge that this pack does not contain?"
        )
    for item in sheet.exceptions:
        if item.metric == "forecast_accuracy" and not item.note_ids:
            questions.append(
                f"{item.label} forecast accuracy breaches the floor and no operating note is attached. "
                "What should demand planning add before this brief is treated as closed?"
            )
        elif item.metric == "dos" and item.note_ids:
            questions.append(
                f"{item.label} is past the days-of-supply ceiling and a note is attached. "
                "The note is not a write-down. Is the close disclosure only, or does finance want a separate inventory action?"
            )
        elif item.metric == "revenue" and not item.note_ids:
            questions.append(
                f"{item.label} revenue breaches the plan bar. No price, volume, or mix bridge was supplied. "
                "What should commercial add before a cause is written into the close?"
            )
        elif item.metric == "expedite_cost":
            questions.append(
                f"{item.label} expedite cost breaches its plan bar. "
                "Should premium freight be disclosed on its own, without being treated as the explanation of service?"
            )
        elif item.metric == "gross_margin":
            questions.append(
                f"{item.label} margin breaches the plan bar. No cost bridge was supplied. "
                "What should finance add before the gap is explained?"
            )
    if not questions:
        questions.append(
            "No policy exception fired. Is the scorecard still the right close narrative, "
            "or is a watch-item missing from the published policy?"
        )
    unique: list[str] = []
    for question in questions:
        if question not in unique:
            unique.append(question)
    return "\n".join(f"- {question}" for question in unique)


def _movement(sheet: FactSheet, slice_id: str, metric: str, baseline: str, noun: str) -> str:
    style = VARIANCE_STYLE[metric]
    abs_id = f"{slice_id}.{metric}.var_{baseline}_{style}_abs"
    signed_id = f"{slice_id}.{metric}.var_{baseline}_{style}_signed"
    sign = display_sign(sheet.facts[signed_id].primary)
    word = {1: "above", -1: "below", 0: "in line with"}[sign]
    return f"{sheet.cite(abs_id)} {word} {noun}"


def _bar_sentence(sheet: FactSheet, slice_id: str, metric: str, subject: str) -> str:
    level = sheet.slices[slice_id].levels[metric]
    flag = materiality(metric, level.actual, level.plan)
    if flag is None:
        return f"{subject} sits inside the materiality bar."
    return f"{subject} {trigger_phrase(flag)}."


def _drill_for(sheet: FactSheet, slice_id: str, metric: str) -> Drill | None:
    for drill in sheet.drills:
        if drill.parent_slice == slice_id and drill.metric == metric:
            return drill
    return None


def _fact_index(body: str) -> str:
    seen: list[str] = []
    for fact_id in re.findall(r"\(cite:([a-z0-9_.]+)\)", body):
        if fact_id not in seen:
            seen.append(fact_id)
    lines = ["## Fact index", ""]
    lines.extend(f"- `{fact_id}`" for fact_id in seen)
    return "\n".join(lines)


def _period_label(period: str) -> str:
    year, month = period.split("-")
    return f"{_MONTHS[month]} {year}"


def _and_join(items: Iterable[str]) -> str:
    values = list(dict.fromkeys(items))
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"
