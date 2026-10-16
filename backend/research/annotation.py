"""Tools for the hand-written test sets (docs/annotation/GUIDELINES.md).

    python -m research.annotation template                 # writes empty CSV sheets to docs/annotation/
    python -m research.annotation import queries_hi.csv    # checks a filled sheet and appends it to data/queries/test.jsonl
    python -m research.annotation kappa a.csv b.csv        # Cohen's kappa between two people's labels of the same messages
    python -m research.annotation negation neg_mr.csv      # checks a negation sheet and appends it to data/negation/test.jsonl

CSV is used so the sheets open in Excel or Google Sheets and diff cleanly in git.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

from .common import BACKEND, LANGS, REPO, SITUATIONS

SUBTYPES = {"unresponsive": {"path_a", "path_b", ""}, "bites": {"snake", "insect_sting", "scorpion", "dog", ""},
            "burns": {"fire_heat", "chemical_acid", "electrical", ""}}
URGENCY = {"emergency", "clinic", "home", ""}
QUERY_COLS = ["id", "lang", "text", "situation", "subtype", "urgency", "written_by", "labelled_by", "notes"]
NEG_COLS = ["id", "lang", "text", "slot", "gold", "written_by", "notes"]
NEG_GOLD = {"responsive": {"yes", "no", "uncertain"}, "breathing": {"normal", "abnormal", "absent", "uncertain"},
            "chest_pain": {"yes", "no", "uncertain"}, "power_off": {"yes", "no", "uncertain"}, "allergy_signs": {"yes", "no", "uncertain"}}
ANN = REPO / "docs" / "annotation"


def read(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def template():
    ANN.mkdir(parents=True, exist_ok=True)
    for lang in LANGS:
        with open(ANN / f"queries_{lang}.csv", "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(QUERY_COLS)
        with open(ANN / f"negation_{lang}.csv", "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(NEG_COLS)
    print("wrote empty sheets to", ANN)


def check_query(r: dict) -> list[str]:
    errs = []
    if r["lang"] not in LANGS:
        errs.append(f"lang must be one of {LANGS}")
    if not r["text"]:
        errs.append("text is empty")
    if r["situation"] not in SITUATIONS:
        errs.append(f"situation must be one of {SITUATIONS}")
    if r["subtype"] and r["subtype"] not in SUBTYPES.get(r["situation"], {""}):
        errs.append(f"subtype {r['subtype']!r} does not belong to {r['situation']}")
    if r["urgency"] not in URGENCY:
        errs.append("urgency must be emergency, clinic, home or empty (cannot be decided)")
    if not r.get("written_by"):
        errs.append("written_by is empty (who wrote the message)")
    return errs


def import_queries(path: str):
    rows = read(path)
    out = BACKEND / "data" / "queries" / "test.jsonl"
    existing = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()} if out.exists() else set()
    bad, new = [], []
    for i, r in enumerate(rows, start=2):
        errs = check_query(r)
        if r["id"] in existing:
            errs.append("id already in test.jsonl")
        if errs:
            bad.append(f"row {i} ({r.get('id')}): " + "; ".join(errs))
            continue
        new.append({"id": r["id"], "lang": r["lang"], "text": r["text"], "situation": r["situation"], "subtype": r["subtype"] or None,
                    "urgency": r["urgency"] or None, "slots": {}, "split": "test", "written_by": r["written_by"], "labelled_by": r.get("labelled_by", "")})
    if bad:
        print("Fix these rows first; nothing was imported:\n  " + "\n  ".join(bad))
        sys.exit(1)
    with open(out, "a", encoding="utf-8") as f:
        for r in new:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    c = Counter((r["lang"], r["situation"]) for r in new)
    print(f"imported {len(new)} messages into {out}")
    for (l, s), n in sorted(c.items()):
        print(f"  {l:9s} {s:14s} {n}")


def kappa(path_a: str, path_b: str):
    """Cohen's kappa for situation and urgency, matched by id."""
    from sklearn.metrics import cohen_kappa_score

    a = {r["id"]: r for r in read(path_a)}
    b = {r["id"]: r for r in read(path_b)}
    ids = sorted(set(a) & set(b))
    if not ids:
        print("no shared ids")
        return
    for field in ("situation", "urgency"):
        x = [a[i][field] or "none" for i in ids]
        y = [b[i][field] or "none" for i in ids]
        agree = sum(p == q for p, q in zip(x, y)) / len(ids)
        print(f"{field:10s} n={len(ids)} raw agreement={agree:.2f} Cohen's kappa={cohen_kappa_score(x, y):.2f}")
        for lang in LANGS:
            li = [i for i in ids if a[i]["lang"] == lang]
            if len(li) >= 10:
                print(f"   {lang:9s} n={len(li)} kappa={cohen_kappa_score([a[i][field] or 'none' for i in li], [b[i][field] or 'none' for i in li]):.2f}")
    print("Disagreements to discuss:")
    for i in ids:
        if (a[i]["situation"], a[i]["urgency"]) != (b[i]["situation"], b[i]["urgency"]):
            print(f"  {i}: {a[i]['text']!r}  A={a[i]['situation']}/{a[i]['urgency']}  B={b[i]['situation']}/{b[i]['urgency']}")


def import_negation(path: str):
    rows = read(path)
    out = BACKEND / "data" / "negation" / "test.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, dict] = {}
    bad = []
    for i, r in enumerate(rows, start=2):
        if r["lang"] not in LANGS or not r["text"]:
            bad.append(f"row {i}: lang/text")
            continue
        if r["slot"] not in NEG_GOLD or r["gold"] not in NEG_GOLD[r["slot"]]:
            bad.append(f"row {i}: slot must be one of {sorted(NEG_GOLD)} with gold one of its values")
            continue
        g = grouped.setdefault(r["id"], {"id": r["id"], "lang": r["lang"], "text": r["text"], "gold": {}, "frame": "owner",
                                         "kind": "hand-written", "written_by": r["written_by"]})
        g["gold"][r["slot"]] = r["gold"]
    if bad:
        print("Fix these rows first; nothing was imported:\n  " + "\n  ".join(bad))
        sys.exit(1)
    with open(out, "a", encoding="utf-8") as f:
        for g in grouped.values():
            f.write(json.dumps(g, ensure_ascii=False) + "\n")
    print(f"imported {len(grouped)} sentences into {out}; run python -m research.e6_negation")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    {"template": lambda: template(), "import": lambda: import_queries(*args), "kappa": lambda: kappa(*args),
     "negation": lambda: import_negation(*args)}.get(cmd, lambda: print(__doc__))()
