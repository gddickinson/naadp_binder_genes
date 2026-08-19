#!/usr/bin/env python
"""S0 step 4 — re-derive every `[db]` number in `docs/naadp_binder_background.md`.

Writes, into `results/s0_baseline/`:

  symbol_table.tsv          the species x {JPT2, LSM12, JPT1} table, re-queried
  symbol_table_raw.tsv      EVERY hit each query returned, before screening
  symbol_collision.tsv      the gene_exact:HN1L trap, re-measured
  pfam_counts.tsv           the API's own count per family Pfam (S2's denominator)
  pfam_taxonomy.tsv         per-lineage distribution per family Pfam
  snapshot_meta.json        date, tool versions, one row per query issued

Nothing here needs the bulk data root: the whole snapshot is a few hundred
API rows. Run:  python scripts/s0_db_snapshot.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.s0_lib import (  # noqa: E402
    gene_exact_query, interpro_pfam_count, interpro_taxonomy, pick_best,
    uniprot_query, write_tsv,
)
from src.utils.family import (  # noqa: E402
    CENSUS_PFAM_IDS, FAMILY_PARTITIONS, SYMBOL_COLLISIONS,
)

OUT = ROOT / "results" / "s0_baseline"
LIVE = ROOT / "results" / "session_live.json"

#: The species panel of the background document's table, in its order.
SPECIES = [
    ("human", 9606), ("mouse", 10090), ("chicken", 9031),
    ("X. tropicalis", 8364), ("zebrafish", 7955), ("fly", 7227),
    ("worm", 6239), ("Arabidopsis", 3702), ("yeast", 4932),
    ("Dictyostelium", 44689),
]

#: Which partition each queried symbol belongs to, hence which Pfam and band
#: screen it (D14: the screen is per partition, never pooled).
SYMBOLS = [
    ("JPT2", "JPT"), ("LSM12", "LSM12"), ("JPT1", "JPT"),
]

QUERY_LOG: list[dict] = []


def _live(step: str, done: int, total: int) -> None:
    """Dashboard progress (roadmap protocol: results/session_live.json)."""
    LIVE.parent.mkdir(parents=True, exist_ok=True)
    LIVE.write_text(json.dumps({
        "task": "S0", "workers": 1,
        "steps": [{"label": step, "done": done, "total": total}],
    }, indent=2))


#: The two UniProt organism fields, and the reason both are run. `organism_id`
#: matches one node exactly; `taxonomy_id` matches the node and everything
#: under it. The setup snapshot used the first and lost yeast LSM12 to it.
ORGANISM_FIELDS = ["taxonomy_id", "organism_id"]


def snapshot_symbol_table() -> tuple[list[dict], list[dict]]:
    """Re-run the `gene_exact:<symbol> x <organism field>:<taxid>` grid.

    Run under BOTH organism fields so the difference between them is a
    committed measurement rather than a silent fix (roadmap D23).
    """
    screened: list[dict] = []
    raw: list[dict] = []
    total = len(SPECIES) * len(SYMBOLS) * len(ORGANISM_FIELDS)
    n = 0

    for species, taxid in SPECIES:
        for symbol, partition in SYMBOLS:
            part = FAMILY_PARTITIONS[partition]
            per_field = {}

            for field in ORGANISM_FIELDS:
                n += 1
                _live(f"UniProt {symbol} / {species} ({field})", n, total)
                hits, url = gene_exact_query(symbol, taxid, field=field)
                QUERY_LOG.append({"kind": "uniprot_gene_exact", "field": field,
                                  "url": url, "n_hits": len(hits)})
                best, reason = pick_best(hits, part["pfam"], part["length_aa"])
                per_field[field] = (hits, best, reason)

                if field == "taxonomy_id":
                    for h in hits:
                        raw.append({
                            "species": species, "taxid": taxid,
                            "symbol_queried": symbol, "partition": partition,
                            "accession": h.accession, "entry_name": h.entry_name,
                            "protein_name": h.protein_name,
                            "gene_names": ";".join(h.gene_names),
                            "length_aa": h.length, "status": h.status,
                            "pfam": ";".join(h.pfam), "organism": h.organism,
                        })

            # The subtree query is the one the project adopts (D23).
            hits, best, reason = per_field["taxonomy_id"]
            _, exact_best, _ = per_field["organism_id"]
            differs = ((best.accession if best else "")
                       != (exact_best.accession if exact_best else ""))

            screened.append({
                "species": species, "taxid": taxid, "symbol_queried": symbol,
                "partition": partition,
                "n_hits_returned": len(hits),
                "accession": best.accession if best else "",
                "length_aa": best.length if best else "",
                "status": best.status if best else "",
                "pfam": ";".join(best.pfam) if best else "",
                "protein_name": best.protein_name if best else "",
                "result": "found" if best else "not found by symbol",
                "screen_note": reason,
                "query": f"gene_exact:{symbol} AND taxonomy_id:{taxid}",
                "organism_id_result": ("found" if exact_best
                                       else "not found by symbol"),
                "organism_id_accession": (exact_best.accession
                                          if exact_best else ""),
                "field_changes_call": differs,
            })
    return screened, raw


def snapshot_symbol_collision() -> list[dict]:
    """Re-measure `gene_exact:HN1L` — the trap recorded in family.py."""
    rows = []
    for symbol, spec in SYMBOL_COLLISIONS.items():
        hits, url = uniprot_query(f"gene_exact:{symbol}", size=100)
        QUERY_LOG.append({"kind": "symbol_collision", "url": url,
                          "n_hits": len(hits)})
        human = [h for h in hits if h.taxon_id == 9606]
        longest = max(human, key=lambda h: h.length) if human else None
        for h in sorted(human, key=lambda h: -h.length):
            rows.append({
                "symbol_queried": symbol,
                "accession": h.accession,
                "protein_name": h.protein_name,
                "gene_names": ";".join(h.gene_names),
                "length_aa": h.length,
                "status": h.status,
                "pfam": ";".join(h.pfam),
                "is_expected_correct": h.accession == spec["correct"],
                "is_longest_first_pick": bool(longest and
                                              h.accession == longest.accession),
                "query": f"gene_exact:{symbol}",
            })
    return rows


def snapshot_pfam() -> tuple[list[dict], list[dict]]:
    """The API's own protein count and lineage spread per family Pfam."""
    counts, taxa = [], []
    for i, pfam in enumerate(CENSUS_PFAM_IDS, start=1):
        _live(f"InterPro {pfam}", i, len(CENSUS_PFAM_IDS))
        partition = next((k for k, v in FAMILY_PARTITIONS.items()
                          if pfam in v["pfam"]), "?")
        n, url, _page = interpro_pfam_count(pfam)
        QUERY_LOG.append({"kind": "interpro_count", "url": url, "n_hits": n})
        counts.append({"pfam": pfam, "partition": partition,
                       "uniprot_proteins": n, "url": url})

        rows, turl = interpro_taxonomy(pfam)
        QUERY_LOG.append({"kind": "interpro_taxonomy", "url": turl,
                          "n_hits": len(rows)})
        for r in rows:
            taxa.append({"pfam": pfam, "partition": partition, **r})
    return counts, taxa


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("[S0] re-deriving the symbol table (UniProt, live)...")
    screened, raw = snapshot_symbol_table()
    write_tsv(OUT / "symbol_table.tsv", screened, [
        "species", "taxid", "symbol_queried", "partition", "result",
        "accession", "length_aa", "status", "pfam", "protein_name",
        "n_hits_returned", "screen_note", "query",
        "organism_id_result", "organism_id_accession", "field_changes_call"])
    write_tsv(OUT / "symbol_table_raw.tsv", raw, [
        "species", "taxid", "symbol_queried", "partition", "accession",
        "entry_name", "protein_name", "gene_names", "length_aa", "status",
        "pfam", "organism"])
    flips = [r for r in screened if r["field_changes_call"]]
    print(f"  -> {len(screened)} cells, {len(raw)} raw hits")
    print(f"  -> organism_id vs taxonomy_id changes the call in "
          f"{len(flips)} cell(s):")
    for f in flips:
        print(f"     {f['species']}/{f['symbol_queried']}: "
              f"taxonomy_id={f['result']} ({f['accession']}) vs "
              f"organism_id={f['organism_id_result']}")

    print("[S0] re-measuring the HN1L symbol collision...")
    coll = snapshot_symbol_collision()
    write_tsv(OUT / "symbol_collision.tsv", coll, [
        "symbol_queried", "accession", "protein_name", "gene_names",
        "length_aa", "status", "pfam", "is_expected_correct",
        "is_longest_first_pick", "query"])
    print(f"  -> {len(coll)} human hits for the colliding symbols")

    print("[S0] re-deriving the Pfam counts + taxonomy (InterPro, live)...")
    counts, taxa = snapshot_pfam()
    write_tsv(OUT / "pfam_counts.tsv", counts,
              ["pfam", "partition", "uniprot_proteins", "url"])
    write_tsv(OUT / "pfam_taxonomy.tsv", taxa,
              ["pfam", "partition", "tax_id", "name", "rank", "counters"])
    for c in counts:
        print(f"  -> {c['pfam']} ({c['partition']}): "
              f"{c['uniprot_proteins']:,} UniProt proteins")

    (OUT / "snapshot_meta.json").write_text(json.dumps({
        "task": "S0",
        "snapshot_date": date.today().isoformat(),
        "python": sys.version.split()[0],
        "n_queries": len(QUERY_LOG),
        "queries": QUERY_LOG,
    }, indent=2))
    _live("S0 database snapshot complete", 1, 1)
    print(f"[S0] wrote {OUT} ({len(QUERY_LOG)} queries logged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
