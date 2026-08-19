#!/usr/bin/env python
"""S0 — how much of each family does its planned census signature actually see?

S2's brief enumerates the census from the Pfam signatures declared in
`family.py` (PF17054 for the JPT partition; PF09793 / PF21166 for LSM12).
This script measures whether that denominator is the family.

It does two things:

1. **Denominator comparison.** For every family Pfam, look up the InterPro
   entry it is integrated into and compare protein and taxon counts. A Pfam
   that is a *member* of a larger InterPro family entry enumerates only the
   part of the family its HMM matches.
2. **Known-true-positive recall.** Take the accessions this project already
   knows are real family members (`REFERENCE_PANEL` + `SISTER_PANEL` + the
   orthologs S0 re-derived) and ask, per accession, whether the planned
   Pfam signature is actually annotated on it. A signature that misses a
   reviewed ortholog cannot be the census denominator.

Writes `results/s0_baseline/signature_scope.tsv` and
`results/s0_baseline/signature_recall.tsv`.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.s0_lib import USER_AGENT, _get, write_tsv  # noqa: E402
from src.utils.family import (  # noqa: E402
    CENSUS_PFAM_IDS, FAMILY_PARTITIONS, REFERENCE_PANEL, SISTER_PANEL,
)

OUT = ROOT / "results" / "s0_baseline"
INTERPRO = "https://www.ebi.ac.uk/interpro/api"


def pfam_meta(pfam_id: str) -> dict:
    d = _get(f"{INTERPRO}/entry/pfam/{pfam_id}/").json()["metadata"]
    return {
        "accession": d["accession"],
        "name": d["name"].get("name", ""),
        "type": d.get("type", ""),
        "integrated_into": d.get("integrated") or "",
        "proteins": (d.get("counters") or {}).get("proteins", 0),
        "taxa": (d.get("counters") or {}).get("taxa", 0),
    }


def interpro_meta(ipr: str) -> dict:
    d = _get(f"{INTERPRO}/entry/interpro/{ipr}/").json()["metadata"]
    return {
        "accession": d["accession"],
        "name": d["name"].get("name", ""),
        "type": d.get("type", ""),
        "members": ",".join(sorted((d.get("member_databases") or {}).keys())),
        "proteins": (d.get("counters") or {}).get("proteins", 0),
        "taxa": (d.get("counters") or {}).get("taxa", 0),
    }


def uniprot_signatures(acc: str) -> tuple[list[str], list[str], str, int, bool]:
    """Return (pfam ids, interpro ids, protein name, length, reviewed)."""
    r = requests.get(
        f"https://rest.uniprot.org/uniprotkb/{acc}.json",
        params={"fields": "accession,xref_pfam,xref_interpro,protein_name,"
                          "length,reviewed,organism_name"},
        headers={"User-Agent": USER_AGENT}, timeout=40)
    r.raise_for_status()
    d = r.json()
    xr = d.get("uniProtKBCrossReferences", []) or []
    pfam = sorted({x["id"] for x in xr if x.get("database") == "Pfam"})
    ipr = sorted({x["id"] for x in xr if x.get("database") == "InterPro"})
    rec = (d.get("proteinDescription", {}).get("recommendedName") or {})
    name = (rec.get("fullName") or {}).get("value", "")
    reviewed = "unreviewed" not in d.get("entryType", "").lower()
    length = int((d.get("sequence") or {}).get("length", 0) or 0)
    return pfam, ipr, name, length, reviewed


#: The InterPro **family**-level entry per partition — the candidate census
#: denominator this script exists to compare the planned Pfam against.
FAMILY_LEVEL_ENTRIES = {
    "JPT": "IPR033335",     # Microtubule-associated protein Jupiter
    "LSM12": "IPR039683",   # Protein Lsm12-like
}


def family_level_rows() -> list[dict]:
    """The family-level InterPro entry per partition, as a comparison row."""
    rows = []
    for partition, ipr in FAMILY_LEVEL_ENTRIES.items():
        im = interpro_meta(ipr)
        rows.append({
            "partition": partition,
            "pfam": "(family-level entry)",
            "pfam_name": "",
            "pfam_type": "",
            "pfam_proteins": "",
            "pfam_taxa": "",
            "interpro_entry": ipr,
            "interpro_name": im["name"],
            "interpro_type": im["type"],
            "interpro_members": im["members"],
            "interpro_proteins": im["proteins"],
            "interpro_taxa": im["taxa"],
            "pfam_fraction_of_interpro": "",
        })
    return rows


def scope_rows() -> list[dict]:
    rows = []
    for pfam in CENSUS_PFAM_IDS:
        partition = next((k for k, v in FAMILY_PARTITIONS.items()
                          if pfam in v["pfam"]), "?")
        pm = pfam_meta(pfam)
        ipr = pm["integrated_into"]
        im = interpro_meta(ipr) if ipr else {}
        p_prot = pm["proteins"] or 0
        i_prot = im.get("proteins", 0) or 0
        rows.append({
            "partition": partition,
            "pfam": pfam,
            "pfam_name": pm["name"],
            "pfam_type": pm["type"],
            "pfam_proteins": p_prot,
            "pfam_taxa": pm["taxa"],
            "interpro_entry": ipr,
            "interpro_name": im.get("name", ""),
            "interpro_type": im.get("type", ""),
            "interpro_members": im.get("members", ""),
            "interpro_proteins": i_prot,
            "interpro_taxa": im.get("taxa", ""),
            "pfam_fraction_of_interpro": (round(p_prot / i_prot, 3)
                                          if i_prot else ""),
        })
    return rows


def recall_rows() -> list[dict]:
    """Do the planned signatures actually annotate the known true positives?"""
    panel: list[tuple[str, str, str]] = []
    for label, acc in REFERENCE_PANEL:
        panel.append((label, acc, "reference (known binder)"))
    for label, acc in SISTER_PANEL:
        panel.append((label, acc, "sister paralog (known non-binder)"))

    # The orthologs S0 re-derived, so recall is measured on real records.
    st = OUT / "symbol_table.tsv"
    if st.exists():
        with st.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if r["result"] == "found" and r["accession"]:
                    panel.append((f"{r['species']}_{r['symbol_queried']}",
                                  r["accession"], "S0 symbol-table ortholog"))

    seen, rows = set(), []
    for label, acc, role in panel:
        if acc in seen:
            continue
        seen.add(acc)
        pfam, ipr, name, length, reviewed = uniprot_signatures(acc)
        partition = "LSM12" if "LSM12" in label.upper() else "JPT"
        planned = FAMILY_PARTITIONS[partition]["pfam"]
        hit = [p for p in planned if p in pfam]
        rows.append({
            "label": label, "accession": acc, "role": role,
            "partition": partition, "length_aa": length,
            "status": "SP" if reviewed else "TR",
            "protein_name": name,
            "planned_pfam": ",".join(planned),
            "pfam_annotated": ",".join(pfam) or "NONE",
            "interpro_annotated": ",".join(ipr) or "NONE",
            "found_by_planned_pfam": bool(hit),
        })
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    print("[S0] comparing Pfam vs InterPro-family denominators...")
    scope = scope_rows() + family_level_rows()
    write_tsv(OUT / "signature_scope.tsv", scope, list(scope[0].keys()))
    for r in scope:
        print(f"  {r['partition']:6} {r['pfam']:22} {str(r['pfam_proteins']):>6}"
              f"  ->  {r['interpro_entry']} ({r['interpro_type']:6}) "
              f"{r['interpro_proteins']:>6} proteins / {r['interpro_taxa']:>5} taxa  "
              f"fraction={r['pfam_fraction_of_interpro']}")

    print("[S0] testing the planned signatures against known true positives...")
    rec = recall_rows()
    write_tsv(OUT / "signature_recall.tsv", rec, list(rec[0].keys()))
    missed = [r for r in rec if not r["found_by_planned_pfam"]]
    print(f"  {len(rec) - len(missed)}/{len(rec)} known members carry their "
          f"planned Pfam")
    for m in missed:
        print(f"  MISSED: {m['label']} {m['accession']} ({m['status']}, "
              f"{m['length_aa']} aa) pfam={m['pfam_annotated']} "
              f"interpro={m['interpro_annotated']}")

    (OUT / "signature_scope_meta.json").write_text(json.dumps({
        "n_signatures": len(scope), "n_panel": len(rec),
        "n_missed_by_planned_pfam": len(missed),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
