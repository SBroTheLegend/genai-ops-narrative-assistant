"""Prompt text pinned to the same ids as the templates.

The deterministic engine does not send these anywhere. They exist so an
optional polish hook has a versioned instruction, and so a reviewer can see
the constraint the model would have been under. The hook still discards a
draft that fails the faithfulness gate. The prompt is not the control.
"""

from __future__ import annotations

from ops_narrative.errors import TemplateError

_SHARED = """
You are polishing an executive operations and finance brief.
Rules you cannot break:
- Do not add, remove, or alter any number, percent, basis point, day count, or citation.
- Do not add a cause, customer, person, market fact, or recommendation that is not already in the draft.
- Do not turn an operating note into a quantified bridge.
- Do not invent a price, volume, or mix explanation.
- Keep the claims boundary intact.
- If a sentence is already precise, leave it.
Return only the brief.
""".strip()

PROMPTS: dict[str, str] = {
    "month_end.v1.0.0": _SHARED
    + "\n\nTemplate month_end.v1.0.0. Preserve the scorecard, the material-variance table, every exception id, and the reviewer questions.",
    "month_end.v0.9.0": _SHARED
    + "\n\nTemplate month_end.v0.9.0. This retired brief is a scorecard only. Do not add exception prose.",
    "variance.v1.0.0": _SHARED
    + "\n\nTemplate variance.v1.0.0. Do not describe an immaterial movement as if it had been judged.",
    "exception.v1.0.0": _SHARED
    + "\n\nTemplate exception.v1.0.0. Where the draft says a cause is not assigned, do not supply one.",
}


def prompt_for(template_id: str) -> str:
    try:
        return PROMPTS[template_id]
    except KeyError as exc:
        raise TemplateError(f"No prompt is registered for {template_id}.") from exc
