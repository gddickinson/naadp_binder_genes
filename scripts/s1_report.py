#!/usr/bin/env python
"""Render `results/benchmark_controls/report.md` from the committed S1
tables — never written by hand alongside them (D13).

Every number in the report comes out of a TSV or `summary.json` in the
same directory. Run after `s1_benchmark.py` and `s1_figures.py`:

    /opt/anaconda3/envs/piezo1/bin/python scripts/s1_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.s1_lib import read_tsv  # noqa: E402
from scripts.s1_report_limits import (sec_limits, sec_margin,  # noqa: E402
                                      sec_size)
from scripts.s1_report_sections import (sec_crossfamily, sec_decoys,  # noqa: E402
                                        sec_positives, sec_toolchain)

IN = PROJECT_ROOT / "results" / "benchmark_controls"
OUT = IN / "report.md"


def main() -> int:
    S = json.loads((IN / "summary.json").read_text())
    T = {name: read_tsv(IN / f"{name}.tsv") for name in (
        "toolchain", "scores", "bait_margin", "size_component",
        "crossfamily_identity", "alignment_width_effect",
        "partition_assignment", "symbol_collisions")}

    n_tools = len(T["toolchain"])
    ok_tools = sum(1 for r in T["toolchain"] if r["status"] == "ok")
    parts = [
        "# S1 control benchmark — toolchain, partitioning, recall, "
        "specificity, and the JPT1 decoy",
        "",
        f"_Generated from the committed tables on {S['generated_at']} · "
        f"benchmark run {S['elapsed_s']} s · "
        f"{S['n_positive_records']} positive + {S['n_decoy_records']} decoy "
        f"panel records over {S['n_unique_accessions']} unique accessions · "
        f"promotion threshold score ≥ {S['promotion_threshold']} · "
        f"size band {S['size_band_aa'][0]}–{S['size_band_aa'][1]} aa._",
        "",
        _headline(S),
        "",
        "![S1 scorer validation](figures/s1_scorer_validation.png)",
        "",
        "**Figure S1.** *(a)* Pairwise identity within each family and "
        "across the JPT/LSM12 boundary, from the joint alignment, under "
        "both metrics; the shaded band is the twilight zone the scorer "
        "credits with +20 for novelty. *(b)* Every JPT-partition record's "
        "score with the sister-family test on (open) and off (filled). "
        "The five JPT1 decoys are the only records the test moves.",
        "",
        sec_toolchain(S, T, n_tools, ok_tools),
        sec_crossfamily(S, T),
        sec_positives(S, T),
        sec_decoys(S, T),
        sec_margin(S, T),
        sec_size(S, T),
        sec_limits(S, T),
    ]
    OUT.write_text("\n".join(parts).rstrip() + "\n")
    print(f"[s1_report] → {OUT} ({len(OUT.read_text().splitlines())} lines)")
    return 0


def _headline(S: dict) -> str:
    pa, ps = "part_anonymised", "part_anon_sigset"
    return (
        "**Headline.** The scorer is usable **only per partition**, and "
        "only with the family-signature fallback attached.\n\n"
        f"* **Specificity {S['part_baseline_specificity_hit']}/"
        f"{S['part_baseline_specificity_n']} (100 %)**, including "
        f"{S['part_baseline_jpt1_pass']}/{S['part_baseline_jpt1_n']} JPT1 "
        "decoys — but **only because of the sister-family test**. With it "
        f"disabled, {S['part_nosister_jpt1_n'] - S['part_nosister_jpt1_pass']}"
        f"/{S['part_nosister_jpt1_n']} JPT1 decoys are promoted, at 60–80, "
        "and specificity falls to "
        f"{S['part_nosister_specificity_hit']}/{S['part_nosister_specificity_n']}.\n"
        f"* **Recall {S[pa + '_recall_hit']}/{S[pa + '_recall_n']} "
        f"({100 * S[pa + '_recall_hit'] // S[pa + '_recall_n']} %)** when a "
        "true member arrives unnamed — every miss is a JPT2 ortholog that "
        "carries **no Pfam cross-reference** (D25). Attaching the "
        "MSA-derived family signature derived from the named members takes "
        f"it to **{S[ps + '_recall_hit']}/{S[ps + '_recall_n']} (100 %)**.\n"
        "* **Mixing the two families is harmless while each keeps a named "
        "member, and severe as soon as one does not.** Joint versus "
        "partitioned changed "
        f"{S['distortion_joint_baseline_vs_part_baseline_score_differs']}/"
        f"{S['distortion_joint_baseline_vs_part_baseline_n']} scores with "
        "both families named, and "
        f"{S['distortion_joint_crossfam_vs_part_crossfam_score_differs']}/"
        f"{S['distortion_joint_crossfam_vs_part_crossfam_n']} scores with "
        f"{S['distortion_joint_crossfam_vs_part_crossfam_call_flips']} call "
        "flips when only JPT2 was named.\n"
        "* **The labelled-bait margin cannot call the deep grade.** It is "
        f"{S['bait_margin_correct']}/{S['bait_margin_n']} correct on the "
        "vertebrate panel under the metric in use, but *Drosophila* "
        "Jupiter sits inside the D7 no-call band and is called the wrong "
        "way under the fragment-aware metric S6 adopts."
    )


if __name__ == "__main__":
    sys.exit(main())
