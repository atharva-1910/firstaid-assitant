"""Statistics and figures for the Data in Brief article (docs/data_article/).

    cd firstaid-assistant && backend/.venv/bin/python docs/data_article/analyze_data.py

Reads the repository's data files and writes figures/*.png and figures/stats.json.
"""
import glob
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
B = REPO / "backend"
OUT = HERE / "figures"
OUT.mkdir(parents=True, exist_ok=True)

LANGS = ["en", "hi", "hinglish", "mr"]
LN = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish", "mr": "Marathi"}
COL = {"en": "#2a78d6", "hi": "#eb6834", "hinglish": "#1baf7a", "mr": "#eda100"}
S1, S2, S3, MUT, INK, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#52514e", "#0b0b0b", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUT, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.titlesize": 9, "axes.titlelocation": "left"})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=220)
    plt.close(fig)


def load(p):
    return [json.loads(line) for line in open(p, encoding="utf-8") if line.strip()]


def label(ax, bars, fmt="{:.0f}", dy=0.5):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h), ha="center", va="bottom", fontsize=7, color=INK)


M = {}
# ------------------------------------------------------------------ procedure corpus
recs = {Path(f).stem: json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(str(B / "content/situations/*.json")))}
steps, branches, prim, anyc = [], [], Counter(), Counter()
for sid, r in recs.items():
    for bn, b in r["branches"].items():
        branches.append((sid, bn, len(b["steps"]), len(b.get("do_not", []))))
        for s in b["steps"]:
            steps.append((sid, bn, s))
            prim[s["source"]["doc"]] += 1
            for d in {s["source"]["doc"]} | {a["doc"] for a in s.get("also_in", [])}:
                anyc[d] += 1
M.update(n_steps=len(steps), n_branches=len(branches), n_do_not=sum(b[3] for b in branches), prim=dict(prim), any=dict(anyc),
         verified=sum(s["verified"] for *_, s in steps), page_filled=sum(s["source"].get("page") is not None for *_, s in steps),
         agreement=dict(Counter(s["agreement"] for *_, s in steps)), evidence=dict(Counter(s["evidence"] for *_, s in steps)),
         images=sum(bool(s.get("image")) for *_, s in steps), anims=sum(bool(s.get("animation")) for *_, s in steps),
         aids=dict(Counter(s["aid"]["kind"] for *_, s in steps if s.get("aid"))), checks=sum(bool(s.get("check")) for *_, s in steps),
         review={k: r["review_status"] for k, r in recs.items()},
         step_words={l: round(float(np.mean([len(s["text"][l].split()) for *_, s in steps if s["text"].get(l)])), 1) for l in LANGS},
         branches=[list(b) for b in branches])


def walk(o, acc):
    if isinstance(o, dict):
        if "en" in o and isinstance(o.get("en"), str) and o["en"]:
            acc.append(o)
        for v in o.values():
            walk(v, acc)
    elif isinstance(o, list):
        for v in o:
            walk(v, acc)


loc = []
for r in recs.values():
    walk(r, loc)
for f in ["questions.json", "strings.json"]:
    walk(json.load(open(B / "content" / f, encoding="utf-8")), loc)
myths = load(B / "content/myths.jsonl")
for m in myths:
    walk(m, loc)
M.update(loc_strings=len(loc), loc_filled={l: sum(bool(x.get(l)) for x in loc) for l in LANGS}, myths=len(myths),
         myth_src=dict(Counter(m.get("source") for m in myths)), questions=len(json.load(open(B / "content/questions.json"))["questions"]))
lex = {}
for l in LANGS:
    d = json.load(open(B / f"content/lexicons/{l}.json", encoding="utf-8"))
    lex[l] = {"entries": len(d["entries"]), "terms": sum(len(e["terms"]) for e in d["entries"]), "neg": len(d.get("negation_cues", [])),
              "unc": len(d.get("uncertainty_cues", [])), "actions": len(d.get("actions", []))}
