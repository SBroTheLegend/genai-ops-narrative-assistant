"""The external hook is off unless asked, and a bad polish is discarded."""

from __future__ import annotations

import pytest

from ops_narrative.data.generate import generate_pack
from ops_narrative.errors import LLMConfigError
from ops_narrative.identity import HERO_PERIOD
from ops_narrative.narrative.compose import compose
from ops_narrative.narrative.llm import engine_name, maybe_polish


def test_default_environment_stays_deterministic():
    assert engine_name({}) == "deterministic"
    assert engine_name({"OPS_NARRATIVE_LLM": "0"}) == "deterministic"


def test_garbage_flag_is_rejected():
    with pytest.raises(LLMConfigError):
        engine_name({"OPS_NARRATIVE_LLM": "maybe"})


def test_external_mode_without_a_transport_does_not_pretend_to_call_out():
    pack = generate_pack(HERO_PERIOD)
    draft = compose(pack, kind="variance")
    with pytest.raises(LLMConfigError):
        maybe_polish(
            draft,
            pack,
            template_id="variance.v1.0.0",
            environ={"OPS_NARRATIVE_LLM": "1"},
            transport=None,
        )


def test_polish_that_changes_a_figure_is_discarded():
    pack = generate_pack(HERO_PERIOD)
    draft = compose(pack, kind="variance")

    def transport(text: str, prompt: str) -> str:
        assert "Do not add" in prompt
        return text + "\n\nUpside of $9.9M was added by the model.\n"

    kept, status = maybe_polish(
        draft,
        pack,
        template_id="variance.v1.0.0",
        environ={"OPS_NARRATIVE_LLM": "1"},
        transport=transport,
    )
    assert kept == draft
    assert status["rejected"] is True
    assert status["polished"] is False


def test_polish_that_preserves_the_draft_can_pass():
    pack = generate_pack(HERO_PERIOD)
    draft = compose(pack, kind="variance")

    def transport(text: str, prompt: str) -> str:
        return text

    kept, status = maybe_polish(
        draft,
        pack,
        template_id="variance.v1.0.0",
        environ={"OPS_NARRATIVE_LLM": "1"},
        transport=transport,
    )
    assert kept == draft
    assert status == {"engine": "external", "polished": True, "rejected": False}
