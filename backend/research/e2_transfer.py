"""E2. Cross-lingual transfer: how much target-language data does each language need?

    python -m research.e2_transfer

Train on all English training data plus a fraction (0, 5, 10, 25, 50, 100%) of one target
language's training data, then test situation accuracy on that language. Three random
subsamples per fraction. Evaluated on the dev set (template) and on the probe set (short, misspelt, machine-drafted),
because template-to-template transfer flatters every method.

Classical character and word features cannot transfer from Latin to Devanagari at 0%, so the
0% point here measures how much the scripts share (nothing for Hindi and Marathi, a lot for
Hinglish). training/05_research_transformers.ipynb repeats the experiment with multilingual
sentence embeddings (LaBSE, BGE-M3), where the 0% point is real zero-shot transfer.
"""
from __future__ import annotations

import random

import numpy as np

from .common import LANG_NAMES, SEED, dev_rows, md_table, probe_rows, train_rows, write_json
from .plotting import SERIES, plt, save

FRACTIONS = [0.0, 0.05, 0.10, 0.25, 0.50, 1.0]
SEEDS = [SEED, SEED + 1, SEED + 2]
TARGETS = ["hi", "hinglish", "mr"]
KINDS = {"char": "chars (2-5)", "word": "words (1-2)"}


def run(kind: str, train: list[dict], test_sets: dict[str, list[dict]]) -> dict:
    from .common import make_model

    en = [r for r in train if r["lang"] == "en"]
    out = {}
    for tgt in TARGETS:
        pool = [r for r in train if r["lang"] == tgt]
        out[tgt] = {}
        for frac in FRACTIONS:
            accs = {name: [] for name in test_sets}
            for seed in SEEDS if 0 < frac < 1 else SEEDS[:1]:
                rng = random.Random(seed)
                extra = rng.sample(pool, int(round(frac * len(pool))))
                rows = en + extra
                m = make_model(kind)
                m.fit([r["text"] for r in rows], [r["situation"] for r in rows])
                for name, rows_t in test_sets.items():
                    t = [r for r in rows_t if r["lang"] == tgt and r.get("situation")]
                    pred = m.predict([r["text"] for r in t])
                    accs[name].append(float(np.mean([p == r["situation"] for p, r in zip(pred, t)])))
            out[tgt][frac] = {name: (float(np.mean(v)), float(np.std(v))) for name, v in accs.items()}
    return out


def main():
    train = train_rows()
    test_sets = {"dev (template)": dev_rows(), "probe": probe_rows()}
    results = {kind: run(kind, train, test_sets) for kind in KINDS}
    write_json("e2_transfer.json", {k: {t: {str(f): v for f, v in d.items()} for t, d in r.items()} for k, r in results.items()})

    md = ["# E2. Cross-lingual transfer (English + a fraction of the target language)", "",
          "Situation accuracy on the target language, mean over 3 subsamples. Classical features cannot cross scripts,",
          "so 0% for Hindi and Marathi is a floor, not zero-shot transfer; the Colab notebook runs the same curve with multilingual embeddings.", ""]
    for kind, label in KINDS.items():
        for name in test_sets:
            md += [f"**TF-IDF {label} + LR · {name}**", ""]
            md.append(md_table(["Target"] + [f"{int(f*100)}%" for f in FRACTIONS],
                               [[LANG_NAMES[t]] + [f"{results[kind][t][f][name][0]:.2f}" for f in FRACTIONS] for t in TARGETS]))
            md.append("")
    (write_json.__globals__["OUT"] / "e2_transfer.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.3), sharey=True)
    xs = [f * 100 for f in FRACTIONS]
    for ax, name in zip(axes, test_sets):
        for i, t in enumerate(TARGETS):
            m = [results["char"][t][f][name][0] for f in FRACTIONS]
            s = [results["char"][t][f][name][1] for f in FRACTIONS]
            ax.plot(xs, m, marker="o", color=SERIES[i], label=LANG_NAMES[t])
            ax.fill_between(xs, np.array(m) - s, np.array(m) + s, color=SERIES[i], alpha=0.12, linewidth=0)
        ax.set_xscale("symlog", linthresh=5)
        ax.set_xticks(xs, [f"{int(x)}%" for x in xs])
        ax.set_title(name)
        ax.set_xlabel("Target-language training data added to English")
        ax.set_ylim(0, 1.03)
    axes[0].set_ylabel("Situation accuracy")
    axes[1].legend(loc="lower right")
    fig.suptitle("Transfer from English, TF-IDF chars + LR", fontsize=11, fontweight="bold")
    save(fig, "e2_transfer.png")
    for t in TARGETS:
        print(t, " ".join(f"{results['char'][t][f]['probe'][0]:.2f}" for f in FRACTIONS))


if __name__ == "__main__":
    main()
