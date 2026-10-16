"""E4. Corpus statistics and the Code-Mixing Index.

    python -m research.e4_corpus

Per set and language: messages, distinct messages, mean words, vocabulary size, type-token
ratio, distinct-bigram ratio. For code-mixing, every word is tagged English or Indian-language
and the Code-Mixing Index of Das & Gambäck (2014) is computed per message:

    CMI = 100 * (1 - max_i(w_i) / (n - u))   if n > u, else 0

where w_i is the number of words in language i, n all words and u language-independent words
(numbers, punctuation). Word tagging: in Devanagari messages a Latin-script word is English; in
Hinglish a word is English if it is in an English vocabulary (English training messages and
English lexicon terms) and not a common romanised Hindi word. This is a lexicon tagger, so
treat CMI as an estimate.
"""
from __future__ import annotations

import json
import re
from collections import Counter

import numpy as np

from .common import BACKEND, LANG_NAMES, LANGS, dev_rows, md_table, probe_rows, safety_rows, test_rows, train_rows, write_json
from .plotting import SERIES, plt, save

TOKEN = re.compile(r"[\wऀ-ॿ]+", re.UNICODE)
LATIN = re.compile(r"^[A-Za-z]+$")
NUM = re.compile(r"^[\d०-९]+$")
# Romanised Hindi words that are also English spellings, or would be mistaken for English.
HINDI_ROMAN = {"me", "main", "mein", "hai", "he", "ho", "na", "to", "ki", "ke", "ka", "se", "par", "pe", "aur", "ye", "wo", "koi",
               "bhi", "kya", "ab", "jab", "tab", "kar", "raha", "rahi", "rahe", "gaya", "gayi", "gaye", "nahi", "ne", "ko", "hi", "bahut"}


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def english_vocab() -> set[str]:
    v = set()
    for r in train_rows():
        if r["lang"] == "en":
            v.update(tokens(r["text"]))
    lex = json.loads((BACKEND / "content" / "lexicons" / "en.json").read_text(encoding="utf-8"))
    for e in lex["entries"]:
        for t in e["terms"]:
            v.update(tokens(t.replace("*", "")))
    return v - HINDI_ROMAN


def tag(tok: str, lang: str, en_vocab: set[str]) -> str:
    if NUM.match(tok):
        return "u"
    if lang in ("hi", "mr"):
        return "en" if LATIN.match(tok) else "in"
    if lang == "hinglish":
        return "en" if tok in en_vocab else "in"
    return "en" if LATIN.match(tok) else "in"


def cmi(text: str, lang: str, en_vocab: set[str]) -> float:
    tags = [tag(t, lang, en_vocab) for t in tokens(text)]
    n, u = len(tags), tags.count("u")
    if n - u <= 0:
        return 0.0
    counts = Counter(t for t in tags if t != "u")
    return 100.0 * (1 - max(counts.values()) / (n - u))


def stats(rows: list[dict], lang: str, en_vocab: set[str]) -> dict:
    rs = [r for r in rows if r["lang"] == lang]
    if not rs:
        return {}
    toks = [tokens(r["text"]) for r in rs]
    flat = [t for ts in toks for t in ts]
    bigrams = [(a, b) for ts in toks for a, b in zip(ts, ts[1:])]
    cmis = [cmi(r["text"], lang, en_vocab) for r in rs]
    # Vocabulary of 24 random messages (the smallest set size), averaged over 50 draws: a size-matched comparison.
    rng = np.random.default_rng(13)
    k = min(24, len(rs))
    vocab24 = float(np.mean([len({t for i in rng.choice(len(rs), k, replace=False) for t in toks[i]}) for _ in range(50)]))
    return {
        "vocab_per_24_messages": vocab24,
        "messages": len(rs),
        "distinct_messages": len({r["text"].strip().lower() for r in rs}),
        "mean_words": float(np.mean([len(t) for t in toks])),
        "vocabulary": len(set(flat)),
        "type_token_ratio": len(set(flat)) / max(1, len(flat)),
        "distinct_bigram_ratio": len(set(bigrams)) / max(1, len(bigrams)),
        "cmi_mean": float(np.mean(cmis)),
        "cmi_mixed_only": float(np.mean([c for c in cmis if c > 0])) if any(c > 0 for c in cmis) else 0.0,
        "share_code_mixed": float(np.mean([c > 0 for c in cmis])),
    }


def main():
    en_vocab = english_vocab()
    sets = {"train (template)": train_rows(), "dev (template)": dev_rows(), "safety suite": safety_rows(), "probe": probe_rows()}
    if test_rows():
        sets["test (hand-written)"] = test_rows()
    results = {s: {l: stats(rows, l, en_vocab) for l in LANGS} for s, rows in sets.items()}
    write_json("e4_corpus.json", results)

    md = ["# E4. Corpus statistics and code-mixing", "",
          "Vocab per 24 msgs = distinct words in 24 random messages (size-matched; mean of 50 draws). Distinct bigrams = share of word pairs that are unique. CMI = Code-Mixing Index (Das & Gambäck 2014), 0 = one language, 50 = evenly mixed.", ""]
    rows = []
    for s, by in results.items():
        for l in LANGS:
            d = by[l]
            if d:
                rows.append([s, LANG_NAMES[l], d["messages"], d["distinct_messages"], f"{d['mean_words']:.1f}", d["vocabulary"],
                             f"{d['vocab_per_24_messages']:.0f}", f"{d['distinct_bigram_ratio']:.3f}", f"{d['cmi_mean']:.1f}",
                             f"{100 * d['share_code_mixed']:.0f}%"])
    md.append(md_table(["Set", "Language", "Messages", "Distinct", "Words/msg", "Vocabulary", "Vocab per 24 msgs", "Distinct bigrams", "CMI (mean)", "Code-mixed msgs"], rows))
    md += ["", "Template data repeats a few frames with different people and times, so its vocabulary and bigram variety are a fraction",
           "of the safety suite and probe of the same size; this is why template scores do not predict real-world accuracy.", ""]
    (write_json.__globals__["OUT"] / "e4_corpus.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
    show = ["train (template)", "safety suite", "probe"]
    import numpy as _np
    x = _np.arange(len(LANGS))
    w = 0.8 / len(show)
    for i, s in enumerate(show):
        axes[0].bar(x - 0.4 + w * (i + 0.5), [results[s][l].get("distinct_bigram_ratio", 0) for l in LANGS], w * 0.88, color=SERIES[i], label=s)
        axes[1].bar(x - 0.4 + w * (i + 0.5), [results[s][l].get("cmi_mean", 0) for l in LANGS], w * 0.88, color=SERIES[i], label=s)
    for ax, t in zip(axes, ("Distinct word pairs (share)", "Code-Mixing Index (mean)")):
        ax.set_xticks(x, [LANG_NAMES[l] for l in LANGS])
        ax.set_title(t)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(fontsize=8)
    save(fig, "e4_corpus.png")
    for r in rows:
        print(" | ".join(str(c) for c in r))


if __name__ == "__main__":
    main()
