#!/usr/bin/env python
"""S0 steps 2-3 — audit every `[lit]` claim in the background document.

Each claim below was checked against a primary source during S0. The
verdict, the supporting PMIDs and the reason are declared here; the
citation metadata is fetched live from Europe PMC, so `references.tsv` is
generated rather than hand-typed and cannot drift from the record.

Verdicts:
  verified      the claim stands as written
  qualified     true, but the source hedges or the support is review-level
  refined       true, but the background document's wording is imprecise
  corrected     the background document is wrong; the corrected form is given
  retag         the claim is true but carries the wrong evidence tag

Writes `results/s0_baseline/lit_claims.tsv` and `references.tsv`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.s0_lib import write_tsv  # noqa: E402

OUT = ROOT / "results" / "s0_baseline"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
UA = {"User-Agent": "naadp_binder_genes/S0 (george.dickinson@gmail.com)"}

#: Every `[lit]`-tagged claim in `docs/naadp_binder_background.md`, plus the
#: one claim S0 found to be mis-tagged. `claim` quotes the document.
CLAIMS = [
    {
        "id": "L1",
        "section": "The problem these proteins solved",
        "claim": "NAADP is the most potent Ca2+-mobilising second messenger "
                 "known.",
        "verdict": "qualified",
        "pmids": ["7836444", "31182546"],
        "evidence":
            "Primary datum: Lee & Aarhus 1995 measured half-maximal Ca2+ "
            "release at ~30 nM NAADP in sea urchin egg homogenate, with NADP "
            "and NAAD ineffective at 10-40x higher concentrations. The "
            "comparative superlative is review-level and is hedged in its "
            "source: Galione 2019 writes 'NAADP is arguably the most "
            "tantalizing. It is the most potent, often efficacious at low "
            "nanomolar concentrations.'",
        "action":
            "Keep, but attribute. The superlative is a comparative statement "
            "from a review, not a head-to-head primary measurement in this "
            "project's scope; quote the ~30 nM EC50 when a number is needed.",
    },
    {
        "id": "L2",
        "section": "The problem these proteins solved",
        "claim": "For roughly two decades its receptor was unidentified — "
                 "the 'missing NAADP receptor' problem.",
        "verdict": "corrected",
        "pmids": ["3496336", "7836444", "33758061", "33758062", "34362892"],
        "evidence":
            "The Ca2+-mobilising activity was reported in 1987 (Clapper et "
            "al.) and the active species identified as NAADP in 1995 (Lee & "
            "Aarhus). The NAADP-binding proteins were identified in 2021 "
            "(Gunaratne et al.; Roggenkamp et al.; Zhang et al.). That is 26 "
            "years from the identification of the messenger, or 34 years "
            "from the original observation - not 'roughly two decades'.",
        "action":
            "Correct to 'for more than a quarter of a century (1995-2021)'.",
    },
    {
        "id": "L3",
        "section": "The problem these proteins solved",
        "claim": "Two-pore channels were proposed and widely accepted as the "
                 "answer, then shown not to bind NAADP directly.",
        "verdict": "verified",
        "pmids": ["19387438", "19557428", "19940116", "22117075", "22117077",
                  "23063126"],
        "evidence":
            "Proposed: Calcraft et al. 2009 (Nature), Zong et al. 2009 and "
            "Brailoiu et al. 2009. Refuted as the direct binding site: "
            "Lin-Moshier et al. 2012 could not photolabel endogenous or "
            "overexpressed TPCs and found labelling preserved in TPC1 and "
            "TPC2 knockout mouse pancreas, concluding 'an accessory "
            "component within a larger TPC complex is responsible for "
            "binding NAADP'; Walseth et al. 2012 found the sea urchin "
            "photolabelled proteins smaller than sea urchin TPCs and "
            "concluded 'high affinity NAADP binding sites are distinct from "
            "TPCs'. Wang et al. 2012 separately showed TPCs are "
            "PI(3,5)P2-activated Na+-selective channels.",
        "action": "Keep as written.",
    },
    {
        "id": "L4",
        "section": "The problem these proteins solved",
        "claim": "NAADP binds two small accessory proteins, JPT2 (also HN1L) "
                 "and LSM12, which then confer NAADP sensitivity onto the "
                 "two-pore channels, and in some reports onto the ryanodine "
                 "receptors.",
        "verdict": "refined",
        "pmids": ["33758061", "33758062", "34362892", "37607218"],
        "evidence":
            "JPT2: Gunaratne et al. 2021 isolated JPT2 with a clickable "
            "NAADP photoprobe and showed it is required for endogenous "
            "NAADP-evoked Ca2+ signalling via TPCs. LSM12: Zhang et al. 2021 "
            "showed Lsm12 binds NAADP through its Lsm domain and is required "
            "for NAADP-evoked TPC activation. Both bind NAADP with high "
            "affinity and independently associate with TPC1 and TPC2 "
            "(Gunaratne et al. 2023). The ryanodine-receptor arm is reported "
            "for JPT2/HN1L specifically - Roggenkamp et al. 2021 show "
            "TCR/CD3-dependent coprecipitation of HN1L/JPT2 with RYRs in T "
            "cells - and NOT for LSM12, whose reported targets are TPC1/2.",
        "action":
            "Refine: attach the ryanodine-receptor clause to JPT2 alone, not "
            "to both binders.",
    },
    {
        "id": "L5",
        "section": "The problem these proteins solved",
        "claim": "The channel and the receptor are different molecules.",
        "verdict": "verified",
        "pmids": ["22117075", "22117077", "37607218"],
        "evidence":
            "Gunaratne et al. 2023: 'Rather than directly binding to TPCs, "
            "NAADP associates with proteins that indirectly confer NAADP "
            "sensitivity to the TPC complex.'",
        "action": "Keep as written.",
    },
    {
        "id": "L6",
        "section": "The decoy is inside the family",
        "claim": "JPT1 (HN1), 154 aa, carries PF17054 — the same signature "
                 "as JPT2 — and is not a NAADP binder.",
        "verdict": "retag",
        "pmids": ["37607218"],
        "evidence":
            "Two claims wearing one tag. The length and Pfam half is [db] "
            "and S0 re-derived it live (Q9UK76, 154 aa, PF17054). The 'is "
            "not a NAADP binder' half is [lit] and is verified by Gunaratne "
            "et al. 2023, which tested JPT1 directly: no selective "
            "[32P]-NAADP binding in radioligand assays (IC50 not "
            "determinable, against 1.09 nM for JPT2 and 0.703 nM for LSM12); "
            "JPT1 knockout had no effect in Ca2+ imaging or pseudovirus "
            "trafficking; 'these data validate both JPT2 and LSM12 (but not "
            "JPT1) as bona fide NAADP-binding proteins'.",
        "action":
            "Split the tag: [db] for the signature and length, [lit] for the "
            "non-binder status. D21 rests on the [lit] half and it holds.",
    },
    {
        "id": "L7",
        "section": "The decoy is inside the family (new in S0)",
        "claim": "JPT1 and JPT2 share ~40% amino acid identity.",
        "verdict": "verified",
        "pmids": ["37607218"],
        "evidence":
            "Gunaratne et al. 2023: 'JPT1 and JPT2 comprise the dual "
            "representatives of this conserved gene family in higher "
            "vertebrates, displaying ~40% amino acid identity.' The same "
            "paper gives JPT2 as 174-218 aa against JPT1 at 154 aa, "
            "consistent with the lengths S0 re-derived.",
        "action":
            "Add to the background document. This is the number that "
            "calibrates the S1 sister-margin: binder and decoy are ~40% "
            "identical, so a distance-based separation has to resolve well "
            "inside that.",
    },
    {
        "id": "L8",
        "section": "What the databases hold (new in S0)",
        "claim": "The blank cells in the species table are symbol-query "
                 "artefacts, not genome facts.",
        "verdict": "verified",
        "pmids": ["16518797"],
        "evidence":
            "Demonstrated for two cells without leaving S0. (i) Drosophila: "
            "the founding member of PF17054 is the Drosophila protein "
            "Jupiter (Karpova et al. 2006), and UniProt Q9I7K0 (JUPIT_DROME, "
            "208 aa, reviewed) carries PF17054 and IPR033335 - the fly JPT2 "
            "blank is a naming artefact. (ii) Yeast: LSM12 in S. cerevisiae "
            "is P38828 (187 aa, reviewed, PF09793+PF21166), invisible to the "
            "setup query only because it sits under the S288c strain node "
            "(559292) while the project's species table carries the species "
            "node (4932), and UniProt's organism_id matches one node exactly.",
        "action":
            "Keep the [open] tag on the table's blanks and add these two "
            "worked counter-examples. Adopt taxonomy_id over organism_id "
            "(roadmap D23).",
    },
]

#: References cited by the review that are not attached to a single claim.
CONTEXT_PMIDS = [
    "25872774",   # Ruas 2015 EMBO J - Ca2+-permeable TPCs rescue NAADP
    "37607219",   # Saito 2023 Sci Signal - convergent routes to TPC2
    "30860481",   # She 2019 eLife - TPC2 structure
    "20368989",   # Swisher & Parker 2010 - yeast Lsm12 in stress granules
    "24770793",   # Boccaccio 2014 - plant TPCs not PI(3,5)P2-activated
]


def fetch_reference(pmid: str) -> dict:
    r = requests.get(EPMC, params={"query": f"EXT_ID:{pmid}", "format": "json",
                                   "resultType": "core"},
                     headers=UA, timeout=60)
    r.raise_for_status()
    res = r.json().get("resultList", {}).get("result", [])
    if not res:
        return {"pmid": pmid, "title": "(NOT FOUND)"}
    h = res[0]

    def clean(x: str) -> str:
        for a, b in (("<sup>", ""), ("</sup>", ""), ("<i>", ""), ("</i>", ""),
                     ("<sub>", ""), ("</sub>", "")):
            x = x.replace(a, b)
        return x.strip().rstrip(".")

    return {
        "pmid": pmid,
        "doi": h.get("doi", ""),
        "year": h.get("pubYear", ""),
        "journal": (h.get("journalInfo", {}) or {}).get("journal", {})
                   .get("title", ""),
        "authors": h.get("authorString", ""),
        "title": clean(h.get("title", "")),
        "cited_by": h.get("citedByCount", 0),
        "open_access": h.get("isOpenAccess", ""),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in CLAIMS:
        rows.append({
            "claim_id": c["id"],
            "section": c["section"],
            "claim": c["claim"],
            "verdict": c["verdict"],
            "n_refs": len(c["pmids"]),
            "pmids": ";".join(c["pmids"]),
            "evidence": c["evidence"],
            "action": c["action"],
        })
    write_tsv(OUT / "lit_claims.tsv", rows,
              ["claim_id", "section", "claim", "verdict", "n_refs", "pmids",
               "evidence", "action"])

    wanted = sorted({p for c in CLAIMS for p in c["pmids"]} | set(CONTEXT_PMIDS))
    print(f"[S0] fetching {len(wanted)} references from Europe PMC...")
    refs = []
    for p in wanted:
        ref = fetch_reference(p)
        used_by = [c["id"] for c in CLAIMS if p in c["pmids"]]
        ref["cited_for_claims"] = ";".join(used_by) or "context"
        refs.append(ref)
        print(f"  {ref['pmid']:>9} {ref.get('year',''):>4} "
              f"{ref.get('journal','')[:34]:34} {ref.get('title','')[:60]}")

    refs.sort(key=lambda r: (r.get("year", ""), r.get("pmid", "")))
    write_tsv(OUT / "references.tsv", refs,
              ["pmid", "year", "journal", "authors", "title", "doi",
               "cited_by", "open_access", "cited_for_claims"])

    counts: dict[str, int] = {}
    for c in CLAIMS:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    (OUT / "lit_audit_meta.json").write_text(json.dumps({
        "n_claims": len(CLAIMS), "n_references": len(refs),
        "verdicts": counts,
    }, indent=2))

    print(f"\n[S0] {len(CLAIMS)} claims audited, {len(refs)} references")
    for v, n in sorted(counts.items()):
        print(f"  {v:12} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
