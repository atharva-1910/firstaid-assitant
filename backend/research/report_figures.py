"""Figures for the CCA1 report, each sized to fill at least half a page (6.5 x 4.6 in).

    python -m research.report_figures      # after python -m research.report and python -m research.report_extra

Every figure is plotted from the JSON results in docs/research/; nothing is drawn by hand.
Output: docs/report/figures/*.png, plus figures.json (figure id -> title, owner, caption).
"""
from __future__ import annotations

import json

import numpy as np

from .common import LANG_NAMES, LANGS, OUT, REPO, SITUATIONS, dev_rows, train_rows
from .plotting import GRID, INK2, SERIES, plt

FIGDIR = REPO / "docs" / "report" / "figures"
W, H = 6.5, 4.6
L4 = [LANG_NAMES[l] for l in LANGS]
SIT_SHORT = {"unresponsive": "Unresp.", "heart_attack": "Heart att.", "choking": "Choking", "bites": "Bites", "burns": "Burns", "out_of_scope": "Out of scope"}
CATALOG: dict[str, dict] = {}


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def save(fig, fid, title, owner):
    FIGDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGDIR / f"{fid}.png", dpi=220, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    CATALOG[fid] = {"title": title, "owner": owner}


def bars(ax, groups, series: dict, ylim=(0, 1.08), labels=True, fmt="{:.2f}", errors=None):
    n = len(series)
    w = 0.8 / n
    x = np.arange(len(groups))
    for i, (name, vals) in enumerate(series.items()):
        pos = x - 0.4 + w * (i + 0.5)
        yerr = None
        if errors and name in errors:
            yerr = [[v - e[0] for v, e in zip(vals, errors[name])], [e[1] - v for v, e in zip(vals, errors[name])]]
        b = ax.bar(pos, vals, w * 0.9, label=name, color=SERIES[i % len(SERIES)], yerr=yerr, error_kw={"ecolor": INK2, "elinewidth": 1, "capsize": 2})
        if labels:
            for rect, v in zip(b, vals):
                ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.015 * (ylim[1] - ylim[0]), fmt.format(v), ha="center", va="bottom", fontsize=7, color=INK2)
    ax.set_xticks(x, groups)
    ax.set_ylim(*ylim)
    ax.grid(axis="x", visible=False)


def legend_below(ax, ncol=3):
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=ncol, fontsize=8)


def heat(ax, mat, xlabels, ylabels, cmap="Blues", fmt="{:d}", vmax=None):
    m = np.asarray(mat, dtype=float)
    im = ax.imshow(m, cmap=cmap, vmin=0, vmax=vmax or m.max(), aspect="auto")
    ax.set_xticks(range(len(xlabels)), xlabels, rotation=30, ha="right")
    ax.set_yticks(range(len(ylabels)), ylabels)
    ax.grid(False)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m[i, j]
            ax.text(j, i, fmt.format(int(v)) if fmt == "{:d}" else fmt.format(v), ha="center", va="center", fontsize=8,
                    color="white" if v > 0.6 * (vmax or m.max()) else "#0b0b0b")
    return im


