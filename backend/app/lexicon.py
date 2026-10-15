"""Compiles the per-language lexicons (content/lexicons/{lang}.json) into token matchers.

Matching is token based and typo tolerant:
  * exact token match;
  * a lexicon token ending in '*' matches any token that starts with it (useful for Hindi and Marathi suffixes);
  * Latin tokens of 5+ letters may match with rapidfuzz ratio >= 85 (Section 8.3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from rapidfuzz import fuzz

from . import content
from .normalize import Token, normalize_term

FUZZY_THRESHOLD = 85
FUZZY_MIN_LEN = 5
_LATIN = re.compile(r"^[a-z0-9']+$")


@dataclass(frozen=True)
class TermTok:
    text: str
    prefix: bool


@dataclass
class Term:
    toks: tuple[TermTok, ...]
    raw: str
    ref: int  # index of the entry / action / cue this term belongs to


@dataclass
class Match:
    ref: int
    term: str
    start: int  # token index
    end: int  # token index, exclusive
    score: float


@dataclass
class CompiledLexicon:
    lang: str
    direction: str
    entries: list[dict]
    entry_terms: list[Term]
    neg_terms: list[Term]
    unc_terms: list[Term]
    action_terms: list[Term]
    actions: list[str]
    breakers: set[str]
    year_units: list[str]
    month_units: list[str]
    time_units: list[str]
    markers: set[str] = field(default_factory=set)
    strong_markers: set[str] = field(default_factory=set)


def _compile_term(raw: str, ref: int) -> Term | None:
    norm = normalize_term(raw)
    parts = norm.split()
    if not parts:
        return None
    toks = []
    for p in parts:
        prefix = p.endswith("*")
        toks.append(TermTok(p.rstrip("*"), prefix))
    return Term(tuple(toks), raw, ref)


def _compile_list(raws: list[str], ref_of=lambda i: i) -> list[Term]:
    out = []
    for i, r in enumerate(raws):
        t = _compile_term(r, ref_of(i))
        if t:
            out.append(t)
    return out


@lru_cache(maxsize=8)
def get(lang: str) -> CompiledLexicon:
    layers = [content.raw_lexicon(lang)]
    for inc in layers[0].get("include", []):
        layers.append(content.raw_lexicon(inc))

    entries: list[dict] = []
    action_names: list[str] = []
    action_raw: list[tuple[str, int]] = []
    neg: list[str] = []
    unc: list[str] = []
    breakers: set[str] = set()
    years: list[str] = []
    months: list[str] = []
    times: list[str] = []
    for layer in layers:
        entries.extend(layer.get("entries", []))
        for a in layer.get("actions", []):
            idx = len(action_names)
            action_names.append(a["action"])
            action_raw.extend((t, idx) for t in a["terms"])
        neg.extend(layer.get("negation_cues", []))
        unc.extend(layer.get("uncertainty_cues", []))
        breakers.update(normalize_term(b) for b in layer.get("scope_breakers", []))
        au = layer.get("age_units", {})
        years.extend(au.get("years", []))
        months.extend(au.get("months", []))
        times.extend(layer.get("time_units", []))

    entry_terms: list[Term] = []
    for i, e in enumerate(entries):
        for raw in e["terms"]:
            t = _compile_term(raw, i)
            if t:
                entry_terms.append(t)
    action_terms = [t for t in (_compile_term(r, i) for r, i in action_raw) if t]

    base = layers[0]
    return CompiledLexicon(
        lang=lang,
        direction=base.get("cue_direction", "before"),
        entries=entries,
        entry_terms=entry_terms,
        neg_terms=_compile_list(neg),
        unc_terms=_compile_list(unc),
        action_terms=action_terms,
        actions=action_names,
        breakers=breakers,
        year_units=years,
        month_units=months,
        time_units=times,
        markers={normalize_term(m) for m in base.get("markers", [])},
        strong_markers={normalize_term(m) for m in base.get("strong_markers", [])},
    )


def _tok_score(tt: TermTok, tok: str) -> float:
    if tok == tt.text:
        return 100.0
    if tt.prefix and tok.startswith(tt.text):
        return 99.0
    if len(tt.text) >= FUZZY_MIN_LEN and len(tok) >= FUZZY_MIN_LEN and _LATIN.match(tok) and _LATIN.match(tt.text):
        s = fuzz.ratio(tt.text, tok)
        if s >= FUZZY_THRESHOLD:
            return float(s)
    return 0.0


# Intensifiers that may sit inside a phrase ("chest pain" vs "chest very bad pain" is not
# covered, but "seene mein bahut dard" and "छातीत खूप दुखत" are).
FILLERS = {
    "very", "so", "really", "too", "severe", "bad", "badly", "terrible", "sudden", "suddenly", "a", "the", "his", "her", "my",
    "bahut", "bohot", "bahot", "boht", "zyada", "jyada", "tez", "achanak", "bhi", "hi",
    "बहुत", "ज्यादा", "तेज", "अचानक", "भी", "ही", "खूप", "जास्त", "फार",
}


def _match_at(tokens: list[Token], term: Term, i: int, consumed: set[int], fuzzy: bool) -> tuple[int, float] | None:
    """Tries to match `term` starting at token i. Returns (end index, mean score) or None."""
    j = i
    score_sum = 0.0
    skipped = 0
    for k, tt in enumerate(term.toks):
        while True:
            if j >= len(tokens):
                return None
            tok = tokens[j]
            if tok.is_break or j in consumed:
                return None
            if fuzzy:
                s = _tok_score(tt, tok.text)
            else:
                s = 100.0 if tok.text == tt.text or (tt.prefix and tok.text.startswith(tt.text)) else 0.0
            if s > 0:
                score_sum += s
                j += 1
                break
            # Inside a multi-word term, skip one filler word.
            if k > 0 and skipped == 0 and tok.text in FILLERS:
                skipped += 1
                j += 1
                continue
            return None
    return j, score_sum / len(term.toks)


def find_matches(tokens: list[Token], terms: list[Term], consumed: set[int], fuzzy: bool = True) -> list[Match]:
    """Non-overlapping matches, chosen longest first. Exact and prefix matches are chosen
    before any typo-tolerant (fuzzy) match, so a fuzzy hit never beats an exact one.
    Marks matched tokens in `consumed`."""
    chosen: list[Match] = []
    passes = [False, True] if fuzzy else [False]
    for use_fuzzy in passes:
        cands: list[Match] = []
        for term in terms:
            for i in range(len(tokens)):
                r = _match_at(tokens, term, i, consumed, use_fuzzy)
                if r:
                    end, score = r
                    if use_fuzzy and score >= 99.0:
                        continue  # already handled in the exact pass
                    cands.append(Match(term.ref, term.raw, i, end, score))
        cands.sort(key=lambda m: (-len(terms_of(m)), -(m.end - m.start), -m.score, m.start))
        for m in cands:
            if any(j in consumed for j in range(m.start, m.end)):
                continue
            consumed.update(range(m.start, m.end))
            chosen.append(m)
    chosen.sort(key=lambda m: m.start)
    return chosen


def terms_of(m: Match) -> list[str]:
    return m.term.split()


def units_regex(units: list[str]) -> str:
    parts = []
    for u in sorted(set(units), key=len, reverse=True):
        nu = normalize_term(u)
        if nu.endswith("*"):
            parts.append(re.escape(nu[:-1]) + r"[^\s,.;!?|।]*")
        else:
            parts.append(re.escape(nu) + r"(?![a-zऀ-ॿ])")
    return "|".join(parts) if parts else r"(?!x)x"
