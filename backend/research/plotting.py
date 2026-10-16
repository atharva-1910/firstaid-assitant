"""One look for every figure in the report: white surface, recessive grid, the first validated
categorical slots in fixed order (blue, orange, aqua, then yellow, magenta)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "figure.facecolor": "#ffffff", "axes.facecolor": "#ffffff", "savefig.facecolor": "#ffffff",
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "legend.frameon": False,
    "lines.linewidth": 2, "lines.markersize": 6,
})


def grouped_bars(ax, groups: list[str], series: dict[str, list[float]], errors: dict[str, list[tuple[float, float]]] | None = None, ylim=(0, 1.05)):
    import numpy as np

    n = len(series)
    width = 0.8 / n
    x = np.arange(len(groups))
    for i, (name, vals) in enumerate(series.items()):
        pos = x - 0.4 + width * (i + 0.5)
        yerr = None
        if errors and name in errors:
            lo = [v - e[0] for v, e in zip(vals, errors[name])]
            hi = [e[1] - v for v, e in zip(vals, errors[name])]
            yerr = [lo, hi]
        ax.bar(pos, vals, width * 0.88, label=name, color=SERIES[i % len(SERIES)], yerr=yerr,
               error_kw={"ecolor": INK2, "elinewidth": 1, "capsize": 2})
    ax.set_xticks(x, groups)
    ax.set_ylim(*ylim)
    ax.grid(axis="x", visible=False)
    return ax


def legend_below(ax, ncol: int = 2):
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=ncol, fontsize=8)


def save(fig, name: str):
    from .common import FIG

    FIG.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return FIG / name
