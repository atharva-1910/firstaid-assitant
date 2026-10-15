"""Feature F3: negation and uncertainty handling (owner: Siddhi Karhekar).

Every negation or uncertainty cue is attached to the nearest extracted term within a
small window (3 tokens for negation, 5 for uncertainty), never across a scope breaker
(punctuation, "but", "lekin", "पण" ...). When two terms are equally close, the term in the
language's usual direction wins: English cues come before the word they negate, while in
Hindi, Hinglish and Marathi the cue usually follows the symptom noun (Section 8.5).
For English, negspacy can replace this in real mode; the window rule is used in stub mode.
"""
from __future__ import annotations

from dataclasses import dataclass

from .lexicon import CompiledLexicon, Match
from .normalize import Token

NEG_WINDOW = 3
UNC_WINDOW = 5


@dataclass
class CueHit:
    kind: str  # "neg" or "unc"
    start: int
    end: int
    term: str


def _blocked(tokens: list[Token], lo: int, hi: int, breakers: set[str]) -> bool:
    for t in tokens[lo:hi]:
        if t.is_break or t.text in breakers:
            return True
    return False


def _distance(cue: CueHit, m: Match) -> tuple[int, str] | None:
    if cue.end <= m.start:
        return (m.start - cue.end + 1, "before")  # cue before the term
    if cue.start >= m.end:
        return (cue.start - m.end + 1, "after")  # cue after the term
    return None


def attach_cues(
    tokens: list[Token],
    lex: CompiledLexicon,
    matches: list[Match],
    cues: list[CueHit],
) -> dict[int, list[CueHit]]:
    """Returns {match index: [attached cues]}."""
    result: dict[int, list[CueHit]] = {}
    for cue in cues:
        window = NEG_WINDOW if cue.kind == "neg" else UNC_WINDOW
        best: tuple[int, int, int] | None = None  # (distance, direction penalty, match index)
        for mi, m in enumerate(matches):
            entry = lex.entries[m.ref]
            if cue.kind == "neg" and "neg" not in entry:
                continue
            if cue.kind == "unc" and not entry.get("set"):
                continue
            d = _distance(cue, m)
            if d is None:
                continue
            dist, direction = d
            if dist > window:
                continue
            lo, hi = (cue.end, m.start) if direction == "before" else (m.end, cue.start)
            if _blocked(tokens, lo, hi, lex.breakers):
                continue
            penalty = 0 if direction == lex.direction else 1
            key = (dist, penalty, mi)
            if best is None or key < best:
                best = key
        if best is not None:
            result.setdefault(best[2], []).append(cue)
    return result
