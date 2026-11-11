"""Command line for packs, briefs, review, and figures.

Exit 0 when the requested work succeeded. Exit 1 when a review gate fails.
Exit 2 when the invocation itself is invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ops_narrative import __version__
from ops_narrative.charts import write_figures
from ops_narrative.data.generate import generate_sample_packs
from ops_narrative.data.store import dump_pack, load_pack
from ops_narrative.errors import OpsNarrativeError
from ops_narrative.identity import DEFAULT_SEED, ENTITY_DISCLAIMER, ENTITY_NAME, HERO_PERIOD, SAMPLE_PERIODS
from ops_narrative.narrative.compose import compose
from ops_narrative.narrative.templates import SPECS
from ops_narrative.paths import repo_root, sample_figure_dir, sample_output_dir, synthetic_dir
from ops_narrative.review.faithfulness import format_report, review_markdown


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except OpsNarrativeError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ops-narrative",
        description=(
            "Draft evidence-backed operations and finance narratives from a synthetic KPI pack. "
            "The default engine is deterministic and does not call an external model."
        ),
    )
    parser.add_argument("--version", action="version", version=f"ops-narrative {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate-packs", help="Write deterministic synthetic KPI packs.")
    generate.add_argument("--seed", type=int, default=DEFAULT_SEED)
    generate.add_argument("--out", type=Path, default=None)
    generate.set_defaults(func=_generate)

    narrate = sub.add_parser("narrate", help="Render a brief from a pack.")
    narrate.add_argument("--pack", type=Path, required=True)
    narrate.add_argument("--kind", default="month-end")
    narrate.add_argument("--template", default=None)
    narrate.add_argument("--out", type=Path, default=None)
    narrate.add_argument("--review", action="store_true", help="Review the brief and fail if the gate fails.")
    narrate.set_defaults(func=_narrate)

    review = sub.add_parser("review", help="Score a brief against its pack.")
    review.add_argument("--pack", type=Path, required=True)
    review.add_argument("--narrative", type=Path, required=True)
    review.add_argument("--template", default=None)
    review.add_argument("--json-out", type=Path, default=None)
    review.set_defaults(func=_review)

    charts = sub.add_parser("charts", help="Write the sample figures for a pack.")
    charts.add_argument("--pack", type=Path, required=True)
    charts.add_argument("--out", type=Path, default=None)
    charts.set_defaults(func=_charts)

    samples = sub.add_parser("samples", help="Regenerate committed sample packs, briefs, and figures.")
    samples.add_argument("--seed", type=int, default=DEFAULT_SEED)
    samples.set_defaults(func=_samples)

    templates = sub.add_parser("templates", help="List template ids and which one is active.")
    templates.set_defaults(func=_templates)
    return parser


def _generate(args: argparse.Namespace) -> int:
    out = args.out or synthetic_dir()
    packs = generate_sample_packs(seed=args.seed)
    _write_packs(packs, out, args.seed)
    print(f"Wrote {len(packs)} packs to {out}")
    return 0


def _narrate(args: argparse.Namespace) -> int:
    pack = load_pack(args.pack)
    text = compose(pack, template_id=args.template, kind=None if args.template else args.kind)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    else:
        sys.stdout.write(text)
    if args.review:
        report = review_markdown(text, pack, template_id=args.template)
        print(format_report(report), file=sys.stderr)
        return 0 if report.passed else 1
    return 0


def _review(args: argparse.Namespace) -> int:
    pack = load_pack(args.pack)
    text = args.narrative.read_text(encoding="utf-8")
    report = review_markdown(text, pack, template_id=args.template)
    print(format_report(report))
    for finding in report.findings:
        print(f"- {finding.code}: {finding.detail}")
    if args.json_out:
        payload = {
            "passed": report.passed,
            "template_id": report.template_id,
            "faithfulness_score": report.faithfulness_score,
            "coverage_score": report.coverage_score,
            "citation_count": report.citation_count,
            "ungrounded_count": report.ungrounded_count,
            "direction_ok": report.direction_ok,
            "attribution_ok": report.attribution_ok,
            "missing": list(report.missing),
            "findings": [{"code": item.code, "detail": item.detail} for item in report.findings],
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if report.passed else 1


def _charts(args: argparse.Namespace) -> int:
    pack = load_pack(args.pack)
    out = args.out or sample_figure_dir()
    for path in write_figures(pack, out):
        print(path)
    return 0


def _samples(args: argparse.Namespace) -> int:
    root = repo_root()
    pack_dir = synthetic_dir(root)
    output_dir = sample_output_dir(root)
    figure_dir = sample_figure_dir(root)
    packs = generate_sample_packs(seed=args.seed)
    _write_packs(packs, pack_dir, args.seed)
    hero = next(pack for pack in packs if pack.period == HERO_PERIOD)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind, filename in (
        ("month-end", f"{HERO_PERIOD}-month-end.md"),
        ("variance", f"{HERO_PERIOD}-variance.md"),
        ("exceptions", f"{HERO_PERIOD}-exceptions.md"),
    ):
        text = compose(hero, kind=kind)
        path = output_dir / filename
        path.write_text(text, encoding="utf-8")
        report = review_markdown(text, hero)
        if not report.passed:
            print(format_report(report), file=sys.stderr)
            for finding in report.findings[:12]:
                print(f"- {finding.code}: {finding.detail}", file=sys.stderr)
            return 1
        written.append(path)
    review_path = output_dir / f"{HERO_PERIOD}-review.json"
    hero_text = (output_dir / f"{HERO_PERIOD}-month-end.md").read_text(encoding="utf-8")
    report = review_markdown(hero_text, hero)
    review_path.write_text(
        json.dumps(
            {
                "passed": report.passed,
                "template_id": report.template_id,
                "faithfulness_score": report.faithfulness_score,
                "coverage_score": report.coverage_score,
                "citation_count": report.citation_count,
                "ungrounded_count": report.ungrounded_count,
                "direction_ok": report.direction_ok,
                "attribution_ok": report.attribution_ok,
                "fictional": True,
                "entity_name": ENTITY_NAME,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    figures = write_figures(hero, figure_dir)
    print(f"Packs: {pack_dir}")
    for path in written:
        print(path)
    print(review_path)
    for path in figures:
        print(path)
    return 0


def _templates(_args: argparse.Namespace) -> int:
    for spec in SPECS:
        marker = "active" if spec.status == "active" else spec.status
        print(f"{spec.template_id:24} {spec.kind:12} {marker:8} {spec.summary}")
    return 0


def _write_packs(packs, out: Path, seed: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for pack in packs:
        dump_pack(pack, out / f"{pack.period}.json")
    manifest = {
        "fictional": True,
        "entity_name": ENTITY_NAME,
        "entity_disclaimer": ENTITY_DISCLAIMER,
        "seed": seed,
        "periods": list(SAMPLE_PERIODS),
        "hero_period": HERO_PERIOD,
        "schema_version": packs[0].schema_version,
        "generator_version": packs[0].generator_version,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
