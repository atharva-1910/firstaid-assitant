"""E6. Negation and uncertainty: the 3-token window against alternatives (F3, owner Siddhi).

    python -m research.e6_negation

Same extractor, only the cue-attachment step changes:
  current          nearest term within 3 tokens; ties go to the language's usual direction
                   (before the word in English, after it in Hindi, Hinglish and Marathi)
  no direction     nearest term within 3 tokens, direction ignored
  English rule     cues only look forward (before the word), as English negation does
  window 1 / 6     the current rule with a 1- or 6-token window
  ConText-style    a cue covers every term in its direction up to a scope breaker or the end of
                   the sentence (Harkema et al., 2009), not only the nearest one

Data: the diagnostic set in research/negation_frames.py (65 sentences per language,
machine-drafted) and, when present, data/negation/test.jsonl written by the language owners.
Dangerous error = a negated or uncertain fact read as its affirmed value, or the reverse for a
safety fact ("not breathing" read as breathing normally).
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager

import numpy as np

from .common import BACKEND, LANG_NAMES, LANGS, jsonl, md_table, write_json
from .negation_frames import FRAMES, build
from .plotting import grouped_bars, legend_below, plt, save


def make_attach(window: int, direction: str, all_in_scope: bool = False, unc_clause: bool = False):
    from app import negation as N

    def attach(tokens, lex, matches, cues):
        result: dict[int, list] = {}
        for cue in cues:
            if unc_clause and cue.kind == "unc":
                # Proposed: uncertainty is about the whole clause, so it covers every safety fact in it, either side.
                from app.extract import SAFETY_SLOTS

                for mi, m in enumerate(matches):
                    entry = lex.entries[m.ref]
                    if not any(sl in SAFETY_SLOTS for sl in entry.get("set", {})):
                        continue
                    d = N._distance(cue, m)
                    if d is None:
                        continue
                    lo, hi = (cue.end, m.start) if d[1] == "before" else (m.end, cue.start)
                    if not N._blocked(tokens, lo, hi, lex.breakers):
                        result.setdefault(mi, []).append(cue)
                continue
            win = (window if cue.kind == "neg" else max(window, N.UNC_WINDOW)) if not all_in_scope else 10**6
            cands = []
            for mi, m in enumerate(matches):
                entry = lex.entries[m.ref]
                if cue.kind == "neg" and "neg" not in entry:
                    continue
                if cue.kind == "unc" and not entry.get("set"):
                    continue
                d = N._distance(cue, m)
                if d is None:
                    continue
                dist, side = d
                if dist > win:
                    continue
                if direction == "forward" and side != "before":
                    continue
                if all_in_scope and side != ("before" if lex.direction == "before" else "after"):
                    continue
                lo, hi = (cue.end, m.start) if side == "before" else (m.end, cue.start)
                if N._blocked(tokens, lo, hi, lex.breakers):
                    continue
                penalty = 0 if direction in ("none", "forward") or side == lex.direction else 1
                cands.append((dist, penalty, mi))
            if not cands:
                continue
            chosen = [c[2] for c in cands] if all_in_scope else [min(cands)[2]]
            for mi in chosen:
                result.setdefault(mi, []).append(cue)
        return result

    return attach


VARIANTS = {
    "current (3 tokens, language direction)": dict(window=3, direction="language"),
    "no direction preference": dict(window=3, direction="none"),
    "English rule (cue before word only)": dict(window=3, direction="forward"),
    "window 1": dict(window=1, direction="language"),
    "window 6": dict(window=6, direction="language"),
    "ConText-style (whole clause)": dict(window=3, direction="language", all_in_scope=True),
    "proposed: current + clause-wide uncertainty": dict(window=3, direction="language", unc_clause=True),
}


@contextmanager
def variant(**kw):
    from app import extract as X

    orig = X.attach_cues
    X.attach_cues = make_attach(**kw)
    try:
        yield
    finally:
        X.attach_cues = orig


AFFIRMED = {"breathing": "normal", "responsive": "yes", "chest_pain": "yes"}


def judge(row, ex) -> tuple[int, int, int]:
    """(facts, correct, dangerous) for one sentence."""
    facts = correct = danger = 0
    for slot, gold in row["gold"].items():
        facts += 1
        got = "uncertain" if slot in ex.uncertain and slot not in ex.slots else ex.slots.get(slot)
        correct += int(got == gold)
        if gold != AFFIRMED.get(slot) and got == AFFIRMED.get(slot):
            danger += 1  # a negated/uncertain fact read as reassuring
        if gold == AFFIRMED.get(slot) and got not in (None, gold, "uncertain"):
            danger += 0  # over-cautious reading: wrong, not dangerous
    return facts, correct, danger


def main():
    from app.extract import extract

    sets = {"diagnostic (machine-drafted)": build()}
    owner = BACKEND / "data" / "negation" / "test.jsonl"
    if owner.exists() and owner.read_text(encoding="utf-8").strip():
        sets = {"hand-written (owners)": jsonl(owner), **sets}
    results = {}
    for set_name, rows in sets.items():
        results[set_name] = {}
        for vname, kw in VARIANTS.items():
            agg = defaultdict(lambda: [0, 0, 0])
            frames = defaultdict(lambda: [0, 0])
            with variant(**kw):
                for r in rows:
                    f, c, d = judge(r, extract(r["text"], r["lang"]))
                    for k in (r["lang"], "all"):
                        a = agg[k]
                        a[0] += f
                        a[1] += c
                        a[2] += d
                    fr = frames[(r["lang"], r.get("frame", "?"))]
                    fr[0] += f
                    fr[1] += c
            results[set_name][vname] = {
                "by_lang": {k: {"facts": v[0], "accuracy": v[1] / v[0], "dangerous": v[2]} for k, v in agg.items()},
                "by_frame": {f"{l}:{fid}": v[1] / v[0] for (l, fid), v in frames.items()},
            }
    write_json("e6_negation.json", results)

    md = ["# E6. Negation and uncertainty (F3)", "",
          "Fact-level accuracy (each sentence states 1–2 facts). Dangerous = a negated or uncertain fact read as reassuring.", ""]
    for set_name in results:
        md += [f"## {set_name}", ""]
        md.append(md_table(["Variant"] + [LANG_NAMES[l] for l in LANGS] + ["All", "Dangerous errors"],
                           [[v] + [f"{results[set_name][v]['by_lang'][l]['accuracy']:.2f}" for l in LANGS + ["all"]]
                            + [results[set_name][v]["by_lang"]["all"]["dangerous"]] for v in VARIANTS]))
        md += ["", "**Current rule, by frame** (accuracy)", ""]
        cur = results[set_name]["current (3 tokens, language direction)"]["by_frame"]
        md.append(md_table(["Frame", "Kind"] + [LANG_NAMES[l] for l in LANGS],
                           [[fid, FRAMES[fid][0]] + [f"{cur.get(f'{l}:{fid}', float('nan')):.2f}" for l in LANGS] for fid in FRAMES]))
        md.append("")
    (write_json.__globals__["OUT"] / "e6_negation.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    diag = results["diagnostic (machine-drafted)"]
    show = ["English rule (cue before word only)", "current (3 tokens, language direction)", "ConText-style (whole clause)", "proposed: current + clause-wide uncertainty"]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    grouped_bars(ax, [LANG_NAMES[l] for l in LANGS], {s: [diag[s]["by_lang"][l]["accuracy"] for l in LANGS] for s in show})
    ax.set_ylabel("Fact accuracy")
    ax.set_title("Negation and uncertainty: cue attachment rules")
    legend_below(ax, 2)
    save(fig, "e6_negation.png")
    for v in VARIANTS:
        print(f"{v:42s}", " ".join(f"{diag[v]['by_lang'][l]['accuracy']:.2f}" for l in LANGS + ["all"]), "danger", diag[v]["by_lang"]["all"]["dangerous"])
    print({k: round(v, 2) for k, v in diag["current (3 tokens, language direction)"]["by_frame"].items() if v < 1})


if __name__ == "__main__":
    main()
