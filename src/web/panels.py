"""Result panels for the stage pages (S0 baseline, literature audit, S1 benchmark).

Each function returns {'panels': [...]} where a panel is {'id', 'title', 'note', 'provenance', ...data}. Values are
taken verbatim from committed tables (cells, rows, JSON keys); the only arithmetic is counting rows that match a stated
filter, and the filter is returned with the value so the reader can repeat it.
"""
from __future__ import annotations

import json

from . import committed as C
from .parse import delimiter_for, records, table

S0 = "results/s0_baseline/"
S1 = "results/benchmark_controls/"


def tsv(path: str) -> dict:
    return table(C.read_text(path), delimiter_for(path))


def recs(path: str) -> list[dict]:
    return records(C.read_text(path), delimiter_for(path))


def js(path: str):
    return json.loads(C.read_text(path))


def panel(pid: str, title: str, paths: list[str], note: str = "", **data) -> dict:
    return {"id": pid, "title": title, "note": note, "provenance": C.prov(*paths), **data}


def table_panel(pid: str, title: str, path: str, note: str = "") -> dict:
    return panel(pid, title, [path], note, table=tsv(path))


def figures_under(prefix: str) -> list[str]:
    return [p for p in C.tracked(prefix) if p.endswith(".png") and "/figures/" in p]


# --- S0 ----------------------------------------------------------------------------------------------------------
def baseline() -> dict:
    sym = recs(S0 + "symbol_table.tsv")
    species = list(dict.fromkeys(r["species"] for r in sym))
    symbols = list(dict.fromkeys(r["symbol_queried"] for r in sym))
    grid = {f'{r["species"]}|{r["symbol_queried"]}': {k: r[k] for k in (
        "result", "accession", "length_aa", "status", "pfam", "partition", "organism_id_result",
        "field_changes_call", "screen_note")} for r in sym}
    smoke = js(S0 + "smoke_test.json")
    smoke_rows = [{k: run.get(k) for k in ("partition", "preset", "scope", "n_variants", "n_sequences",
                                           "sources_requested", "sources_ok", "sources")}
                  for run in smoke.get("runs", [])]
    return {"stage": "S0", "panels": [
        panel("symbols", "Species x symbol grid (UniProt, taxonomy_id)", [S0 + "symbol_table.tsv"],
              "Each cell is the record the S0 screen picked for that symbol in that species. 'field changes call' "
              "marks cells where querying organism_id instead of taxonomy_id gives a different answer (D23).",
              species=species, symbols=symbols, grid=grid),
        table_panel("collision", "The HN1L symbol collision", S0 + "symbol_collision.tsv",
                    "gene_exact:HN1L returns two proteins; a longest-first pick takes the wrong one."),
        table_panel("scope", "Signature scope: Pfam vs its InterPro family entry (D25)", S0 + "signature_scope.tsv",
                    "pfam_fraction_of_interpro is the share of the InterPro entry's proteins the planned Pfam covers."),
        table_panel("recall", "Do the known members carry the planned signature?", S0 + "signature_recall.tsv"),
        table_panel("pfam", "Pfam protein counts", S0 + "pfam_counts.tsv"),
        table_panel("taxonomy", "Pfam lineage spread", S0 + "pfam_taxonomy.tsv"),
        table_panel("ensembl", "Ensembl endpoint probe (S0)", S0 + "ensembl_endpoint_probe.tsv"),
        table_panel("ensembl1", "Ensembl re-probe (S1)", S1 + "ensembl_reprobe.tsv"),
        panel("smoke", "App smoke test (per partition)", [S0 + "smoke_test.json"],
              table={"columns": list(smoke_rows[0]) if smoke_rows else [],
                     "rows": [[str(v) for v in r.values()] for r in smoke_rows], "n_rows": len(smoke_rows),
                     "truncated": False}),
    ]}


def literature() -> dict:
    meta = js(S0 + "lit_audit_meta.json")
    return {"stage": "S0", "meta": meta, "meta_provenance": C.prov(S0 + "lit_audit_meta.json"), "panels": [
        panel("claims", "Literature claims and verdicts", [S0 + "lit_claims.tsv"],
              "Every [lit] claim in the background document, with its verdict and supporting PMIDs.",
              claims=recs(S0 + "lit_claims.tsv")),
        panel("refs", "References (metadata fetched live from Europe PMC at S0)", [S0 + "references.tsv"],
              references=recs(S0 + "references.tsv")),
    ]}


