"""Errors a caller can catch without parsing message text."""

from __future__ import annotations


class OpsNarrativeError(Exception):
    """Base error for packs, templates, and the optional language-model hook."""


class PackValidationError(OpsNarrativeError):
    """The pack is internally inconsistent or violates the sample-data rules."""


class TemplateError(OpsNarrativeError):
    """The requested narrative template is unknown."""


class LLMConfigError(OpsNarrativeError):
    """The optional external hook was requested in a way this build cannot run."""
