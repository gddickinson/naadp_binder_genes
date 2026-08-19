#!/usr/bin/env python
"""S1 figure — the two measurements the rest of the project rests on.

**A. The family boundary is not a distance.** Cross-family (JPT vs LSM12)
identities from the joint alignment, against within-family identities,
under both metrics. The twilight zone the scorer treats as evidence of
novelty is shaded. Under the full-alignment metric no cross-family pair
reaches it; under the fragment-aware metric S6 adopts, 13 % do — which is
why D14 is a rule and not a preference.

**B. The decoy is inside the family.** Every JPT-partition record's score
with and without the sister-family test. The JPT1 decoys carry JPT2's
Pfam and are promoted at 60-80 without it.

Reads the committed tables only (D13). Run after s1_benchmark.py:
    /opt/anaconda3/envs/piezo1/bin/python scripts/s1_figures.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import figstyle as fs  # noqa: E402

IN_DIR = PROJECT_ROOT / "results" / "benchmark_controls"
FIG_DIR = IN_DIR / "figures"
THRESHOLD = 40


def _read(name):
    with (IN_DIR / name).open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _panel_a(ax, rows):
    """Grouped bars: median and max identity per pair class per metric,
    with the twilight zone shaded across the axis."""
    import numpy as np

    metrics = ["full alignment", "covered columns only"]
    classes = sorted({r["pair_class"] for r in rows})
    # within-family classes first, then across
    classes.sort(key=lambda c: (c.startswith("across"), c))
    idx = {c: i for i, c in enumerate(classes)}
    width = 0.36
    colours = {"full alignment": fs.PARALOG["JPT2"],
               "covered columns only": fs.PARALOG["LSM12"]}

    ax.axhspan(0.20, 0.40, color=fs.GRID, zorder=0)
    ax.annotate("twilight zone:\nthe scorer reads this\nas novelty (+20)",
                xy=(0.02, 0.30), xycoords=("axes fraction", "data"),
                ha="left", va="center", fontsize=fs.FS_NOTE, color=fs.MUTED)

    for k, metric in enumerate(metrics):
        xs, meds, maxs = [], [], []
        for r in rows:
            if r["metric"] != metric:
                continue
            xs.append(idx[r["pair_class"]] + (k - 0.5) * width)
            meds.append(float(r["median_identity"]))
            maxs.append(float(r["max_identity"]))
        ax.bar(xs, meds, width=width * 0.9, color=colours[metric],
               label=f"{metric} — median", zorder=3)
        ax.scatter(xs, maxs, s=9, color=fs.INK, zorder=4,
                   label="maximum" if k == 0 else None)

    for r in rows:
        if r["metric"] != "covered columns only" or not r["pair_class"].startswith("across"):
            continue
        x = idx[r["pair_class"]] + 0.5 * width
        ax.annotate(f"max {float(r['max_identity']):.2f}\n"
                    f"{r['pct_in_twilight_zone']}% of {r['n_pairs']} pairs\n"
                    "reach the zone",
                    xy=(x, float(r["max_identity"])), xytext=(-4, 6),
                    textcoords="offset points", fontsize=fs.FS_NOTE,
                    color=fs.INK, ha="right", va="bottom")

    ax.set_xticks(range(len(classes)))
    ax.set_xticklabels([c.replace("within family ", "within ")
                         .replace("across families ", "across\n")
                        for c in classes])
    ax.set_ylabel("pairwise identity")
    ax.set_ylim(0, 1.12)
    ax.legend(loc="upper center", frameon=False, ncol=1,
              bbox_to_anchor=(0.55, 1.02))
    fs.despine(ax)
    fs.hgrid(ax)


def _panel_b(ax, scores):
    """JPT-partition scores with and without the sister-family test."""
    with_s = {r["accession"]: r for r in scores if r["run"] == "part_baseline"
              and r["partition"] == "JPT"}
    without = {r["accession"]: r for r in scores if r["run"] == "part_nosister"
               and r["partition"] == "JPT"}
    accs = [a for a in without
            if without[a]["score"] != "n/a" and a in with_s
            and with_s[a]["score"] != "n/a"]

    def kind(a):
        g = without[a]["group"]
        if g.startswith("JPT1"):
            return "JPT1"
        return "JPT2" if without[a]["panel_kind"] == "positive" else "other"

    accs.sort(key=lambda a: (kind(a) != "JPT1", -int(without[a]["score"])))
    ys = range(len(accs))
    colour = {"JPT1": fs.PARALOG["JPT1"], "JPT2": fs.PARALOG["JPT2"],
              "other": fs.FAINT}
    for y, a in enumerate(accs):
        s_no, s_yes = int(without[a]["score"]), int(with_s[a]["score"])
        c = colour[kind(a)]
        ax.plot([s_yes, s_no], [y, y], color=c, lw=1.0, zorder=2)
        ax.scatter([s_no], [y], s=16, color=c, zorder=3)
        ax.scatter([s_yes], [y], s=16, facecolor=fs.SURFACE, edgecolor=c,
                   linewidths=0.8, zorder=4)
    ax.axvline(THRESHOLD, color=fs.INK, lw=0.8, ls="--", zorder=1)
    ax.annotate("promotion threshold", xy=(THRESHOLD, 0.0),
                xycoords=("data", "axes fraction"), xytext=(4, 3),
                textcoords="offset points", fontsize=fs.FS_NOTE,
                color=fs.INK, ha="left", va="bottom")
    ax.set_yticks(list(ys))
    ax.set_yticklabels([f"{without[a]['gene_symbol']} "
                        f"{without[a]['species'].split()[0][:6]}."
                        for a in accs])
    ax.invert_yaxis()
    ax.set_xlabel("discovery score")
    ax.set_xlim(0, 100)
    handles = [
        ("JPT1 decoy (same Pfam, not a binder)", fs.PARALOG["JPT1"]),
        ("JPT2 / Jupiter-family true member", fs.PARALOG["JPT2"]),
        ("unrelated decoy", fs.FAINT),
    ]
    import matplotlib.lines as mlines
    ax.legend(handles=[mlines.Line2D([], [], color=c, marker="o", lw=1.0,
                                     markersize=3.6, label=lbl)
                       for lbl, c in handles],
              loc="center right", frameon=False,
              bbox_to_anchor=(1.0, 0.42))
    ax.annotate("filled = sister test off  ·  open = sister test on",
                xy=(0.5, 1.0), xycoords="axes fraction", xytext=(0, 10),
                textcoords="offset points",
                fontsize=fs.FS_NOTE, color=fs.MUTED, ha="center", va="bottom")
    fs.despine(ax)


def main() -> int:
    fs.use()
    import matplotlib.pyplot as plt

    cross = _read("crossfamily_identity.tsv")
    scores = _read("scores.tsv")
    fig, axes = plt.subplots(1, 2, figsize=(fs.W_FULL, 3.9),
                             gridspec_kw={"width_ratios": [1.0, 1.15]})
    _panel_a(axes[0], cross)
    _panel_b(axes[1], scores)
    fs.panel(axes[0], "a", "JPT and LSM12 are not comparable by distance")
    fs.panel(axes[1], "b", "the sister test is what excludes JPT1")
    fig.tight_layout()
    out = fs.save(fig, FIG_DIR / "s1_scorer_validation")
    print("[s1_figures] wrote " + ", ".join(str(p) for p in out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
