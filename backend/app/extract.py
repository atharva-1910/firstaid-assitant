"""Feature F1: symptom and detail extraction (owner: Taneesha Badhe).

Pulls the structured slots of Section 8.3 out of free text, using the per-language
lexicons, then applies F3 (negation and uncertainty) to every extracted fact.
In real mode this can be swapped for spaCy EntityRuler pipelines fed by the same lexicons.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import lexicon as lx
from .negation import CueHit, attach_cues
from .normalize import Normalized, Token, normalize, tokenize

SAFETY_SLOTS = ("responsive", "breathing", "power_off")

# When one message gives two values for a slot, the more serious one wins.
SEVERITY = {
    "responsive": ["no", "yes"],
    "breathing": ["absent", "abnormal", "normal"],
    "chest_pain": ["yes", "no"],
    "choking_signs": ["weak_or_silent", "coughing_strongly", "none"],
    "bite_type": ["snake", "scorpion", "dog", "other_mammal", "insect_sting"],
    "allergy_signs": ["yes", "no"],
    "burn_cause": ["electrical", "chemical_acid", "hot_liquid_steam", "fire_heat"],
    "burn_area": ["eyes_or_face", "large", "sensitive_area", "small"],
    "power_off": ["no", "yes"],
    "age_group": ["infant", "child", "adult"],
}


@dataclass
class Evidence:
    """One lexicon hit, kept so F4 can point at the user's own words."""
    term: str
    text: str  # the user's original spelling
    start: int  # char offsets in the original text
    end: int
    polarity: str  # affirmed | negated | uncertain
    slots: dict
    flags: list[str]
    sits: list[str]


@dataclass
class Extraction:
    lang: str
    slots: dict = field(default_factory=dict)
    uncertain: set = field(default_factory=set)
    flags: set = field(default_factory=set)
    sits: dict = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    cues: list[dict] = field(default_factory=list)


def _set_slot(slots: dict, slot: str, value: str) -> None:
    if slot not in slots:
        slots[slot] = value
        return
    order = SEVERITY.get(slot)
    if order and value in order and slots[slot] in order and order.index(value) < order.index(slots[slot]):
        slots[slot] = value


def _char_span(norm: Normalized, tokens: list[Token], start: int, end: int) -> tuple[int, int, str]:
    cs, ce = tokens[start].start, tokens[end - 1].end
    os_, oe = norm.original_span(cs, ce)
    return os_, oe, norm.original[os_:oe]


def _age_and_time(norm: Normalized, lex: lx.CompiledLexicon, out: Extraction) -> None:
    text = norm.text
    years = re.compile(r"(?<![\d])(\d{1,3})\s*-?\s*(?:" + lx.units_regex(lex.year_units) + ")")
    months = re.compile(r"(?<![\d])(\d{1,2})\s*-?\s*(?:" + lx.units_regex(lex.month_units) + ")")
    times = re.compile(r"(?<![\d])(\d{1,3})\s*(?:" + lx.units_regex(lex.time_units) + ")")
    for m in months.finditer(text):
        n = int(m.group(1))
        _set_slot(out.slots, "age_group", "infant" if n < 12 else "child")
        s, e = norm.original_span(m.start(), m.end())
        out.evidence.append(Evidence("months", norm.original[s:e], s, e, "affirmed", {"age_group": out.slots["age_group"]}, [], []))
    for m in years.finditer(text):
        n = int(m.group(1))
        group = "infant" if n < 1 else ("child" if n < 18 else "adult")
        _set_slot(out.slots, "age_group", group)
        s, e = norm.original_span(m.start(), m.end())
        out.evidence.append(Evidence("years", norm.original[s:e], s, e, "affirmed", {"age_group": group}, [], []))
    for m in times.finditer(text):
        s, e = norm.original_span(m.start(), m.end())
        out.slots["time_since"] = norm.original[s:e].strip()