def corpus_figures():
    rows = train_rows() + dev_rows()
    fig, axes = plt.subplots(1, 2, figsize=(W, H))
    for i, l in enumerate(LANGS):
        lens = [len(r["text"].split()) for r in rows if r["lang"] == l]
        c = np.bincount(lens, minlength=25)[:25]
        axes[0].plot(range(25), c, color=SERIES[i], label=f"{LANG_NAMES[l]} (mean {np.mean(lens):.1f})")
    axes[0].set_xlabel("Words per message")
    axes[0].set_ylabel("Messages")
    axes[0].set_title("a. Message length, train + dev")
    axes[0].legend(fontsize=7, loc="upper right")
    urg = {"emergency": 0, "clinic": 0, "home": 0, "not decidable": 0}
    for r in rows:
        urg[r["urgency"] or "not decidable"] += 1
    axes[1].barh(list(urg)[::-1], list(urg.values())[::-1], color=SERIES[0])
    for y, v in enumerate(list(urg.values())[::-1]):
        axes[1].text(v + 20, y, str(v), va="center", fontsize=8, color=INK2)
    axes[1].set_title("b. Urgency labels, all languages")
    fig.subplots_adjust(wspace=0.55)
    axes[1].set_xlabel("Messages")
    axes[1].grid(axis="y", visible=False)
    save(fig, "corpus_stats", "Query corpus statistics: (a) message length per language, (b) urgency labels", "all")

    e4 = load("e4_corpus.json")
    fig, axes = plt.subplots(1, 2, figsize=(W, H))
    sets = ["train (template)", "safety suite", "probe"]
    names = ["Template (train)", "Safety suite (team-written)", "Probe"]
    bars(axes[0], L4, {n: [e4[s][l]["vocab_per_24_messages"] for l in LANGS] for n, s in zip(names, sets)}, ylim=(0, 135), fmt="{:.0f}")
    axes[0].set_title("a. Distinct words in 24 messages")
    axes[0].tick_params(axis="x", labelsize=8)
    axes[0].legend(fontsize=7, loc="upper center", ncol=1, bbox_to_anchor=(0.5, -0.1))
    cmi = [e4[s]["hinglish"]["cmi_mean"] for s in sets]
    mixed = [e4[s]["hinglish"]["share_code_mixed"] for s in sets]
    b = axes[1].bar(["Template", "Safety suite", "Probe"], cmi, color=SERIES[:3], width=0.6)
    for rect, c, m in zip(b, cmi, mixed):
        axes[1].text(rect.get_x() + rect.get_width() / 2, c + 0.15, f"{c:.1f}\n({100 * m:.0f}% mixed)", ha="center", fontsize=8, color=INK2)
    axes[1].set_ylim(0, max(cmi) * 1.35)
    axes[1].set_title("b. Hinglish Code-Mixing Index")
    axes[1].grid(axis="x", visible=False)
    save(fig, "corpus_diversity", "Corpus diversity: (a) vocabulary of 24 random messages per set, (b) Code-Mixing Index (Das & Gambäck, 2014)", "Soham")


def taneesha(e1, e2, x):
    fig, ax = plt.subplots(figsize=(W, H))
    v = [x["slot_f1"]["dev (template)"][l] for l in LANGS]
    bars(ax, L4, {"Slot F1": v})
    ax.set_ylabel("Micro-F1 over slot=value pairs")
    ax.set_title("Slot extraction F1 per language (dev set)")
    save(fig, "T1_slot_f1", "Taneesha: F1 slot extraction, micro-F1 per language on the dev set", "Taneesha")

    sets = [k for k in e1 if not k.startswith("test")]
    names = {"dev (template)": "Dev (template)", "safety suite (team-written)": "Safety suite", "probe (machine-drafted, silver labels)": "Probe"}
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, L4, {names[s]: [e1[s]["rules"][l]["situation_acc"][0] for l in LANGS] for s in sets},
         errors={names[s]: [e1[s]["rules"][l]["situation_acc"][1:] for l in LANGS] for s in sets})
    ax.set_ylabel("Situation accuracy (rules)")
    ax.set_title("Situation identification by the app, per language and evaluation set")
    legend_below(ax)
    save(fig, "T2_situation_sets", "Taneesha: situation accuracy of the app on template, safety-suite and probe messages (95% bootstrap intervals)", "Taneesha")

    probe = next(k for k in e1 if k.startswith("probe"))
    systems = [("rules before probe fixes (33802b7)", "Rules (before probe fixes)"), ("TF-IDF words + Naive Bayes", "TF-IDF + Naive Bayes"),
               ("TF-IDF words (1-2) + LR", "TF-IDF words + LR"), ("TF-IDF chars (2-5) + LR", "TF-IDF chars + LR")]
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, L4, {n: [e1[probe][s][l]["situation_acc"][0] for l in LANGS] for s, n in systems}, ylim=(0.5, 1.08))
    ax.set_ylabel("Situation accuracy")
    ax.set_title("Probe set: rules vs classical models")
    legend_below(ax, 2)
    save(fig, "T3_situation_models", "Taneesha: situation accuracy on the probe set, rules vs classical text classifiers", "Taneesha")

    c = x["confusion"]
    lab = [SIT_SHORT[s] for s in c["labels"]]
    fig, axes = plt.subplots(1, 2, figsize=(W, H))
    for ax, key, title in ((axes[0], "rules", "a. Rules (app)"), (axes[1], "model", "b. TF-IDF words + chars + LR")):
        heat(ax, c[key], lab, lab, vmax=max(max(r) for r in c["rules"]))
        ax.set_title(title)
        ax.set_xlabel("Predicted")
    axes[0].set_ylabel("True situation")
    axes[1].set_yticklabels([])
    save(fig, "T4_confusion", f"Taneesha: situation confusion matrices on {c['n']} safety-suite and probe messages", "Taneesha")

    fr = ["0.0", "0.05", "0.1", "0.25", "0.5", "1.0"]
    xs = [0, 5, 10, 25, 50, 100]
    fig, axes = plt.subplots(1, 2, figsize=(W, H), sharey=True)
    for ax, s, title in ((axes[0], "dev (template)", "a. Dev (template)"), (axes[1], "probe", "b. Probe")):
        for i, t in enumerate(["hi", "hinglish", "mr"]):
            ax.plot(xs, [e2["char"][t][f][s][0] for f in fr], marker="o", color=SERIES[i], label=LANG_NAMES[t])
        ax.set_xscale("symlog", linthresh=5)
        ax.set_xticks(xs, [f"{v}%" for v in xs], fontsize=7)
        ax.set_title(title)
        ax.set_xlabel("Target-language data added to English")
        ax.set_ylim(0, 1.03)
    axes[0].set_ylabel("Situation accuracy")
    axes[1].legend(fontsize=8, loc="lower right")
    save(fig, "T5_transfer", "Taneesha: cross-lingual transfer from English, situation accuracy as target-language training data is added", "Taneesha")


