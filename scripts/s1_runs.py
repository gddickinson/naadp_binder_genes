"""S1 benchmark run harness — the four scorer arrangements, and the
InterPro/domain plumbing they share.

Kept separate from `s1_benchmark.py` so the driver reads as a list of
experiments rather than as wiring. Nothing here decides anything; every
number this produces is written to a table and interpreted in
`s1_report.py` (D13).

The arrangements:

  `joint`  — both families in ONE set and ONE alignment. This is the
             D14-violating arrangement, and reaching it requires
             `allow_cross_partition=True` explicitly. It exists so the
             distortion can be measured before the fix (session brief
             step 4: run it first, or the fix erases its own evidence).
  `parts`  — one alignment and one scorer pass per family, which is what
             D14 requires and what `run_partitioned_discovery` does.

Both take a `known` symbol list and a `size_points` value so the same
records can be re-scored under the D22 size-component variants.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.s1_lib import (MafftTracer, components, nearest_in_set,  # noqa: E402
                            nearest_known_identity, sister_margin, write_tsv)
from src.analysis.distance import identity_matrix  # noqa: E402
from src.analysis.pipeline import _label_for, analyse  # noqa: E402
from src.databases.interpro import batch_fetch_family_signatures  # noqa: E402
from src.discovery.candidates import (DiscoveryConfig,  # noqa: E402
                                      build_signature_set,
                                      discover_novel_paralogs)
from src.discovery.partition import run_partitioned_discovery  # noqa: E402
from src.utils.family import (FAMILY_PFAM_IDS, MAX_LENGTH_AA,  # noqa: E402
                              MIN_LENGTH_AA)

OUT_DIR = PROJECT_ROOT / "results" / "benchmark_controls"
DOMAIN_CACHE = OUT_DIR / "domain_hits.tsv"
PROMOTION_THRESHOLD = 40

#: The one member per partition that keeps its name in an anonymised run.
REFERENCE_ACCS = {"JPT": "Q9H910", "LSM12": "Q3MHD2"}
BOTH_KNOWN = ["JPT2", "LSM12"]


def load_domain_hits(accessions: list[str], log=print) -> dict[str, list]:
    """Live InterPro family-signature lookup, cached to TSV so the
    benchmark reruns offline. This is the production route — and it is
    what hands the JPT1 decoys their +20 domain point, by design."""
    from src.databases.interpro import DomainHit
    if DOMAIN_CACHE.exists():
        out: dict[str, list] = {a: [] for a in accessions}
        for line in DOMAIN_CACHE.read_text().splitlines()[1:]:
            parts = (line.split("\t") + ["", "", "", ""])[:5]
            acc, pfam, pfam_name, n_hits, coverage = parts
            if pfam:
                out.setdefault(acc, []).append(DomainHit(
                    accession=acc, pfam_id=pfam, pfam_name=pfam_name,
                    n_hits=int(n_hits or 1), coverage=float(coverage or 0.0)))
        missing = [a for a in accessions if a not in out]
        for a in missing:
            out[a] = []
        log(f"[domains] loaded {sum(len(v) for v in out.values())} hits from "
            f"cache {DOMAIN_CACHE.name}"
            + (f"; {len(missing)} accession(s) not in cache — delete it to "
               "re-query" if missing else ""))
        return out
    log(f"[domains] InterPro lookup for {len(accessions)} accessions "
        f"(~{len(accessions) * 1.2:.0f}s)…")
    hits = batch_fetch_family_signatures(accessions)
    rows = [{"accession": acc, "pfam_id": h.pfam_id, "pfam_name": h.pfam_name,
             "n_hits": h.n_hits, "coverage": f"{h.coverage:.4f}"}
            for acc in accessions for h in hits.get(acc, [])]
    write_tsv(DOMAIN_CACHE, rows,
              ["accession", "pfam_id", "pfam_name", "n_hits", "coverage"])
    n_with = sum(1 for a in accessions if hits.get(a))
    log(f"[domains] {n_with}/{len(accessions)} accessions carry >=1 family "
        f"Pfam ({','.join(FAMILY_PFAM_IDS)})")
    return hits


def uniq_by_accession(variants):
    """One record per accession — the `BOTH` decoys exist once per
    partition and must not be double-counted in a joint set."""
    seen, out = set(), []
    for v in variants:
        if v.accession in seen:
            continue
        seen.add(v.accession)
        out.append(v)
    return out


def label_map_for(variants) -> dict[str, str]:
    return {f"{v.source}|{v.accession}|{v.gene_symbol}": _label_for(v)
            for v in variants}


def run_joint(variants, known, domain_hits, size_points=15,
              config_overrides=None, log=print):
    """One alignment, one scorer pass, both families — D14-violating."""
    with MafftTracer() as tracer:
        analysis = analyse(variants, identity_threshold=0.4, use_mafft=True,
                           max_variants=len(variants),
                           reference_accession=REFERENCE_ACCS["JPT"])
    lmap = label_map_for(variants)
    sset = build_signature_set(variants, analysis.msa, lmap, known)
    cfg = DiscoveryConfig(known_paralogs=list(known),
                          allow_cross_partition=True,
                          size_component_points=size_points,
                          **(config_overrides or {}))
    report = discover_novel_paralogs(
        variants, cfg, analysis_label_for=lmap, distances=analysis.distances,
        domain_hits=domain_hits, signature_set=sset)
    log(f"[joint] MAFFT rc="
        f"{tracer.calls[0]['returncode'] if tracer.calls else 'NONE'}, "
        f"{analysis.n_analyzed} rows, width "
        f"{len(analysis.msa[0].aligned) if analysis.msa else 0}, "
        f"{len(report.candidates)} candidates, "
        f"{len(sset.signatures) if sset else 0} signature blocks")
    return {"analysis": analysis, "report": report, "label_map": lmap,
            "tracer": tracer, "signature_blocks": len(sset.signatures) if sset else 0}


def run_parts(variants, known, domain_hits, size_points=15,
              config_overrides=None, signature_sets=None, log=print):
    """One alignment and one scorer pass per family — what D14 requires."""
    overrides = dict(config_overrides or {})
    overrides["size_component_points"] = size_points
    with MafftTracer() as tracer:
        runs, unassigned = run_partitioned_discovery(
            variants, known, domain_hits=domain_hits, use_mafft=True,
            identity_threshold=0.4, config_overrides=overrides,
            signature_sets=signature_sets, log=log)
    return {"runs": runs, "unassigned": unassigned, "tracer": tracer}


def row(v, cand, run_name, partition, domain_hits, extra=None) -> dict:
    """One scored record, in the shape every S1 table shares."""
    out = {
        "run": run_name, "partition": partition,
        "panel_kind": v.raw.get("panel_kind", ""),
        "group": v.raw.get("panel_note", ""),
        "accession": v.accession,
        "gene_symbol": v.raw.get("named_symbol") or v.gene_symbol,
        "scored_as": v.gene_symbol,
        "species": v.species, "length_aa": v.length_aa or "",
        "in_band": str(bool(v.length_aa and
                            MIN_LENGTH_AA <= v.length_aa <= MAX_LENGTH_AA)),
        "n_family_pfam": len(domain_hits.get(v.accession, [])),
        "score": cand.score if cand else "n/a",
        "promoted": str(bool(cand and cand.score >= PROMOTION_THRESHOLD)),
        "components": components(cand),
        "id_to_nearest_known_pct": nearest_known_identity(cand),
        "nearest_in_set": nearest_in_set(cand),
        "sister_margin": sister_margin(cand),
    }
    out.update(extra or {})
    return out


def crossfamily_identity(analysis, variants, novelty_floor=0.20,
                         novelty_ceiling=0.40, log=print) -> list[dict]:
    """How similar does a JPT2 actually look to an LSM12?

    The decisive number for D14. The scorer's twilight-zone component
    fires when identity to the nearest known member falls in
    [floor, ceiling]; if cross-family identities land inside that window,
    a joint run hands every candidate +20 of family-specific evidence
    earned from an unrelated protein — and +20 outlier also satisfies the
    D3 promotion gate.

    Computed on the JOINT alignment (the only place cross-family cells
    exist) under both metrics: the full-alignment one the scorer uses
    today, and the fragment-aware `covered_only` one S6 adopts. The
    sibling ITPR project measured that the switch raises sister-family
    identities by ~0.15 — enough to move a class across the floor — so
    the same check is pre-registered here.
    """
    from src.utils.partitions import assign_partition
    if not (analysis and analysis.distances and analysis.msa):
        return []
    part_of_label = {}
    for v in variants:
        lbl = _label_for(v)
        key, _ = assign_partition(v)
        part_of_label[lbl] = key or "unassigned"
    covered = identity_matrix(analysis.msa, covered_only=True)
    rows = []
    for metric, dt in (("full alignment", analysis.distances),
                       ("covered columns only", covered)):
        buckets: dict[str, list[float]] = {}
        n = len(dt.labels)
        for i in range(n):
            pi = part_of_label.get(dt.labels[i], "unassigned")
            for j in range(i + 1, n):
                pj = part_of_label.get(dt.labels[j], "unassigned")
                if "unassigned" in (pi, pj):
                    continue
                # Sort the pair so JPT-vs-LSM12 and LSM12-vs-JPT are one
                # class, not two.
                a, b = sorted((pi, pj))
                cls = (f"within family ({a})" if pi == pj
                       else f"across families ({a} vs {b})")
                buckets.setdefault(cls, []).append(dt.identity[i][j])
        for cls, vals in sorted(buckets.items()):
            in_zone = sum(1 for v in vals
                          if novelty_floor <= v <= novelty_ceiling)
            rows.append({
                "metric": metric, "pair_class": cls, "n_pairs": len(vals),
                "min_identity": f"{min(vals):.4f}",
                "median_identity": f"{sorted(vals)[len(vals) // 2]:.4f}",
                "max_identity": f"{max(vals):.4f}",
                "n_in_twilight_zone": in_zone,
                "pct_in_twilight_zone": f"{100 * in_zone / len(vals):.1f}",
                "twilight_zone": f"{novelty_floor:.2f}-{novelty_ceiling:.2f}",
            })
            log(f"[crossfam] {metric:<21} {cls:<28} n={len(vals):<5} "
                f"median={rows[-1]['median_identity']} max={rows[-1]['max_identity']} "
                f"in-zone={in_zone} ({rows[-1]['pct_in_twilight_zone']}%)")
    return rows


def alignment_width_effect(variants, giant, log=print) -> list[dict]:
    """What one giant decoy does to a 190 aa family's alignment.

    Measured because the first run of this benchmark included titin
    (34,350 aa) and every alignment in it came out ~34,360 columns wide.
    Reported rather than quietly fixed: for a family of ~190 aa proteins
    the out-of-band decoys have to be bounded, and that is a panel-design
    rule the sibling projects never needed.
    """
    rows = []
    for label, vs in (("without giant", variants),
                      ("with giant", list(variants) + [giant])):
        a = analyse(vs, identity_threshold=0.4, use_mafft=True,
                    max_variants=len(vs))
        n = len(a.distances.labels) if a.distances else 0
        pairs = [a.distances.identity[i][j]
                 for i in range(n) for j in range(i + 1, n)]
        # The number that matters is not the panel mean — it is what the
        # giant does to the identities *between true family members*,
        # which is what every distance-based component reads.
        true_labels = {_label_for(v) for v in vs
                       if v.raw.get("panel_kind") == "positive"}
        idx = [i for i, lbl in enumerate(a.distances.labels)
               if lbl in true_labels] if a.distances else []
        true_pairs = [a.distances.identity[i][j]
                      for x, i in enumerate(idx) for j in idx[x + 1:]]
        rows.append({
            "panel": label, "n_rows": a.n_analyzed,
            "alignment_width": len(a.msa[0].aligned) if a.msa else 0,
            "mean_pairwise_identity": f"{sum(pairs) / len(pairs):.4f}" if pairs else "",
            "n_true_member_pairs": len(true_pairs),
            "mean_identity_true_members":
                f"{sum(true_pairs) / len(true_pairs):.4f}" if true_pairs else "",
            "min_identity_true_members":
                f"{min(true_pairs):.4f}" if true_pairs else "",
        })
        log(f"[width] {label}: {rows[-1]['alignment_width']} columns, "
            f"panel mean identity {rows[-1]['mean_pairwise_identity']}, "
            f"true-member mean {rows[-1]['mean_identity_true_members']}")
    return rows