def extract(text: str, lang: str) -> Extraction:
    norm = normalize(text)
    tokens = tokenize(norm)
    lex = lx.get(lang)
    out = Extraction(lang=lang)

    consumed: set[int] = set()
    # 1. Uncertainty phrases first, so "not sure" / "pata nahi" are not read as negation.
    unc = lx.find_matches(tokens, lex.unc_terms, consumed, fuzzy=False)
    # 2. Lexicon entries (longest first). Phrases that contain a negation word consume it.
    matches = lx.find_matches(tokens, lex.entry_terms, consumed)
    # 3. Remaining negation cues.
    neg = lx.find_matches(tokens, lex.neg_terms, consumed, fuzzy=False)
    cues = [CueHit("unc", m.start, m.end, m.term) for m in unc] + [CueHit("neg", m.start, m.end, m.term) for m in neg]
    out.cues = [{"kind": c.kind, "term": c.term} for c in cues]
    attached = attach_cues(tokens, lex, matches, cues)

    for mi, m in enumerate(matches):
        entry = lex.entries[m.ref]
        mcues = attached.get(mi, [])
        kinds = {c.kind for c in mcues}
        negated = "neg" in kinds
        uncertain = "unc" in kinds
        if negated:
            if "neg" not in entry:
                continue
            slots = dict(entry["neg"])
            sits = entry.get("neg_sit", [])
            flags: list[str] = []
            polarity = "negated"
        else:
            slots = dict(entry.get("set", {}))
            sits = entry.get("sit", [])
            flags = list(entry.get("flags", []))
            polarity = "affirmed"
        if uncertain:
            polarity = "uncertain"
            for slot in list(slots):
                if slot in SAFETY_SLOTS:
                    out.uncertain.add(slot)
                    slots.pop(slot)
        for slot, value in slots.items():
            _set_slot(out.slots, slot, value)
        out.flags.update(flags)
        w = float(entry.get("w", 1.0))
        for s in sits:
            out.sits[s] = out.sits.get(s, 0.0) + w
        # The highlighted span includes the attached cue ("saans nahi le rahe", not just "saans").
        lo = min([m.start] + [c.start for c in mcues])
        hi = max([m.end] + [c.end for c in mcues])
        cs, ce, orig = _char_span(norm, tokens, lo, hi)
        out.evidence.append(Evidence(m.term, orig, cs, ce, polarity, slots, flags, list(sits)))

    for a in lx.find_matches(tokens, lex.action_terms, set()):
        name = lex.actions[a.ref]
        if name not in out.actions:
            out.actions.append(name)

    _age_and_time(norm, lex, out)

    # Choking: "can't breathe" while choking describes the airway, not an unresponsive person.
    if "choking_ctx" in out.flags and out.slots.get("responsive") != "no":
        if out.slots.get("breathing") in ("absent", "abnormal") or "distress" in out.flags:
            out.slots["choking_signs"] = "weak_or_silent"
            out.slots.pop("breathing", None)
            out.uncertain.discard("breathing")
            for ev in out.evidence:
                if "breathing" in ev.slots and "unresponsive" in ev.sits:
                    out.sits["unresponsive"] = max(0.0, out.sits.get("unresponsive", 0.0) - 1.0)
                    ev.sits.remove("unresponsive")
                    ev.slots = {"choking_signs": "weak_or_silent"}
            if not out.sits.get("unresponsive"):
                out.sits.pop("unresponsive", None)
    # A certain value in the same message beats an uncertain mention.
    for slot in list(out.uncertain):
        if slot in out.slots:
            out.uncertain.discard(slot)
    return out


# ---------------------------------------------------------------- cross-language safety net

# The other language written in the same script: a wrong language guess lands on it.
SIBLING = {"hi": "mr", "mr": "hi", "en": "hinglish", "hinglish": "en"}
# Values that can only make the system more cautious.
RAISING = {
    "responsive": {"no"},
    "breathing": {"absent", "abnormal"},
    "chest_pain": {"yes"},
    "choking_signs": {"weak_or_silent"},
    "bite_type": {"snake"},
    "allergy_signs": {"yes"},
    "burn_cause": {"electrical", "chemical_acid"},
    "burn_area": {"eyes_or_face", "large", "sensitive_area"},
    "power_off": {"no"},
    "age_group": {"infant", "child"},
}
# Context slots: taken only when the main pass found none, so a burn or bite is not missed.
CONTEXT = ("burn_cause", "bite_type")


def _more_severe(slot: str, new: str, old: str | None) -> bool:
    if old is None:
        return True
    order = SEVERITY.get(slot, [])
    return new in order and old in order and order.index(new) < order.index(old)


def extract_safe(text: str, lang: str) -> Extraction:
    """F1 with a safety net against a wrong language guess.

    Runs extraction again with the sibling language's lexicon and keeps only facts that raise
    urgency, from words the main pass did not already read. A model can only make the system
    more cautious, never less (Section 8.2).
    """
    out = extract(text, lang)
    other = extract(text, SIBLING.get(lang, lang)) if SIBLING.get(lang) else None
    if other is None:
        return out
    seen = [(e.start, e.end) for e in out.evidence]
    for ev in other.evidence:
        if any(ev.start < e and s < ev.end for s, e in seen):
            continue
        adopted = {
            k: v for k, v in ev.slots.items()
            if (v in RAISING.get(k, ()) and _more_severe(k, v, out.slots.get(k))) or (k in CONTEXT and k not in out.slots)
        }
        new_flags = [f for f in ev.flags if f not in out.flags]
        if not adopted and not new_flags:
            continue
        out.slots.update(adopted)
        for slot in adopted:
            out.uncertain.discard(slot)
        out.flags.update(new_flags)
        for s in ev.sits:
            out.sits[s] = out.sits.get(s, 0.0) + 1.0
        out.evidence.append(ev)
        seen.append((ev.start, ev.end))
    return out