def atharva(e5, x):
    acc = x["langid"]["accuracy"]
    fig, axes = plt.subplots(1, 2, figsize=(W, H), sharey=True)
    for ax, s, title in ((axes[0], "safety suite", "a. Safety suite"), (axes[1], "probe", "b. Probe (short, misspelt)")):
        bars(ax, L4, {m: [acc[s][m][l] for l in LANGS] for m in ("word-list rules", "char n-gram model")}, ylim=(0.8, 1.04))
        ax.set_title(title)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel("Language identification accuracy")
    h, lb = axes[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=8)
    save(fig, "A1_langid", "Atharva: language identification accuracy, word-list rules vs trained character n-gram model", "Atharva")

    conf = x["langid"]["probe_confusion"]
    fig, axes = plt.subplots(1, 2, figsize=(W, H))
    for ax, m in zip(axes, ("word-list rules", "char n-gram model")):
        heat(ax, conf[m], L4, L4, cmap="Oranges", vmax=25)
        ax.set_title(m)
        ax.set_xlabel("Predicted language")
    axes[0].set_ylabel("True language")
    axes[1].set_yticklabels([])
    save(fig, "A2_langid_confusion", "Atharva: language identification confusion matrices on the 100-message probe set", "Atharva")

    cl = x["clarify"]
    fig, axes = plt.subplots(1, 2, figsize=(W, H))
    res = cl["resolution"]
    bars(axes[0], L4, {"Resolved within 2 questions": [res[l]["resolved"] / res[l]["ambiguous"] for l in LANGS]})
    for i, l in enumerate(LANGS):
        axes[0].text(i, 0.08, f"n={res[l]['ambiguous']}", ha="center", color="white", fontsize=8)
    axes[0].set_title("a. Resolved within 2 questions", fontsize=10)
    hw = cl["hand_written_asked"]
    share = [hw[l].get("question", 0) / sum(hw[l].values()) for l in LANGS]
    bars(axes[1], L4, {"Asked a question": share}, ylim=(0, 0.6))
    axes[1].set_title("b. Messages that got a question", fontsize=10)
    fig.subplots_adjust(wspace=0.35)
    for ax in axes:
        ax.tick_params(axis="x", labelsize=8)
    save(fig, "A3_clarify", "Atharva: F2 clarifying questions, (a) ambiguous queries resolved within two questions, (b) share of safety-suite and probe messages that received a question", "Atharva")

    hwk = "safety suite + probe"
    fig, ax = plt.subplots(figsize=(W, H))
    ax.plot([0, 1], [0, 1], color="#c3c2b7", linestyle="--", linewidth=1, label="Perfect calibration")
    for i, (sysk, name) in enumerate((("model", "TF-IDF model"), ("rules (app confidence)", "App (rule confidence)"))):
        b = e5[hwk][sysk]["bins"]
        ax.plot([t[3] for t in b], [t[4] for t in b], marker="o", color=SERIES[i], label=f"{name}, ECE = {e5[hwk][sysk]['ece']:.3f}")
        for t in b:
            ax.annotate(str(t[2]), (t[3], t[4]), textcoords="offset points", xytext=(4, -10), fontsize=6, color=SERIES[i])
    ax.set_xlabel("Mean confidence in bin")
    ax.set_ylabel("Accuracy in bin")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.05)
    ax.set_title("Reliability diagram, safety suite + probe (numbers = messages per bin)")
    ax.legend(fontsize=8, loc="upper left")
    save(fig, "A4_reliability", "Atharva: reliability diagram of situation confidence on safety-suite and probe messages", "Atharva")

    from .common import fit, probe_rows, safety_rows
    from .e5_calibration import risk_coverage

    rows = [r for r in safety_rows() + probe_rows() if r.get("situation")]
    m = fit("word+char", train_rows(), "situation")
    p = m.predict_proba([r["text"] for r in rows])
    conf = p.max(1)
    correct = (m.classes_[p.argmax(1)] == np.array([r["situation"] for r in rows])).astype(float)
    cov, risk, aurc = risk_coverage(conf, correct)
    fig, ax = plt.subplots(figsize=(W, H))
    ax.plot(cov, risk, color=SERIES[0], label=f"TF-IDF model (AURC = {aurc:.3f})")
    keep = (conf >= 0.75).mean()
    ax.axvline(keep, color=SERIES[1], linestyle="--", linewidth=1.5, label=f"Confidence ≥ 0.75: {100 * keep:.0f}% answered directly")
    ax.set_xlabel("Coverage (share answered without a question)")
    ax.set_ylabel("Error rate among answered messages")
    ax.set_title("Risk–coverage curve, safety suite + probe")
    ax.set_ylim(0, max(risk) * 1.15)
    ax.legend(fontsize=8, loc="upper left")
    save(fig, "A5_risk_coverage", "Atharva: risk–coverage curve; asking a question below 0.75 confidence keeps the error rate low", "Atharva")