M["lex"] = lex

# ------------------------------------------------------------------ message datasets
tr, dv = load(B / "data/queries/train.jsonl"), load(B / "data/queries/dev.jsonl")
suite, probe = load(B / "tests/safety_suite.jsonl"), load(B / "data/queries/probe_labelled.jsonl")
ver = load(B / "data/verifier/adversarial.jsonl")
M.update(train=len(tr), dev=len(dv), suite=len(suite), probe=len(probe), verifier=len(ver),
         urgency=dict(Counter(str(r["urgency"]) for r in tr + dv)), suite_em=sum(r["must_be_emergency"] for r in suite),
         suite_lang=dict(Counter(r["lang"] for r in suite)), suite_expect=dict(Counter(r["expect"] for r in suite)),
         probe_sit=dict(Counter(str(r.get("situation")) for r in probe)),
         ver_kind=dict(Counter(r["kind"] for r in ver)), ver_label=dict(Counter(r["label"] for r in ver)), ver_lang=dict(Counter(r["lang"] for r in ver)),
         slots=dict(Counter(k for r in tr + dv for k in r.get("slots", {})).most_common()),
         subtypes=dict(Counter(f'{r["situation"]}/{r["subtype"]}' for r in tr + dv if r.get("subtype"))))
e4 = json.load(open(REPO / "docs/research/e4_corpus.json", encoding="utf-8"))
sets = [("train (template)", "Templates", S1), ("safety suite", "Safety suite", S2), ("probe", "Probe", S3)]
M["e4"] = {sn: {l: {k: e4[sn][l][k] for k in ("mean_words", "vocab_per_24_messages", "vocabulary", "share_code_mixed", "cmi_mean")} for l in LANGS}
           for sn in ("train (template)", "dev (template)", "safety suite", "probe")}

# ------------------------------------------------------------------ figures
# Workflow (drawn with code)
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.axis("off")
ax.set_xlim(0, 100)
ax.set_ylim(0, 64)


def box(x, y, w, h, t, c, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5", fc=fc, ec=c, lw=1.2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7, color=INK)


def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=MUT, lw=1))


RAW, PROC, OUTC = ("#eb6834", "#fdeee6"), ("#2a78d6", "#e8f1fb"), ("#1baf7a", "#e5f6ef")
ax.text(1, 61, "RAW SOURCES", fontsize=8, fontweight="bold", color=RAW[0])
ax.text(37, 61, "PROCESSING", fontsize=8, fontweight="bold", color=PROC[0])
ax.text(72, 61, "DATA FILES", fontsize=8, fontweight="bold", color=OUTC[0])
box(1, 50, 28, 8, "5 guideline documents (G1–G5)\nIFRC, AHA ×2, ILCOR, NAPSE", *RAW)
box(1, 37, 28, 8, "Team's knowledge of\neveryday phrasing (4 languages)", *RAW)
box(1, 24, 28, 8, "Wikimedia Commons pictures\n+ team drawings", *RAW)
box(1, 11, 28, 8, "Procedure steps (row 1)", *RAW)
box(36, 50, 28, 8, "1 Read section, note page\n2 Rewrite step in plain words", *PROC)
box(36, 37, 28, 8, "3 Translate (hi, mr, hinglish)\n4 Word lists + templates", *PROC)
box(36, 24, 28, 8, "5 Resize, white background,\nWebP; record licence", *PROC)
box(36, 11, 28, 8, "6 Generate safe and dangerous\nrewordings of every step", *PROC)
box(71, 50, 28, 8, f"Procedure corpus\n{M['n_steps']} steps · 5 JSON files", *OUTC)
box(71, 37, 28, 8, f"Messages: {M['train'] + M['dev']:,} template\n+ {M['suite']} safety + {M['probe']} probe", *OUTC)
box(71, 24, 28, 8, f"{M['images']} step pictures,\n{M['anims']} animations", *OUTC)
box(71, 11, 28, 8, f"Verifier pairs\n{M['verifier']:,} (8 kinds)", *OUTC)
for y in (54, 41, 28, 15):
    arrow(29.8, y, 35.2, y)
    arrow(64.8, y, 70.2, y)
