"""Cursor IDE adapter feature slice."""

from __future__ import annotations

from agent_gauntlet.features.adapters.cursor.adapter import CursorAdapter
from agent_gauntlet.features.adapters.cursor.validator import CursorRulesValidator

__all__ = [
    "CursorAdapter",
    "CursorRulesValidator",
]