# --- S1 ----------------------------------------------------------------------------------------------------------
RUN_NOTES = {
    "part_baseline": "per partition, members named",
    "part_anonymised": "per partition, members anonymised (hold-out)",
    "part_anon_sigset": "per partition, anonymised + MSA-signature fallback (D30)",
    "part_nosister": "per partition, sister-family test disabled",
    "part_crossfam": "per partition, one family with no named member",
    "joint_baseline": "both families in one set (D14-violating, measurement only)",
    "joint_anonymised": "joint, anonymised (measurement only)",
    "joint_crossfam": "joint, one family unnamed (measurement only)",
}


def benchmark() -> dict:
    s = js(S1 + "summary.json")
    runs = [{"run": r, "note": RUN_NOTES.get(r, ""),
             **{k: s.get(f"{r}_{k}") for k in ("recall_hit", "recall_n", "recall_protected", "specificity_hit",
                                                 "specificity_n", "jpt1_pass", "jpt1_n")}} for r in s.get("runs", [])]
    distortion = [{"comparison": k[len("distortion_"):-2], "n": s[k],
                   "score_differs": s[k[:-2] + "_score_differs"], "call_flips": s[k[:-2] + "_call_flips"],
                   "flipped": s[k[:-2] + "_flipped"]}
                  for k in s if k.startswith("distortion_") and k.endswith("_n")]
    scores = recs(S1 + "scores.tsv")
    keep = ("run", "partition", "panel_kind", "group", "accession", "gene_symbol", "species", "length_aa", "score",
            "promoted", "sister_margin")
    figs = figures_under(S1)
    return {"stage": "S1", "panels": [
        panel("runs", "Scorer runs: recall, specificity and the JPT1 decoys", [S1 + "summary.json"],
              "Straight from summary.json. jpt1_pass counts JPT1 decoys correctly kept below promotion.",
              runs=runs, threshold=s.get("promotion_threshold"), size_band=s.get("size_band_aa"),
              panel_sizes={"positive": s.get("n_positive_records"), "decoy": s.get("n_decoy_records"),
                           "unique": s.get("n_unique_accessions")}),
        panel("scores", "Every record's score, per run", [S1 + "scores.tsv"],
              "One dot per record. The dashed line is the promotion threshold from summary.json.",
              threshold=s.get("promotion_threshold"),
              rows=[{k: r.get(k, "") for k in keep} for r in scores]),
        panel("distortion", "Cross-family distortion: joint vs partitioned (D27)", [S1 + "summary.json"],
              rows=distortion),
        panel("identity", "Cross-family vs within-family identity (D28)", [S1 + "crossfamily_identity.tsv"],
              "Twilight zone 0.20-0.40. 'covered' rows score identity over mutually covered columns only.",
              rows=recs(S1 + "crossfamily_identity.tsv")),
        panel("margin", "Labelled-bait margin: closer to JPT2 or to JPT1?", [S1 + "bait_margin.tsv"],
              "margin = identity to the JPT2 bait minus identity to the JPT1 bait.",
              rows=recs(S1 + "bait_margin.tsv")),
        table_panel("size", "Size component +15 vs 0 (D22/D29)", S1 + "size_component.tsv"),
        table_panel("width", "Alignment-width effect of one giant record", S1 + "alignment_width_effect.tsv"),
        table_panel("partition", "Partition assignment of every panel record", S1 + "partition_assignment.tsv"),
        table_panel("domains", "InterPro domain hits", S1 + "domain_hits.tsv"),
        table_panel("missing", "Panel symbols that did not resolve (positives)", S1 + "panel_positives_missing.tsv"),
        table_panel("missing_d", "Panel symbols that did not resolve (decoys)", S1 + "panel_decoys_missing.tsv"),
        table_panel("toolchain", "Toolchain (versions every later task uses)", S1 + "toolchain.tsv"),
        panel("figure", "Figure S1 as committed", figs, figures=figs),
    ]}
