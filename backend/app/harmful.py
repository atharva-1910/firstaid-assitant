"""Harmful-action detection against the myth set (content/myths.jsonl).

Stub-mode stand-in for the IndicBERT v2 harmful-action head. A myth fires when one of its
patterns appears in the message, the conversation is about the myth's situation, and no
negation cue sits right next to it ("do not give water" is not a harmful action).
"""
from __future__ import annotations

from functools import lru_cache

from . import content
from . import lexicon as lx
from .normalize import normalize, normalize_term, tokenize

NEG_GAP = 2


@lru_cache(maxsize=8)
def _compiled(lang: str) -> list[tuple[dict, list[list[lx.Term]]]]:
    out = []
    langs = [lang] + (["en"] if lang == "hinglish" else [])
    for m in content.myths():
        groups: list[list[lx.Term]] = []
        for l in langs:
            for g_i, group in enumerate(m["patterns"].get(l, [])):
                terms = [t for t in (lx._compile_term(a, 0) for a in group) if t]
                if g_i < len(groups):
                    groups[g_i].extend(terms)
                else:
                    groups.append(terms)
        out.append((m, groups))
    return out


def _subtype(myth: dict, slots: dict) -> str:
    if myth["situation"] == "bites":
        return slots.get("bite_type") or "unknown"
    if myth["situation"] == "burns":
        return slots.get("burn_cause") or "unknown"
    return ""


def detect(text: str, lang: str, slots: dict, flags: set, situations: set[str]) -> list[dict]:
    norm = normalize(text)
    tokens = tokenize(norm)
    lex = lx.get(lang)
    neg_positions: set[int] = set()
    for m in lx.find_matches(tokens, lex.neg_terms, set(), fuzzy=False):
        neg_positions.update(range(m.start, m.end))
    found = []
    for myth, groups in _compiled(lang):
        if myth["situation"] not in situations:
            continue
        subs = myth.get("subtypes") or []
        if subs and _subtype(myth, slots) not in subs:
            continue
        req = myth.get("requires", {})
        if req.get("power_off_not") and slots.get("power_off") == req["power_off_not"]:
            continue
        spans = []
        ok = bool(groups)
        for group in groups:
            hits = lx.find_matches(tokens, group, set(), fuzzy=False)
            hits = [h for h in hits if not any(p in neg_positions for p in range(h.start - NEG_GAP, h.end + NEG_GAP))]
            if not hits:
                ok = False
                break
            spans.append(hits[0])
        if not ok:
            continue
        h = spans[0]
        cs, ce = norm.original_span(tokens[h.start].start, tokens[h.end - 1].end)
        found.append({"myth": myth, "word": norm.original[cs:ce], "start": cs, "end": ce})
    return found
