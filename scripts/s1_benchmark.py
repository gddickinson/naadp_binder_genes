"""S1 control benchmark — is the discovery scorer a validated instrument
for a subject that is two unrelated families?

Mirrors the production wiring (`src/cli.py:run_headless`): live InterPro
domain lookup for every panel accession, `analyse(use_mafft=True)`, the
MSA-derived family-signature fallback, then the scorer. One deliberate
difference: `max_variants` is raised so every panel sequence enters the
MSA — this benchmarks the scorer, not the production truncation.

Six experiments, in this order:

  E0  alignment-width effect — what one giant decoy does to a 190 aa
      family's MSA. Run first because it decided the panel.
  E1  `joint_*` — both families in ONE set and ONE alignment. The
      D14-violating arrangement, run BEFORE the fix so it cannot erase
      its own evidence (session brief step 4).
  E2  `part_*` — one alignment and one scorer pass per family: what D14
      requires. E1 vs E2 on identical records is the distortion number.
  E3  `crossfam` — the arrangement D14's text actually describes: a joint
      set in which one family has **no named member**, so every one of
      its records is scored against an unrelated protein. This is where
      the distortion is expected to bite, and E1/E2 alone would miss it.
  E4  signature-fallback — does the MSA-derived signature set rescue the
      true positives that carry no Pfam cross-reference (the D25 gap)?
  E5  D22 — every score recomputed with the size component zeroed.
  E6  the sister test's contribution — the JPT1 decoys re-scored with
      `exclude_sister_family=False`.

`baseline` keeps every panel symbol; `anonymised` strips the name off
every true member except the human reference, so recall is measured on
records that look like what a genome sweep returns (see
`s1_lib.anonymise` for why a symbol hold-out degenerates here).

Writes tables only — `s1_report.py` renders the report from them (D13).

Run: /opt/anaconda3/envs/piezo1/bin/python scripts/s1_benchmark.py
Outputs → results/benchmark_controls/
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.s1_lib import (JPT1_BAIT_ACCS, JPT_BAIT_ACCS,  # noqa: E402
                            anonymise, bait_margins, write_tsv)
from scripts.s1_panels import (DECOY_SPEC, POSITIVE_SPEC,  # noqa: E402
                               fetch_panel, write_collisions)
from scripts.s1_runs import (BOTH_KNOWN, OUT_DIR,  # noqa: E402
                             PROMOTION_THRESHOLD, REFERENCE_ACCS,
                             alignment_width_effect, crossfamily_identity,
                             load_domain_hits, row, run_joint, run_parts,
                             uniq_by_accession)
from src.analysis.distance import identity_matrix  # noqa: E402
from src.discovery.partition import partition_table  # noqa: E402
from src.utils.family import (FAMILY_PFAM_IDS, MAX_LENGTH_AA,  # noqa: E402
                              MIN_LENGTH_AA)

#: Fetched only for the width experiment, never scored (see s1_panels).
GIANT_SPEC = [("TTN", 9606, "giant (width experiment)", "JPT")]


def _score_lookup(report):
    from scripts.s1_lib import score_lookup
    return score_lookup(report)


def _collect(rows, out, run_name, variants, report, partition, domain_hits):
    lookup = _score_lookup(report)
    for v in variants:
        rows.append(row(v, lookup(v), run_name, partition, domain_hits))
    return out


def main() -> int:
    t0, log = time.time(), print
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    positives = fetch_panel(POSITIVE_SPEC, "positive", OUT_DIR, log=log)
    decoys = fetch_panel(DECOY_SPEC, "decoy", OUT_DIR, log=log)
    write_collisions(OUT_DIR)
    panel = positives + decoys
    accs = sorted({v.accession for v in panel})
    domain_hits = load_domain_hits(accs, log=log)
    write_tsv(OUT_DIR / "partition_assignment.tsv",
              partition_table(uniq_by_accession(panel), domain_hits))

    keep = set(REFERENCE_ACCS.values())
    joint_named, joint_anon = uniq_by_accession(panel), None
    joint_anon = anonymise(joint_named, keep)
    part_named, part_anon = panel, anonymise(panel, keep)

    rows: list[dict] = []
    S: dict = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "promotion_threshold": PROMOTION_THRESHOLD,
        "size_band_aa": [MIN_LENGTH_AA, MAX_LENGTH_AA],
        "family_pfam_ids": list(FAMILY_PFAM_IDS),
        "reference_accessions": REFERENCE_ACCS,
        "jpt2_bait_accessions": JPT_BAIT_ACCS,
        "jpt1_bait_accessions": JPT1_BAIT_ACCS,
        "n_positive_records": len(positives), "n_decoy_records": len(decoys),
        "n_unique_accessions": len(accs),
    }

    # ---------- E0: what a giant decoy does to the alignment ----------
    log("\n[bench] === E0: alignment-width effect ===")
    giant = fetch_panel(GIANT_SPEC, "giant", OUT_DIR, log=log)
    jpt_named = [v for v in part_named
                 if v.raw.get("partition") == "JPT" and v.sequence]
    width_rows = alignment_width_effect(jpt_named, giant[0], log=log) \
        if giant else []
    write_tsv(OUT_DIR / "alignment_width_effect.tsv", width_rows)

    # ---------- E1: the joint (D14-violating) runs, first ----------
    joint = {}
    for name, vset in (("baseline", joint_named), ("anonymised", joint_anon)):
        log(f"\n[bench] === E1: joint_{name} (both families, one set) ===")
        joint[name] = run_joint(vset, BOTH_KNOWN, domain_hits, log=log)
        _collect(rows, None, f"joint_{name}", vset, joint[name]["report"],
                 "JOINT", domain_hits)
        S[f"joint_{name}_width"] = (len(joint[name]["analysis"].msa[0].aligned)
                                    if joint[name]["analysis"].msa else 0)
        S[f"joint_{name}_rows"] = joint[name]["analysis"].n_analyzed
        S[f"joint_{name}_signature_blocks"] = joint[name]["signature_blocks"]
    # E1b: what the joint alignment says a JPT2 and an LSM12 have in
    # common — the number D14 turns on.
    cf_rows = crossfamily_identity(joint["baseline"]["analysis"], joint_named,
                                   log=log)
    write_tsv(OUT_DIR / "crossfamily_identity.tsv", cf_rows)
    S["crossfamily_identity"] = cf_rows

    tr = joint["baseline"]["tracer"]
    S["mafft_argv"] = tr.calls[0]["argv"] if tr.calls else []
    S["mafft_returncode"] = tr.calls[0]["returncode"] if tr.calls else None
    S["mafft_ok"] = tr.ok()
    S["mafft_n_calls"] = len(tr.calls)
    (OUT_DIR / "mafft_trace.json").write_text(json.dumps(
        {"calls": tr.calls, "n_rows": S["joint_baseline_rows"],
         "alignment_width": S["joint_baseline_width"]}, indent=1))
    if not S["mafft_ok"]:
        log("[bench] FATAL: MAFFT was not invoked (or returned non-zero) — "
            "use_mafft=True fell back to the star alignment; benchmark void.")
        return 1

    # ---------- E2: the partitioned runs ----------
    parts, margin_rows = {}, []
    for name, vset in (("baseline", part_named), ("anonymised", part_anon)):
        log(f"\n[bench] === E2: part_{name} (one pass per family) ===")
        parts[name] = run_parts(vset, BOTH_KNOWN, domain_hits, log=log)
        S[f"part_{name}_mafft_calls"] = len(parts[name]["tracer"].calls)
        S[f"part_{name}_unassigned"] = len(parts[name]["unassigned"])
        for key, run in parts[name]["runs"].items():
            _collect(rows, None, f"part_{name}", run.variants, run.report,
                     key, domain_hits)
            S[f"part_{name}_{key}_width"] = (
                len(run.analysis.msa[0].aligned)
                if run.analysis and run.analysis.msa else 0)
            S[f"part_{name}_{key}_rows"] = (run.analysis.n_analyzed
                                            if run.analysis else 0)
            S[f"part_{name}_{key}_signature_blocks"] = run.signature_blocks
        margin_rows += _margins(parts[name]["runs"].get("JPT"), f"part_{name}")
    write_tsv(OUT_DIR / "bait_margin.tsv", margin_rows)

    # ---------- E3: the arrangement D14 actually describes ----------
    # One family named, the other not — so every LSM12 record's "nearest
    # known paralog" is a JPT2. This is the cross-family distortion in the
    # form it takes in a real census, and E1/E2 above do not produce it,
    # because both families kept a named member there.
    log("\n[bench] === E3: crossfam (only JPT2 named, both families in set) ===")
    cf_joint = run_joint(joint_anon, ["JPT2"], domain_hits, log=log)
    _collect(rows, None, "joint_crossfam", joint_anon, cf_joint["report"],
             "JOINT", domain_hits)
    cf_part = run_parts(part_anon, ["JPT2"], domain_hits, log=log)
    for key, run in cf_part["runs"].items():
        _collect(rows, None, "part_crossfam", run.variants, run.report, key,
                 domain_hits)

    # ---------- E4: does the signature fallback rescue the Pfam-less? ----
    # Production derives the family signature from *named* members and
    # applies it to unnamed candidates. Deriving it inside an anonymised
    # run leaves one named row and no PSSM, so the set is carried across.
    log("\n[bench] === E4: anonymised + signature set from named members ===")
    ssets = {}
    for key, run in parts["baseline"]["runs"].items():
        from src.discovery.candidates import build_signature_set
        from src.discovery.partition import known_for_partition
        ssets[key] = build_signature_set(
            run.variants, run.analysis.msa if run.analysis else [],
            run.label_map, known_for_partition(key, BOTH_KNOWN))
    sig = run_parts(part_anon, BOTH_KNOWN, domain_hits,
                    signature_sets=ssets, log=log)
    for key, run in sig["runs"].items():
        _collect(rows, None, "part_anon_sigset", run.variants, run.report,
                 key, domain_hits)
        S[f"part_anon_sigset_{key}_signature_blocks"] = run.signature_blocks

    # ---------- E5: D22 — the size component, zeroed ----------
    log("\n[bench] === E5: D22, size component zeroed ===")
    size_rows: list[dict] = []
    for name, vset in (("baseline", part_named), ("anonymised", part_anon)):
        zero = run_parts(vset, BOTH_KNOWN, domain_hits, size_points=0, log=log)
        for key, run in zero["runs"].items():
            l0 = _score_lookup(run.report)
            l15 = _score_lookup(parts[name]["runs"][key].report)
            for v in run.variants:
                c0, c15 = l0(v), l15(v)
                if c0 is None and c15 is None:
                    continue
                s0 = c0.score if c0 else None
                s15 = c15.score if c15 else None
                size_rows.append({
                    "run": f"part_{name}", "partition": key,
                    "panel_kind": v.raw.get("panel_kind", ""),
                    "group": v.raw.get("panel_note", ""),
                    "accession": v.accession,
                    "gene_symbol": v.raw.get("named_symbol") or v.gene_symbol,
                    "length_aa": v.length_aa or "",
                    "in_band": str(bool(v.length_aa and MIN_LENGTH_AA
                                        <= v.length_aa <= MAX_LENGTH_AA)),
                    "score_size15": s15 if s15 is not None else "n/a",
                    "score_size0": s0 if s0 is not None else "n/a",
                    "delta": (s0 - s15) if (s0 is not None and s15 is not None) else "",
                    "promoted_size15": str(bool(s15 and s15 >= PROMOTION_THRESHOLD)),
                    "promoted_size0": str(bool(s0 and s0 >= PROMOTION_THRESHOLD)),
                    "call_changed": str(bool(
                        s15 is not None and s0 is not None
                        and (s15 >= PROMOTION_THRESHOLD) != (s0 >= PROMOTION_THRESHOLD))),
                })
    write_tsv(OUT_DIR / "size_component.tsv", size_rows)

    # ---------- E6: what the sister test is worth ----------
    log("\n[bench] === E6: sister test disabled ===")
    nosis = run_parts(part_named, BOTH_KNOWN, domain_hits,
                      config_overrides={"exclude_sister_family": False},
                      log=log)
    for key, run in nosis["runs"].items():
        _collect(rows, None, "part_nosister", run.variants, run.report, key,
                 domain_hits)

    write_tsv(OUT_DIR / "scores.tsv", rows)
    _summarise(S, rows, margin_rows, size_rows, width_rows)
    S["elapsed_s"] = round(time.time() - t0, 1)
    (OUT_DIR / "summary.json").write_text(json.dumps(S, indent=1))
    log(f"\n[bench] {S['elapsed_s']}s → {OUT_DIR}")
    return 0


def _margins(jrun, run_name: str) -> list[dict]:
    """JPT2-vs-JPT1 labelled-bait margin for the JPT partition.

    A bait's own row is marked `bait` and excluded from the correctness
    count: with a single JPT2 bait, its self-identity is not available and
    its "identity to the nearest JPT2 bait" is 0 by construction.
    """
    if not (jrun and jrun.analysis and jrun.analysis.distances):
        return []
    lba = {v.accession: jrun.label_map[
        f"{v.source}|{v.accession}|{v.gene_symbol}"] for v in jrun.variants}
    full = bait_margins(jrun.analysis.distances, lba)
    cov = bait_margins(identity_matrix(jrun.analysis.msa, covered_only=True), lba)
    baits = set(JPT_BAIT_ACCS) | set(JPT1_BAIT_ACCS)
    out = []
    for v in jrun.variants:
        m = full.get(lba.get(v.accession, ""), {})
        if not m:
            continue
        mc = cov.get(lba.get(v.accession, ""), {})
        note = v.raw.get("panel_note", "")
        is_bait = v.accession in baits
        truth = ("bait" if is_bait else
                 "JPT1" if note.startswith("JPT1") else
                 "JPT2" if v.raw.get("panel_kind") == "positive" else "other")
        out.append({
            "run": run_name, "accession": v.accession,
            "gene_symbol": v.raw.get("named_symbol") or v.gene_symbol,
            "species": v.species, "length_aa": v.length_aa or "",
            "truth": truth, "panel_note": note,
            "id_to_jpt2_bait": f"{m['id_to_jpt2']:.3f}",
            "id_to_jpt1_bait": f"{m['id_to_jpt1']:.3f}",
            "margin": f"{m['margin']:+.3f}", "call": m["call"],
            "correct": "" if truth in ("other", "bait") else str(m["call"] == truth),
            "id_to_jpt2_bait_cov": f"{mc.get('id_to_jpt2', 0):.3f}",
            "id_to_jpt1_bait_cov": f"{mc.get('id_to_jpt1', 0):.3f}",
            "margin_cov": f"{mc.get('margin', 0):+.3f}",
            "call_cov": mc.get("call", ""),
            "correct_cov": "" if truth in ("other", "bait")
                           else str(mc.get("call") == truth),
        })
    return out


def _summarise(S, rows, margin_rows, size_rows, width_rows) -> None:
    """Per-run recall / specificity. `n/a` records — the named references,
    which the scorer treats as known members rather than candidates — are
    excluded from the recall denominator and counted separately, so a
    protected reference cannot read as a recall failure."""
    runs = sorted({r["run"] for r in rows})
    S["runs"] = runs
    for run in runs:
        rs = [r for r in rows if r["run"] == run]
        pos = [r for r in rs if r["panel_kind"] == "positive"]
        scored = [r for r in pos if r["score"] != "n/a"]
        neg = [r for r in rs if r["panel_kind"] == "decoy"]
        jpt1 = [r for r in neg if r["group"].startswith("JPT1")]
        S[f"{run}_recall_n"] = len(scored)
        S[f"{run}_recall_hit"] = sum(1 for r in scored if r["promoted"] == "True")
        S[f"{run}_recall_protected"] = len(pos) - len(scored)
        S[f"{run}_specificity_n"] = len(neg)
        S[f"{run}_specificity_hit"] = sum(1 for r in neg if r["promoted"] != "True")
        S[f"{run}_jpt1_n"] = len(jpt1)
        S[f"{run}_jpt1_pass"] = sum(1 for r in jpt1 if r["promoted"] != "True")
    scorable = [r for r in margin_rows if r["correct"]]
    S["bait_margin_n"] = len(scorable)
    S["bait_margin_correct"] = sum(1 for r in scorable if r["correct"] == "True")
    S["bait_margin_correct_covered"] = sum(1 for r in scorable
                                           if r["correct_cov"] == "True")
    S["size_rows"] = len(size_rows)
    S["size_calls_changed"] = sum(1 for r in size_rows if r["call_changed"] == "True")
    S["width_effect"] = width_rows
    # Joint vs partitioned, on identical records.
    by = {}
    for r in rows:
        by.setdefault(r["accession"], {})[r["run"]] = r
    for a, b in (("joint_baseline", "part_baseline"),
                 ("joint_anonymised", "part_anonymised"),
                 ("joint_crossfam", "part_crossfam")):
        diff = [acc for acc, d in by.items()
                if a in d and b in d and d[a]["score"] != d[b]["score"]]
        flip = [acc for acc, d in by.items()
                if a in d and b in d and d[a]["promoted"] != d[b]["promoted"]]
        S[f"distortion_{a}_vs_{b}_n"] = sum(1 for d in by.values()
                                            if a in d and b in d)
        S[f"distortion_{a}_vs_{b}_score_differs"] = len(diff)
        S[f"distortion_{a}_vs_{b}_call_flips"] = len(flip)
        S[f"distortion_{a}_vs_{b}_flipped"] = sorted(flip)


if __name__ == "__main__":
    sys.exit(main())
