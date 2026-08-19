"""S0 shared helpers — live UniProt / InterPro queries for the baseline snapshot.

Used by `s0_db_snapshot.py` (re-derives every `[db]` number in
`docs/naadp_binder_background.md`) and `s0_report.py` (renders the report
from the committed tables, D13).

Everything here is a *query recorder*: each function returns both the parsed
result and the exact URL it used, so the snapshot tables can carry their own
provenance and a later session can re-run them verbatim.
"""

from __future__ import annotations

import csv
import json
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import requests

UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
INTERPRO_API = "https://www.ebi.ac.uk/interpro/api"
USER_AGENT = "naadp_binder_genes/S0 (george.dickinson@gmail.com)"

POLITE_SLEEP_S = 0.34


@dataclass
class UniProtHit:
    """One UniProtKB entry, with the fields S0 needs to screen it."""

    accession: str
    entry_name: str
    protein_name: str
    gene_names: list[str]
    length: int
    reviewed: bool
    organism: str
    taxon_id: int
    pfam: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "SP" if self.reviewed else "TR"


def _get(url: str, params: Optional[dict] = None, timeout_s: int = 60,
         retries: int = 4) -> requests.Response:
    """GET with a polite sleep, a UA, and retry on 5xx / connection errors."""
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout_s,
                                headers={"User-Agent": USER_AGENT,
                                         "Accept": "application/json"})
            if resp.status_code >= 500:
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            time.sleep(POLITE_SLEEP_S)
            return resp
        except Exception as exc:  # noqa: BLE001 - retried below
            last = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url} :: {last}")


def _parse_uniprot_entry(entry: dict[str, Any]) -> UniProtHit:
    """Parse one UniProtKB JSON entry.

    NOTE the `reviewed` test: D0b — `"reviewed" in entryType` also matches
    "UniProtKB unreviewed (TrEMBL)". Test for "unreviewed" FIRST.
    """
    entry_type = entry.get("entryType", "")
    reviewed = "unreviewed" not in entry_type.lower()

    prot = entry.get("proteinDescription", {})
    rec = prot.get("recommendedName") or {}
    name = (rec.get("fullName") or {}).get("value")
    if not name:
        subs = prot.get("submissionNames") or []
        name = (subs[0].get("fullName", {}).get("value") if subs else "") or ""

    genes = []
    for g in entry.get("genes", []) or []:
        if g.get("geneName", {}).get("value"):
            genes.append(g["geneName"]["value"])
        for syn in g.get("synonyms", []) or []:
            if syn.get("value"):
                genes.append(syn["value"])

    pfam = sorted({
        x.get("id", "") for x in entry.get("uniProtKBCrossReferences", []) or []
        if x.get("database") == "Pfam" and x.get("id")
    })

    org = entry.get("organism", {}) or {}
    return UniProtHit(
        accession=entry.get("primaryAccession", ""),
        entry_name=entry.get("uniProtkbId", ""),
        protein_name=name,
        gene_names=genes,
        length=int((entry.get("sequence", {}) or {}).get("length", 0) or 0),
        reviewed=reviewed,
        organism=org.get("scientificName", ""),
        taxon_id=int(org.get("taxonId", 0) or 0),
        pfam=pfam,
    )


def uniprot_query(query: str, size: int = 50) -> tuple[list[UniProtHit], str]:
    """Run one UniProtKB query. Returns (hits, the exact URL used)."""
    params = {
        "query": query,
        "size": str(size),
        "fields": ("accession,id,protein_name,gene_names,length,"
                   "reviewed,organism_name,organism_id,xref_pfam"),
        "format": "json",
    }
    url = f"{UNIPROT_SEARCH}?{urllib.parse.urlencode(params)}"
    resp = _get(UNIPROT_SEARCH, params=params)
    data = resp.json()
    return [_parse_uniprot_entry(e) for e in data.get("results", [])], url


def gene_exact_query(symbol: str, taxid: int,
                     field: str = "taxonomy_id") -> tuple[list[UniProtHit], str]:
    """Symbol x organism lookup.

    `field` matters, and S0 measured why. UniProt's **`organism_id` is an
    exact match on one organism node**, while **`taxonomy_id` searches the
    node and its descendants**. The setup snapshot used `organism_id`, so
    *S. cerevisiae* LSM12 (P38828, 187 aa, reviewed, PF09793+PF21166) was
    invisible: the reviewed entry sits under the S288c strain node (559292)
    and the project's species table carries the species node (4932).

    That is a false absence produced by a query field, not a genome fact,
    so both forms are run and recorded (roadmap D23).
    """
    return uniprot_query(f"gene_exact:{symbol} AND {field}:{taxid}")


def pick_best(hits: list[UniProtHit], pfam_required: list[str],
              length_band: tuple[int, int]) -> tuple[Optional[UniProtHit], str]:
    """Screen by length and Pfam, never by rank (family.py:SYMBOL_COLLISIONS).

    Returns (best hit or None, a plain-language reason string).
    """
    if not hits:
        return None, "no hit"

    lo, hi = length_band
    in_band = [h for h in hits if lo <= h.length <= hi]
    dropped_len = [h for h in hits if h not in in_band]

    if pfam_required:
        with_pfam = [h for h in in_band if any(p in h.pfam for p in pfam_required)]
    else:
        with_pfam = list(in_band)

    pool = with_pfam or in_band
    if not pool:
        why = (f"all {len(hits)} hits outside band {lo}-{hi} aa "
               f"({', '.join(f'{h.accession}:{h.length}aa' for h in hits[:4])})")
        return None, why

    # Swiss-Prot preferred, then longest as tie-break — within the screened pool.
    pool.sort(key=lambda h: (h.reviewed, h.length), reverse=True)
    best = pool[0]

    bits = []
    if dropped_len:
        bits.append("screened out by length: " +
                    ", ".join(f"{h.accession}({h.length}aa)" for h in dropped_len))
    if pfam_required and len(with_pfam) < len(in_band):
        no_pfam = [h for h in in_band if h not in with_pfam]
        bits.append("in band but no required Pfam: " +
                    ", ".join(h.accession for h in no_pfam))
    if not with_pfam and pfam_required:
        bits.append("NO hit carried the required Pfam; fell back to length band")
    return best, "; ".join(bits) or "single clean hit"


def interpro_pfam_count(pfam_id: str) -> tuple[int, str, dict]:
    """The API's own count of UniProt proteins carrying a Pfam signature.

    Returns (count, url, the raw first page) — the count is what S2's
    enumeration must reach, so it is recorded here as the denominator.
    """
    url = f"{INTERPRO_API}/protein/UniProt/entry/pfam/{pfam_id}/"
    resp = _get(url, params={"page_size": "1"})
    data = resp.json()
    return int(data.get("count", 0)), url, data


def interpro_taxonomy(pfam_id: str, top_n: int = 25) -> tuple[list[dict], str]:
    """Per-superkingdom / per-lineage protein counts for a Pfam signature."""
    url = f"{INTERPRO_API}/taxonomy/uniprot/entry/pfam/{pfam_id}/"
    resp = _get(url, params={"page_size": str(top_n)})
    data = resp.json()
    rows = []
    for item in data.get("results", []):
        meta = item.get("metadata", {})
        counters = item.get("extra_fields", {}) or {}
        rows.append({
            "tax_id": meta.get("accession", ""),
            "name": meta.get("name", ""),
            "rank": meta.get("rank", ""),
            "counters": json.dumps(counters, sort_keys=True)[:200],
        })
    return rows, url


def write_tsv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, delimiter="\t",
                           extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_tsv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))