def siddhi(e6, e7, x):
    d = e6["diagnostic (machine-drafted)"]
    variants = [("English rule (cue before word only)", "English rule"), ("current (3 tokens, language direction)", "Current (3 tokens, direction)"),
                ("ConText-style (whole clause)", "ConText-style"), ("proposed: current + clause-wide uncertainty", "Proposed")]
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, L4, {n: [d[v]["by_lang"][l]["accuracy"] for l in LANGS] for v, n in variants}, ylim=(0, 1.1))
    ax.set_ylabel("Fact-level accuracy")
    ax.set_title("Negation and uncertainty: cue-attachment rules per language")
    legend_below(ax, 2)
    save(fig, "S1_negation", "Siddhi: F3 negation and uncertainty accuracy per language for four cue-attachment rules", "Siddhi")

    allv = [("English rule (cue before word only)", "English rule"), ("window 1", "Window 1"), ("current (3 tokens, language direction)", "Current (3)"),
            ("window 6", "Window 6"), ("ConText-style (whole clause)", "ConText-style"), ("proposed: current + clause-wide uncertainty", "Proposed")]
    fig, ax = plt.subplots(figsize=(W, H))
    vals = [d[v]["by_lang"]["all"]["dangerous"] for v, _ in allv]
    b = ax.bar([n for _, n in allv], vals, color=[SERIES[1] if v > 0 else SERIES[2] for v in vals], width=0.6)
    for rect, v in zip(b, vals):
        ax.text(rect.get_x() + rect.get_width() / 2, v + 1, str(v), ha="center", fontsize=8, color=INK2)
    ax.set_ylabel("Dangerous errors (negated or uncertain fact read as reassuring)")
    ax.set_title("Dangerous negation errors, all four languages (260 sentences)")
    ax.tick_params(axis="x", labelsize=8)
    ax.grid(axis="x", visible=False)
    save(fig, "S2_dangerous", "Siddhi: dangerous negation errors for each cue-attachment rule", "Siddhi")

    from .negation_frames import FRAMES

    cur = d["current (3 tokens, language direction)"]["by_frame"]
    fids = list(FRAMES)
    mat = [[cur[f"{l}:{f}"] for l in LANGS] for f in fids]
    fig, ax = plt.subplots(figsize=(W, H + 0.6))
    heat(ax, mat, L4, [f"{f} {FRAMES[f][0]}" for f in fids], cmap="Blues", fmt="{:.1f}", vmax=1)
    ax.set_title("Current rule: accuracy by sentence frame")
    ax.tick_params(axis="y", labelsize=7)
    save(fig, "S3_frames", "Siddhi: accuracy of the current negation rule by sentence frame and language", "Siddhi")

    sn = x["safety_net"]
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, [f"{LANG_NAMES[l]}\n(read as {LANG_NAMES[sn[l]['forced_as']]})" for l in LANGS],
         {"Without safety net": [sn[l]["missed_plain"] / sn[l]["n"] for l in LANGS], "With cross-language safety net": [sn[l]["missed_net"] / sn[l]["n"] for l in LANGS]},
         ylim=(0, 1.1), fmt="{:.2f}")
    ax.set_ylabel("Share of emergencies missed")
    ax.set_title("Safety-suite emergencies read with the wrong language")
    ax.tick_params(axis="x", labelsize=8)
    legend_below(ax, 2)
    save(fig, "S4_safety_net", "Siddhi: emergencies missed when the language is guessed wrong, without and with the cross-language safety net", "Siddhi")

    v = e7["results"]
    kinds = ["negation_removed", "negation_added", "number_changed", "call_dropped", "antonym", "polite_form"]
    vers = [k for k in v if not k.startswith("exact")]
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, [k.replace("_", " ") + ("\n(safe: accept)" if k == "polite_form" else "") for k in kinds], {n: [v[n][k] for k in kinds] for n in vers}, ylim=(0, 1.12))
    ax.set_ylabel("Handled correctly (dangerous rejected / safe accepted)")
    ax.set_title(f"Step verifier test: {e7['pairs']} adversarial pairs, four languages")
    ax.tick_params(axis="x", labelsize=7)
    legend_below(ax, 3)
    save(fig, "S5_verifier", "Siddhi: adversarial test of lexical step verifiers; the baseline the mmBERT verifier must beat", "Siddhi")


