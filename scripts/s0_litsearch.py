#!/usr/bin/env python
"""S0 helper — query Europe PMC and print structured candidate citations.

Used interactively while auditing the `[lit]` claims in
`docs/naadp_binder_background.md`: it turns a free-text query into
citations with PMID / DOI / journal / year, so a claim is verified against
a record rather than against search-result prose.

  python scripts/s0_litsearch.py "NAADP binding protein JPT2" --n 8
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
UA = "naadp_binder_genes/S0 (george.dickinson@gmail.com)"


def search(query: str, n: int = 10) -> list[dict]:
    r = requests.get(EPMC, params={
        "query": query, "format": "json", "pageSize": str(n),
        "resultType": "core", "sort": "CITED desc",
    }, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    out = []
    for h in r.json().get("resultList", {}).get("result", []):
        out.append({
            "pmid": h.get("pmid", ""),
            "pmcid": h.get("pmcid", ""),
            "doi": h.get("doi", ""),
            "title": h.get("title", "").rstrip("."),
            "authors": h.get("authorString", ""),
            "journal": (h.get("journalInfo", {}) or {})
                       .get("journal", {}).get("title", ""),
            "year": h.get("pubYear", ""),
            "cited_by": h.get("citedByCount", 0),
            "type": h.get("pubType", ""),
            "is_open_access": h.get("isOpenAccess", ""),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits = search(a.query, a.n)
    if a.json:
        print(json.dumps(hits, indent=2))
        return 0
    for h in hits:
        print(f"[{h['year']}] {h['journal']} | PMID:{h['pmid']} | "
              f"DOI:{h['doi']} | cited:{h['cited_by']} | {h['type']}")
        print(f"    {h['title']}")
        print(f"    {h['authors'][:120]}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
