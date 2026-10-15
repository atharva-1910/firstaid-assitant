"""Urgency levels, ordered from least to most urgent."""
from __future__ import annotations

URGENCY_ORDER = {"home": 0, "clinic": 1, "emergency": 2}


def max_urgency(*levels: str | None) -> str:
    present = [l for l in levels if l]
    return max(present, key=lambda l: URGENCY_ORDER[l]) if present else "home"
