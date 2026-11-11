"""Synthetic pack generation and JSON persistence."""

from ops_narrative.data.generate import generate_history, generate_pack
from ops_narrative.data.store import dump_pack, load_pack

__all__ = ["dump_pack", "generate_history", "generate_pack", "load_pack"]
