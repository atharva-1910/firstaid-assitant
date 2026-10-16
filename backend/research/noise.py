"""Controlled noise for robustness tests (E3). Every function takes (text, lang, level, rng) and
returns a noisier text; level is the per-word (or per-character) probability of a change.

The noise imitates what panicked people type on a phone:
  vowel_drop   "saans nahi" -> "sns nhi"; Devanagari loses vowel signs: "साँस" -> "सस"
  typos        adjacent swap, deleted or doubled letter
  spelling     common spelling variants: aa->a, ee->i, w->v, sh->s; ी<->ि, ू<->ु, ँ->ं, nukta dropped
  code_switch  a word replaced by the English word that sets the same slot in the lexicons
               ("saans" -> "breath", "छाती" -> "chest"), so the meaning is kept
  fragment     words dropped ("saap ne kaata kheth mein" -> "saap kaata")
"""
from __future__ import annotations

import json
import random
import re
from functools import lru_cache

from .common import BACKEND

DEV = re.compile(r"[ऀ-ॿ]")
MATRAS = set(chr(c) for c in range(0x093E, 0x094D)) | {"ँ", "ं", "ॢ", "ॣ"}
LATIN_VOWELS = set("aeiou")


def _words(text: str) -> list[str]:
    return text.split()


def vowel_drop(text: str, lang: str, level: float, rng: random.Random) -> str:
    out = []
    for w in _words(text):
        if rng.random() < level and len(w) > 2:
            if DEV.search(w):
                w = "".join(c for c in w if c not in MATRAS) or w
            else:
                w = w[0] + "".join(c for c in w[1:] if c.lower() not in LATIN_VOWELS) or w
        out.append(w)
    return " ".join(out)


def typos(text: str, lang: str, level: float, rng: random.Random) -> str:
    out = []
    for w in _words(text):
        if rng.random() < level and len(w) > 3:
            i = rng.randrange(1, len(w) - 1)
            op = rng.choice(["swap", "delete", "double"])
            if op == "swap":
                w = w[:i] + w[i + 1] + w[i] + w[i + 2:]
            elif op == "delete":
                w = w[:i] + w[i + 1:]
            else:
                w = w[:i] + w[i] + w[i:]
        out.append(w)
    return " ".join(out)


LATIN_VARIANTS = [("aa", "a"), ("ee", "i"), ("oo", "u"), ("w", "v"), ("sh", "s"), ("ph", "f"), ("ai", "e"), ("au", "o"), ("z", "j"), ("q", "k")]
DEV_VARIANTS = [("ी", "ि"), ("ि", "ी"), ("ू", "ु"), ("ु", "ू"), ("ँ", "ं"), ("़", ""), ("ण", "न"), ("श", "स")]


def spelling(text: str, lang: str, level: float, rng: random.Random) -> str:
    out = []
    for w in _words(text):
        if rng.random() < level:
            pairs = DEV_VARIANTS if DEV.search(w) else LATIN_VARIANTS
            hits = [(a, b) for a, b in pairs if a in w]
            if hits:
                a, b = rng.choice(hits)
                w = w.replace(a, b, 1)
        out.append(w)
    return " ".join(out)


@lru_cache(maxsize=None)
def _lexicon(lang: str) -> dict:
    return json.loads((BACKEND / "content" / "lexicons" / f"{lang}.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def switch_table(lang: str) -> dict[str, str]:
    """Single-word terms of `lang` mapped to an English single-word term with the same slot effect."""
    if lang == "en":
        return {}
    en_by_set: dict[str, str] = {}
    for e in _lexicon("en")["entries"]:
        key = json.dumps(e.get("set", {}), sort_keys=True) + "|" + ",".join(e.get("sit", []))
        single = [t for t in e["terms"] if " " not in t and "*" not in t]
        if single and key not in en_by_set:
            en_by_set[key] = single[0]
    table = {}
    for e in _lexicon(lang)["entries"]:
        key = json.dumps(e.get("set", {}), sort_keys=True) + "|" + ",".join(e.get("sit", []))
        if key in en_by_set:
            for t in e["terms"]:
                if " " not in t and "*" not in t and not t.isascii() or (lang == "hinglish" and " " not in t and "*" not in t):
                    table.setdefault(t, en_by_set[key])
    # Everyday body and symptom words that the lexicons only list inside longer phrases.
    for k, v in COMMON_SWITCHES.get(lang, {}).items():
        table.setdefault(k, v)
    table = {k: v for k, v in table.items() if k != v and len(k) > 2}
    return table


COMMON_SWITCHES = {
    "hinglish": {"dard": "pain", "seene": "chest", "seena": "chest", "chhati": "chest", "saans": "breath", "sans": "breath",
                 "aag": "fire", "pani": "water", "garam": "hot", "haath": "hand", "aankh": "eye", "gala": "throat", "gale": "throat",
                 "khana": "food", "behosh": "unconscious", "kaata": "bit", "jal": "burnt", "pasina": "sweat"},
    "hi": {"दर्द": "pain", "सीने": "chest", "सीना": "chest", "छाती": "chest", "साँस": "breath", "सांस": "breath", "आग": "fire",
           "पानी": "water", "गरम": "hot", "हाथ": "hand", "आँख": "eye", "गले": "throat", "खाना": "food", "साँप": "snake",
           "सांप": "snake", "कुत्ते": "dog", "काटा": "bit", "पसीना": "sweat", "बेहोश": "unconscious"},
    "mr": {"छातीत": "chest", "छाती": "chest", "दुखतंय": "pain", "श्वास": "breath", "आग": "fire", "पाणी": "water", "गरम": "hot",
           "हात": "hand", "हातावर": "hand", "डोळ्यात": "eye", "घशात": "throat", "अन्न": "food", "साप": "snake",
           "कुत्रा": "dog", "चावला": "bit", "घाम": "sweat", "बेशुद्ध": "unconscious", "भाजला": "burnt"},
}


def code_switch(text: str, lang: str, level: float, rng: random.Random) -> str:
    table = switch_table(lang)
    out = []
    for w in _words(text):
        core = w.strip(",.!?।")
        if core in table and rng.random() < max(level * 2, level):  # few words qualify, so give each a fair chance
            w = w.replace(core, table[core])
        out.append(w)
    return " ".join(out)


def fragment(text: str, lang: str, level: float, rng: random.Random) -> str:
    ws = _words(text)
    kept = [w for w in ws if rng.random() >= level]
    return " ".join(kept) if kept else ws[0]


NOISES = {"vowel_drop": vowel_drop, "typos": typos, "spelling": spelling, "code_switch": code_switch, "fragment": fragment}


def mixed(text: str, lang: str, level: float, rng: random.Random) -> str:
    """All of the above at once, each at the given level."""
    for f in (code_switch, spelling, typos, vowel_drop, fragment):
        text = f(text, lang, level, rng)
    return text


NOISES["all combined"] = mixed
