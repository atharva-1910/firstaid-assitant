"""E3. Robustness to messy typing: rules vs models vs hybrid as noise increases.

    python -m research.e3_robustness

Noise types are in research/noise.py. Evaluated on the safety-suite and probe messages (203 messages, 3 noise seeds) and on a 240-message sample of the template dev set.
Reported: situation accuracy and emergency recall (share of true emergencies still flagged).
"""
from __future__ import annotations

import random

import numpy as np

from .common import LANGS, SEED, dev_rows, fit, is_emergency, md_table, probe_rows, rules_predict, safety_rows, train_rows, write_json
from .noise import NOISES
from .plotting import SERIES, plt, save

LEVELS = [0.0, 0.1, 0.2, 0.3, 0.5]
SYSTEMS = ["rules", "model (chars)", "model (words)", "hybrid (rules + chars model)"]


def sample_dev(n_per_lang: int = 60) -> list[dict]:
    rng = random.Random(SEED)
    rows = dev_rows()
    out = []
    for l in LANGS:
        out += rng.sample([r for r in rows if r["lang"] == l], n_per_lang)
    return out


def evaluate(rows, texts, models) -> dict[str, dict[str, float]]:
    char_s, char_u, word_s, word_u = models
    rules = [rules_predict(t) for t in texts]
    em_i = list(char_u.classes_).index("emergency")
    cs, cu = char_s.predict(texts), char_u.predict_proba(texts)[:, em_i] >= 0.5
    ws, wu = word_s.predict(texts), word_u.predict_proba(texts)[:, list(word_u.classes_).index("emergency")] >= 0.5
    preds = {
        "rules": [(r["situation"], r["emergency"]) for r in rules],
        "model (chars)": list(zip(cs, cu)),
        "model (words)": list(zip(ws, wu)),
        "hybrid (rules + chars model)": [(r["situation"], r["emergency"] or bool(m)) for r, m in zip(rules, cu)],
    }
    out = {}
    for name, p in preds.items():
        sit = [g["situation"] == s for g, (s, _) in zip(rows, p) if g.get("situation")]
        rec = [e for g, (_, e) in zip(rows, p) if is_emergency(g)]
        fa = [e for g, (_, e) in zip(rows, p) if is_emergency(g) is False]
        out[name] = {"situation_acc": float(np.mean(sit)), "emergency_recall": float(np.mean(rec)), "missed": int(len(rec) - sum(rec)),
                     "false_alarm": float(np.mean(fa)) if fa else float("nan")}
    return out


def main():
    train = train_rows()
    models = (fit("char", train, "situation"), fit("char", train, "urgency"), fit("word", train, "situation"), fit("word", train, "urgency"))
    sets = {"safety suite + probe": (safety_rows() + probe_rows(), [SEED, SEED + 1, SEED + 2]),
            "dev sample (template)": (sample_dev(), [SEED])}
    results: dict = {}
    for set_name, (rows, seeds) in sets.items():
        results[set_name] = {}
        for noise, f in NOISES.items():
            results[set_name][noise] = {}
            for level in LEVELS:
                runs = []
                for seed in seeds:
                    rng = random.Random(seed)
                    texts = [f(r["text"], r["lang"], level, rng) if level else r["text"] for r in rows]
                    runs.append(evaluate(rows, texts, models))
                    if level == 0:
                        break
                results[set_name][noise][level] = {
                    s: {k: float(np.mean([r[s][k] for r in runs])) for k in ("situation_acc", "emergency_recall", "missed", "false_alarm")} for s in SYSTEMS
                }
            print(set_name, noise, {s: (round(results[set_name][noise][0.3][s]["emergency_recall"], 2), round(results[set_name][noise][0.3][s]["false_alarm"], 2), round(results[set_name][noise][0.3][s]["situation_acc"], 2)) for s in SYSTEMS})
    write_json("e3_robustness.json", {s: {n: {str(l): v for l, v in d.items()} for n, d in r.items()} for s, r in results.items()})

    md = ["# E3. Robustness to noise", "",
          "Mean over 3 noise seeds (safety suite + probe) or 1 seed (dev sample). Level = chance that each word is changed.", ""]
    for set_name in sets:
        for metric, label in (("emergency_recall", "Emergency recall"), ("false_alarm", "False-alarm rate"), ("situation_acc", "Situation accuracy")):
            md += [f"**{label} at level 0.3 · {set_name}**", ""]
            md.append(md_table(["Noise"] + SYSTEMS, [[n] + [f"{results[set_name][n][0.3][s][metric]:.2f}" for s in SYSTEMS] for n in NOISES]))
            md.append("")
        md += [f"**All noise combined, by level · {set_name}** (emergency recall / situation accuracy)", ""]
        md.append(md_table(["Level"] + SYSTEMS, [[f"{l:.1f}"] + [f"{results[set_name]['all combined'][l][s]['emergency_recall']:.2f} / {results[set_name]['all combined'][l][s]['situation_acc']:.2f}" for s in SYSTEMS] for l in LEVELS]))
        md.append("")
    (write_json.__globals__["OUT"] / "e3_robustness.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    plot(results)


def plot(results):
    """Figure from the results (also callable on the saved JSON, whose levels are strings)."""
    hw = "safety suite + probe"
    comb = {float(k): v for k, v in results[hw]["all combined"].items()}
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), sharey=True)
    for ax, metric, title in zip(axes, ("emergency_recall", "situation_acc"), ("Emergencies caught", "Situation accuracy")):
        for i, s in enumerate(SYSTEMS):
            hybrid = s.startswith("hybrid")
            ax.plot(LEVELS, [comb[l][s][metric] for l in LEVELS], marker="o", color=SERIES[i], label=s + (" (situation from rules)" if hybrid else ""),
                    linestyle="--" if hybrid else "-", zorder=3 if hybrid else 2)
        ax.set_title(title)
        ax.set_xlabel("Noise level (all noise types combined)")
        ax.set_ylim(0, 1.03)
    axes[0].set_ylabel("Share")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=8, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("Safety-suite and probe messages under increasing noise", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    save(fig, "e3_robustness.png")


if __name__ == "__main__":
    main()
