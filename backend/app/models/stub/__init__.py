"""Stub-mode models (MODEL_MODE=stub): rule-based stand-ins with the same interfaces as the
real models, so the whole app runs end to end with no GPU and no downloads (Section 0.3)."""
from __future__ import annotations

import re

from ... import lexicon as lx
from ...config import SITUATIONS
from ...extract import extract
from ...harmful import detect as detect_harmful
from ...normalize import normalize, tokenize
from ...safety_rules import evaluate

CLASSES = list(SITUATIONS) + ["out_of_scope"]
EPS = 0.05
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
# Common Hindi function words that Marathi does not use.
HINDI_MARKERS = {"है", "हैं", "नहीं", "क्या", "रहे", "रहा", "रही", "गया", "गई", "गए", "में", "को", "का", "की", "के", "ने", "से", "पर", "और", "हो", "था", "थी", "थे", "दिया", "लिया", "कर", "करें", "करूं"}


class StubLanguageId:
    """Devanagari -> Hindi or Marathi by marker words; Latin -> Hinglish if it has Hinglish words."""

    def detect(self, text: str) -> dict:
        norm = normalize(text)
        toks = [t.text for t in tokenize(norm) if not t.is_break]
        if DEVANAGARI.search(norm.text):
            tokens = tokenize(norm)
            mr_lex, hi_lex = lx.get("mr"), lx.get("hi")
            mr_hits = sum(1 for t in toks if t in mr_lex.markers)
            hi_hits = sum(1 for t in toks if t in HINDI_MARKERS)
            # Words found in only one of the two lexicons are strong evidence too.
            mr_hits += 0.5 * sum(m.end - m.start for m in lx.find_matches(tokens, mr_lex.entry_terms, set(), fuzzy=False))
            hi_hits += 0.5 * sum(m.end - m.start for m in lx.find_matches(tokens, hi_lex.entry_terms, set(), fuzzy=False))
            return {"lang": "mr" if mr_hits > hi_hits else "hi", "script": "devanagari"}
        hl = lx.get("hinglish")
        strong = sum(1 for t in toks if t in hl.strong_markers)
        weak = sum(1 for t in toks if t in hl.markers)
        is_hinglish = strong >= 1 or weak >= 2
        return {"lang": "hinglish" if is_hinglish else "en", "script": "latin"}


class StubTriage:
    """Keyword rules from the lexicons (the safety rules) plus myth matching for harmful actions."""

    def predict(self, text: str, lang: str, slots: dict) -> dict:
        facts = {k: v for k, v in slots.items() if not k.startswith("_")}
        flags = set(slots.get("_flags", []))
        sits = dict(slots.get("_sits", {}))
        rules = evaluate(facts, flags, sits)
        situations = set(slots.get("_situations", [])) or {s for s, w in sits.items() if w > 0}
        harmful = detect_harmful(text, lang, facts, flags, situations) if text else []
        scores = {u: (1.0 if u == rules.urgency else 0.0) for u in ("emergency", "clinic", "home")}
        return {"urgency": rules.urgency, "scores": scores, "harmful": harmful[0] if harmful else None, "all_harmful": harmful}


class StubSituationClassifier:
    """Keyword overlap score per situation, turned into probabilities."""

    def predict(self, text: str, lang: str) -> list[dict]:
        sits = extract(text, lang).sits
        return scores_to_probs(sits)


def scores_to_probs(sits: dict) -> list[dict]:
    raw = {c: max(0.0, sits.get(c, 0.0)) + EPS for c in CLASSES}
    total = sum(raw.values())
    out = [{"situation": c, "p": raw[c] / total} for c in CLASSES]
    out.sort(key=lambda d: -d["p"])
    return out


class StubStepVerifier:
    """Always rejects rephrasing, so the verified text is always shown."""

    def entails(self, verified: str, candidate: str, lang: str) -> bool:
        return False


class StubRephraser:
    """Rephrasing is disabled in stub mode."""

    def rephrase(self, step: str, lang: str, record: dict) -> str | None:
        return None


class StubExplainer:
    """Shows the user's words that matched the safety rules (F4, stub mode)."""

    def __init__(self) -> None:
        self.triggers: list[tuple[str, str]] = []

    def explain(self, text: str, lang: str, urgency: str, triggers: list[tuple[str, str]] | None = None) -> list[dict]:
        if urgency != "emergency" or not text:
            return []
        triggers = triggers if triggers is not None else self.triggers
        ext = extract(text, lang)
        out: list[dict] = []
        for ev in ext.evidence:
            for key, value in triggers:
                if key == "flag":
                    hit = value in ev.flags
                elif key == "sit":
                    hit = value in ev.sits and ev.polarity != "negated"
                else:
                    hit = ev.slots.get(key) == value
                if hit and not any(o["start"] == ev.start for o in out):
                    out.append({"word": ev.text, "start": ev.start, "end": ev.end, "weight": 1.0})
        return out[:3]