def soham(e1, e3, e8):
    probe = next(k for k in e1 if k.startswith("probe"))
    show = [("rules before probe fixes (33802b7)", "Rules (before fixes)"), ("TF-IDF words + chars + LR", "Model"), ("hybrid: rules before fixes + model", "Hybrid (rules + model)")]
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, L4, {n: [e1[probe][s][l]["emergency_recall"][0] for l in LANGS] for s, n in show},
         errors={n: [e1[probe][s][l]["emergency_recall"][1:] for l in LANGS] for s, n in show}, ylim=(0.5, 1.1))
    ax.set_ylabel("Emergency recall")
    ax.set_title("Probe set: emergencies caught per language")
    legend_below(ax, 3)
    save(fig, "H1_recall", "Soham: emergency recall on the probe set; the model under the rules floor catches the emergencies the rules missed", "Soham")

    safety = next(k for k in e1 if k.startswith("safety"))
    systems = [("rules before probe fixes (33802b7)", "Rules (before fixes)"), ("TF-IDF words + Naive Bayes", "Naive Bayes"), ("TF-IDF words (1-2) + LR", "Words + LR"),
               ("TF-IDF chars (2-5) + LR", "Chars + LR"), ("TF-IDF words + chars + LR", "Words+chars + LR"), ("hybrid: rules before fixes + model", "Hybrid")]
    fig, axes = plt.subplots(1, 2, figsize=(W, H))
    for ax, key, title in ((axes[0], "missed_emergencies", "a. Missed emergencies (of 65)"), (axes[1], "false_alarm_rate", "b. False-alarm rate (of 20)")):
        vals = [e1[probe][s]["all"][key] if key == "missed_emergencies" else e1[probe][s]["all"][key][0] for s, _ in systems]
        b = ax.bar(range(len(systems)), vals, color=SERIES[0] if key.startswith("missed") else SERIES[1], width=0.65)
        for rect, val in zip(b, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + (0.2 if key.startswith("missed") else 0.01), f"{val:.0f}" if key.startswith("missed") else f"{val:.2f}", ha="center", fontsize=7, color=INK2)
        ax.set_xticks(range(len(systems)), [n for _, n in systems], fontsize=7, rotation=45, ha="right")
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
    save(fig, "H2_tradeoff", "Soham: probe set, missed emergencies against false alarms for each triage system", "Soham")

    hw = "safety suite + probe"
    comb = e3[hw]["all combined"]
    levels = ["0.0", "0.1", "0.2", "0.3", "0.5"]
    systems3 = list(comb["0.0"])
    fig, axes = plt.subplots(1, 2, figsize=(W, H), sharey=True)
    for ax, metric, title in ((axes[0], "emergency_recall", "a. Emergencies caught"), (axes[1], "situation_acc", "b. Situation accuracy")):
        for i, s in enumerate(systems3):
            hyb = s.startswith("hybrid")
            ax.plot([float(l) for l in levels], [comb[l][s][metric] for l in levels], marker="o", color=SERIES[i], linestyle="--" if hyb else "-", label=s)
        ax.set_title(title)
        ax.set_xlabel("Noise level (all noise types)")
        ax.set_ylim(0, 1.03)
    axes[0].set_ylabel("Share")
    h, lb = axes[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=8)
    save(fig, "H3_noise", "Soham: robustness of triage to realistic typing noise on safety-suite and probe messages", "Soham")

    noises = ["vowel_drop", "typos", "spelling", "code_switch", "fragment"]
    fig, ax = plt.subplots(figsize=(W, H))
    bars(ax, [n.replace("_", " ") for n in noises], {s: [e3[hw][n]["0.3"][s]["emergency_recall"] for n in noises] for s in ("rules", "model (chars)", "hybrid (rules + chars model)")}, ylim=(0, 1.12))
    ax.set_ylabel("Emergency recall at noise level 0.3")
    ax.set_title("Which kind of noise hurts which system")
    legend_below(ax, 3)
    save(fig, "H4_noise_types", "Soham: emergency recall by noise type at level 0.3", "Soham")

    fig, axes = plt.subplots(1, 2, figsize=(W, H), sharey=True)
    for ax, mname, title in ((axes[0], "word", "a. Word model"), (axes[1], "char", "b. Character model")):
        r = e8[mname]
        bars(ax, ["k = 1", "k = 2", "k = 3", "App F4\nwords"], {
            "Top-k attributed words deleted": [r["top1"]["comprehensiveness"], r["top2"]["comprehensiveness"], r["top3"]["comprehensiveness"], r["rule_trigger_words"]["model_comprehensiveness"]],
            "k random words deleted": [r["random1"]["comprehensiveness"], r["random2"]["comprehensiveness"], r["random3"]["comprehensiveness"], float("nan")],
        }, ylim=(0, 0.32))
        ax.set_title(title)
        ax.tick_params(axis="x", labelsize=8)
    axes[0].set_ylabel("Drop in P(emergency) (comprehensiveness)")
    h, lb = axes[0].get_legend_handles_labels()
    fig.legend(h, lb, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, fontsize=8)
    save(fig, "H5_faithfulness", "Soham: faithfulness of explanations, drop in emergency probability when highlighted words are deleted", "Soham")


def main():
    e1, e2, e3, e5, e6, e7, e8 = (load(f"{n}.json") for n in ("e1_models", "e2_transfer", "e3_robustness", "e5_calibration", "e6_negation", "e7_verifier", "e8_faithfulness"))
    x = load("report_extra.json")
    corpus_figures()
    taneesha(e1, e2, x)
    atharva(e5, x)
    siddhi(e6, e7, x)
    soham(e1, e3, e8)
    (FIGDIR / "figures.json").write_text(json.dumps(CATALOG, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(CATALOG), "figures in", FIGDIR)


if __name__ == "__main__":
    main()
