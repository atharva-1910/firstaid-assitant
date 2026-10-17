"""Draws figures/M1_architecture.png: the system architecture and methodology flowchart for the report.
Run: python draw_architecture.py (needs matplotlib)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent / "figures" / "M1_architecture.png"
INK, MUT = "#0b0b0b", "#52514e"
BLUE, ORANGE, GREEN, GREY, YELLOW = ("#2a78d6", "#e8f1fb"), ("#eb6834", "#fdeee6"), ("#1baf7a", "#e5f6ef"), ("#52514e", "#f2f2f0"), ("#b88600", "#fff6dc")

fig, ax = plt.subplots(figsize=(7.6, 6.8))
ax.axis("off")
ax.set_xlim(0, 100)
ax.set_ylim(2, 100)


def box(x, y, w, h, text, style, size=7, bold=False):
    edge, fill = style
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.2", fc=fill, ec=edge, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, fontweight="bold" if bold else "normal")


def lane(y, h, label, style, center=False):
    edge, fill = style
    ax.add_patch(FancyBboxPatch((0.5, y), 99, h, boxstyle="round,pad=0.2,rounding_size=1.5", fc="white", ec=edge, lw=0.8, ls="--"))
    ax.text(57 if center else 1.8, y + h - 2.2, label, fontsize=7.5, fontweight="bold", color=edge, va="top", ha="center" if center else "left")


def arrow(x1, y1, x2, y2, text=None):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=MUT, lw=1))
    if text:
        ax.text((x1 + x2) / 2 + 1, (y1 + y2) / 2, text, fontsize=6, color=MUT, va="center")


# Lane 1: user and browser
lane(84, 15, "1  USER AND BROWSER  (React, frontend/src)", BLUE)
box(3, 86, 24, 8, "Bystander types or speaks\nEnglish · Hindi ·\nHinglish · Marathi", BLUE)
box(33, 86, 26, 8, "Home screen + mic\n(Web Speech API, speech.ts)", BLUE)
box(70, 86, 27, 8, "Screens (flow.ts): Call 112 →\nwarning → question → steps\n→ handover summary", BLUE)
arrow(27.5, 90, 32.5, 90)

# Lane 2: backend pipeline, one row left to right
lane(49, 33, "2  NLP PIPELINE  (FastAPI, backend/app/pipeline.py)", ORANGE, center=True)
steps = [
    ("① Normalise", "Unicode,\ndigits, tokens", "normalize.py"),
    ("② Language ID", "char n-gram\nmodel", "ngram_langid.py"),
    ("③ Extract facts", "F1 slots + F3\nnegation + net", "extract.py"),
    ("④ Rules floor", "19 rules; model\nmay only raise", "safety_rules.py"),
    ("⑤ Situation", "+ F2 question\nif unsure", "clarify.py"),
    ("⑥ Steps + F4", "verified text,\n'why' words", "explain.py"),
]
W, G, X0 = 14.6, 1.7, 2.6
for i, (head, body, f) in enumerate(steps):
    x = X0 + i * (W + G)
    box(x, 57, W, 16, "", ORANGE)
    ax.text(x + W / 2, 70.2, head, ha="center", va="center", fontsize=6.6, fontweight="bold")
    ax.text(x + W / 2, 64.6, body, ha="center", va="center", fontsize=6.3)
    ax.text(x + W / 2, 59.3, f, ha="center", va="center", fontsize=5.6, color=MUT, style="italic")
    if i < 5:
        arrow(x + W + 0.25, 65, x + W + G - 0.25, 65)
ax.text(50, 52.4, "The rules floor runs in every mode: a trained model can raise urgency but never lower it. No step text is generated.",
        ha="center", fontsize=6.4, color=MUT, style="italic")
arrow(40, 85.4, 10, 73.8, None)
ax.text(2.8, 76.6, "POST /api/analyze", fontsize=5.9, color=MUT, ha="left")
arrow(92.5, 73.8, 92.5, 85.4, None)
ax.text(91.6, 76.6, "JSON response", fontsize=5.9, color=MUT, ha="right")

# Lane 3: data the pipeline reads
lane(26, 21, "3  DATA READ AT START-UP  (backend/content, models/weights)", GREEN)
box(3, 28.5, 22, 10, "Procedure corpus\n5 JSON files, 68 cited\nsteps, 29 do-not rules", GREEN, size=6.6)
box(27, 28.5, 22, 10, "Word lists ×4\n(1,838 phrases) + 13\nharmful-remedy myths", GREEN, size=6.6)
box(51, 28.5, 22, 10, "Language model weights\n(481 KB JSON)\n+ 9 questions", GREEN, size=6.6)
box(75, 28.5, 22, 10, "Session memory\n(facts per session,\nkept 2 hours)", GREEN, size=6.6)
for x in (14, 38, 62, 86):
    arrow(x, 39.2, x, 48.6)

# Lane 4: offline methodology
lane(3, 21, "4  OFFLINE METHOD  (backend/research, scripts, training)", YELLOW)
box(3, 5.5, 22, 10, "Guidelines G1–G5 →\nsteps; templates →\n3,600 messages", YELLOW, size=6.4)
box(27, 5.5, 22, 10, "Test sets: safety suite\n103, probe 100, negation\n260, verifier 1,309", YELLOW, size=6.4)
box(51, 5.5, 22, 10, "Experiments E1–E8:\nrules vs models, transfer,\nnoise, calibration", YELLOW, size=6.4)
box(75, 5.5, 22, 10, "Results per language\n→ fixes to word lists\nand rules (tests: 461)", YELLOW, size=6.4)
for x in (25.5, 49.5, 73.5):
    arrow(x, 10.5, x + 1, 10.5)

fig.tight_layout()
fig.savefig(OUT, dpi=220)
print("wrote", OUT)