arrow(50, 49.5, 50, 45.6)
box(36, 0.5, 63, 7, "7 Check: JSON schema (every step needs a source),\nautomated tests, owners verify each step against the source", "#52514e", "#f2f2f0")
arrow(85, 10.5, 85, 7.4)
save(fig, "workflow.png")

# Steps per branch
fig, ax = plt.subplots(figsize=(6.6, 2.5))
names = [f"{s}\n{b}" if b != "default" else s for s, b, *_ in branches]
names = [n.replace("unresponsive", "unrespon-\nsive").replace("heart_attack", "heart\nattack").replace("chemical_acid", "chemical")
         .replace("insect_sting", "insect").replace("_", " ") for n in names]
bars = ax.bar(range(len(branches)), [b[2] for b in branches], color=S1, width=0.6, label="Steps")
label(ax, bars, dy=0.2)
ax.plot(range(len(branches)), [b[3] for b in branches], "o", color=S2, ms=5, label="Do-not rules")
ax.set_xticks(range(len(branches)), names, fontsize=6.5)
ax.set_ylabel("Count")
ax.set_ylim(0, 16)
ax.set_title(f"Steps and do-not rules per branch ({M['n_steps']} steps, {M['n_do_not']} do-not rules)")
ax.legend(frameon=False, fontsize=7)
save(fig, "steps.png")

# Sources
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.4))
G = ["G1", "G2", "G3", "G4", "G5", "UNSOURCED"]
GN = ["G1\nIFRC", "G2\nAHA/RC", "G3\nAHA BLS", "G4\nILCOR", "G5\nNAPSE", "none\nyet"]
x = np.arange(len(G))
w = 0.38
b1 = axs[0].bar(x - w / 2, [M["prim"].get(g, 0) for g in G], w * 0.92, color=S1, label="Main source")
b2 = axs[0].bar(x + w / 2, [M["any"].get(g, 0) for g in G], w * 0.92, color=S3, label="Main or supporting")
label(axs[0], b1, dy=0.6)
label(axs[0], b2, dy=0.6)
axs[0].set_xticks(x, GN, fontsize=6.5)
axs[0].set_ylabel("Steps")
axs[0].set_ylim(0, 62)
axs[0].legend(frameon=False, fontsize=6.5)
axs[0].set_title("a. Guideline cited by each step")
src = M["myth_src"]
ks = ["G1", "G2", "G5"]
b3 = axs[1].bar(range(3), [src.get(k, 0) for k in ks], color=[S1, S2, S3], width=0.55)
label(axs[1], b3, dy=0.15)
axs[1].set_xticks(range(3), ["G1 IFRC", "G2 AHA/RC", "G5 NAPSE"])
axs[1].set_ylim(0, 11)
axs[1].set_title(f"b. Sources of the {M['myths']} harmful-remedy entries")
save(fig, "sources.png")

# Messages: subtypes and urgency
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.7))
sub = ["unresponsive/path_a", "unresponsive/path_b", "bites/snake", "bites/dog", "bites/scorpion", "bites/insect_sting",
       "burns/fire_heat", "burns/electrical", "burns/chemical_acid"]
sn = ["unresp.: not breathing", "unresp.: breathing", "bite: snake", "bite: dog", "bite: scorpion", "bite: insect", "burn: fire/heat", "burn: electrical", "burn: chemical"]
cs = [S1, S1, S2, S2, S2, S2, S3, S3, S3]
vals = [M["subtypes"].get(k, 0) for k in sub]
axs[0].barh(sn[::-1], vals[::-1], color=cs[::-1], height=0.62)
for i, v in enumerate(vals[::-1]):
    axs[0].text(v + 4, i, str(v), va="center", fontsize=6.5)
