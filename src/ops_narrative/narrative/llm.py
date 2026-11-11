"""Optional external polish hook. Off by default.

This module does not import a provider SDK and does not read an API key.
A caller who sets OPS_NARRATIVE_LLM=1 must inject a transport. The transport
is untrusted: if the returned text fails the review gate, the deterministic
draft is kept.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from ops_narrative.errors import LLMConfigError
from ops_narrative.models import KpiPack
from ops_narrative.narrative.prompts import prompt_for
from ops_narrative.review.faithfulness import review_markdown

Transport = Callable[[str, str], str]


def engine_name(environ: Mapping[str, str]) -> str:
    flag = environ.get("OPS_NARRATIVE_LLM", "0").strip()
    if flag in {"", "0", "false", "False", "no", "off"}:
        return "deterministic"
    if flag == "1":
        return "external"
    raise LLMConfigError("OPS_NARRATIVE_LLM must be 0 or 1.")


def maybe_polish(
    draft: str,
    pack: KpiPack,
    *,
    template_id: str,
    environ: Mapping[str, str],
    transport: Transport | None = None,
) -> tuple[str, dict[str, object]]:
    """Return the text to publish and a small status dict.

    External mode without a transport does not call the network. It raises,
    so a mis-set flag cannot look like a successful model run.
    """
    mode = engine_name(environ)
    if mode == "deterministic":
        return draft, {"engine": "deterministic", "polished": False, "rejected": False}
    if transport is None:
        raise LLMConfigError(
            "OPS_NARRATIVE_LLM=1 but no transport was provided. "
            "This build does not call a paid API and does not read a key from disk."
        )
    prompt = prompt_for(template_id)
    polished = transport(draft, prompt)
    report = review_markdown(polished, pack, template_id=template_id)
    if not report.passed:
        return draft, {
            "engine": "deterministic",
            "polished": False,
            "rejected": True,
            "reason": "polish failed the review gate",
        }
    return polished, {"engine": "external", "polished": True, "rejected": False}