axs[0].tick_params(axis="y", labelsize=6.5)
axs[0].set_xlim(0, 360)
axs[0].grid(axis="x", color=GRID)
axs[0].grid(axis="y", visible=False)
axs[0].set_title("a. Messages per subtype (train + dev)")
u = M["urgency"]
order = [("emergency", S2), ("clinic", S1), ("home", S3), ("None", MUT)]
vals = [u.get(k, 0) for k, _ in order]
axs[1].barh(["emergency", "clinic", "home", "no urgency\n(out of scope)"][::-1], vals[::-1], color=[c for _, c in order][::-1], height=0.55)
for i, v in enumerate(vals[::-1]):
    axs[1].text(v + 25, i, f"{v:,} ({v / sum(vals):.0%})", va="center", fontsize=7)
axs[1].set_xlim(0, 2700)
axs[1].grid(axis="x", color=GRID)
axs[1].grid(axis="y", visible=False)
axs[1].set_title("b. Urgency labels")
save(fig, "messages.png")

# Message length and variety by set
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.5))
for ax, key, title, yl, ylim in [(axs[0], "mean_words", "a. Average words per message", "Words", 14.5),
                                 (axs[1], "vocab_per_24_messages", "b. Distinct words in 24 messages", "Distinct words", 130)]:
    x = np.arange(4)
    w = 0.26
    for k, (sname, lab, c) in enumerate(sets):
        v = [float(e4[sname][l][key]) for l in LANGS]
        bb = ax.bar(x + (k - 1) * w, v, w * 0.92, color=c, label=lab)
        for bar, vv in zip(bb, v):
            ax.text(bar.get_x() + bar.get_width() / 2, vv + ylim * 0.01, f"{vv:.0f}" if vv > 20 else f"{vv:.1f}", ha="center", fontsize=6)
    ax.set_xticks(x, [LN[l] for l in LANGS])
    ax.set_ylabel(yl)
    ax.set_title(title)
    ax.set_ylim(0, ylim)
axs[0].legend(frameon=False, fontsize=6.5, ncol=3, loc="upper center")
save(fig, "language.png")

# Verifier pairs and curation status
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.5))
kinds = ["identity", "punctuation", "polite_form", "negation_removed", "negation_added", "antonym", "number_changed", "call_dropped"]
vals = [M["ver_kind"].get(k, 0) for k in kinds]
cols = [S3, S3, S3, S2, S2, S2, S2, S2]
axs[0].barh([k.replace("_", " ") for k in kinds][::-1], vals[::-1], color=cols[::-1], height=0.6)
for i, v in enumerate(vals[::-1]):
    axs[0].text(v + 5, i, str(v), va="center", fontsize=6.5)
axs[0].grid(axis="x", color=GRID)
axs[0].grid(axis="y", visible=False)
axs[0].set_xlim(0, 420)
axs[0].set_title(f"a. Verifier pairs ({M['verifier']:,}): green same, orange different", fontsize=8.5)
n = M["n_steps"]
stat = [("Page number filled", M["page_filled"]), ("Agreement checked", n - M["agreement"].get("unchecked", 0)),
        ("Evidence rated", n - M["evidence"].get("unchecked", 0)), ("Verified against source", M["verified"])]
axs[1].barh([s for s, _ in stat][::-1], [v for _, v in stat][::-1], color=S1, height=0.55)
axs[1].barh([s for s, _ in stat][::-1], [n - v for _, v in stat][::-1], left=[v for _, v in stat][::-1], color=GRID, height=0.55)
for i, (_, v) in enumerate(stat[::-1]):
    axs[1].text(n + 1, i, f"{v}/{n}", va="center", fontsize=7)
axs[1].set_xlim(0, n * 1.25)
axs[1].grid(False)
axs[1].set_title("b. Curation status of the steps")
save(fig, "verifier_status.png")

(OUT / "stats.json").write_text(json.dumps(M, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("figures and stats written to", OUT)
