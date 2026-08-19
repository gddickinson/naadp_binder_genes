"""S1 control panels — the ground truth the discovery scorer is tested on.

Fetched live from UniProt and cached as JSON + FASTA, so the benchmark
reruns offline and the exact panel that produced a number is committed
next to it.

**Every record declares its partition.** In production the partition is a
property of the search (S2 enumerates JPT from IPR033335 and LSM12 from
IPR039683), so the panel declares it the same way rather than letting the
scorer guess. Records marked `BOTH` are emitted twice, once per family —
a generic decoy has to be tested against each family separately, and
scoring one record in two unrelated families in *one* run is the D14 error
wearing a different hat.

POSITIVES — true family members that must score >= 40 when their own name
is held out of `known_paralogs`:
  * JPT2 orthologs across a vertebrate panel (hold-out run `JPT2`);
  * LSM12 orthologs across the same panel plus fly and yeast (hold-out
    `LSM12`);
  * the deep grade — fly `Jupiter`, yeast `LSM12`, worm and plant members.
    These are never name-protected, so they are scored in the baseline
    run: an unnamed true family member surfacing is the real use case.

  NOTE (D21): a positive here is a *family* call, not a binder call. Fly
  Jupiter is a Jupiter-family protein; nothing in this panel asserts that
  it binds NAADP.

DECOYS — must score < 40 in every run:
  * **JPT1 / HN1 across every species in the panel** — the sharp decoy.
    It carries PF17054 exactly as JPT2 does, at 143-154 aa against
    190-218 aa, and is not a NAADP binder. It takes the +20 domain point
    by construction. Reported separately: if it passes, no domain-based
    rule can fix it (D21).
  * CRAMP1 (Q96RY5, 1,269 aa) — the `gene_exact:HN1L` symbol-collision
    trap measured at setup.
  * the Lsm/Sm fold set (LSM1-8, SNRPD1-3, SNRPE/F/G, ATXN2L) for the
    LSM12 partition — an ancient, deep decoy pool.
  * ~16 unrelated proteins inside the 120-280 aa band, which take the
    size component by construction. This is the D22 measurement: the band
    excludes almost nothing for proteins this small.
"""

from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.s0_lib import gene_exact_query, pick_best  # noqa: E402
from src.core.models import ProteinVariant  # noqa: E402
from src.utils.family import FAMILY_PARTITIONS  # noqa: E402

#: (symbol, taxon id, hold-out group, partition). `group` names the run a
#: positive is scored in; `deep_grade` members are scored in the baseline.
POSITIVE_SPEC: list[tuple[str, int, str, str]] = [
    # --- JPT2 orthologs (hold-out JPT2) ---
    ("JPT2", 9606, "JPT2", "JPT"), ("Jpt2", 10090, "JPT2", "JPT"),
    ("Jpt2", 10116, "JPT2", "JPT"), ("JPT2", 9031, "JPT2", "JPT"),
    ("jpt2", 8364, "JPT2", "JPT"), ("jpt2", 7955, "JPT2", "JPT"),
    ("JPT2", 9913, "JPT2", "JPT"), ("HN1L", 9598, "JPT2", "JPT"),
    # --- LSM12 orthologs (hold-out LSM12) ---
    ("LSM12", 9606, "LSM12", "LSM12"), ("Lsm12", 10090, "LSM12", "LSM12"),
    ("Lsm12", 10116, "LSM12", "LSM12"), ("LSM12", 9031, "LSM12", "LSM12"),
    ("lsm12", 8364, "LSM12", "LSM12"), ("lsm12", 7955, "LSM12", "LSM12"),
    ("LSM12", 9913, "LSM12", "LSM12"),
    # --- the deep grade: true members no vertebrate symbol filter knows ---
    ("Jupiter", 7227, "deep_grade", "JPT"),
    ("Lsm12", 7227, "deep_grade", "LSM12"),
    ("LSM12", 4932, "deep_grade", "LSM12"),      # D23: subtree, not node
    ("lsm-12", 6239, "deep_grade", "LSM12"),
    ("LSM12A", 3702, "deep_grade", "LSM12"),
]

#: (symbol, taxon id, category, partition). Partition `BOTH` is emitted
#: once per family — see the module docstring.
DECOY_SPEC: list[tuple[str, int, str, str]] = [
    # --- the sharp decoy: identical Pfam, same size class, not a binder ---
    ("JPT1", 9606, "JPT1 (sister paralog)", "JPT"),
    ("Jpt1", 10090, "JPT1 (sister paralog)", "JPT"),
    ("Jpt1", 10116, "JPT1 (sister paralog)", "JPT"),
    ("JPT1", 9031, "JPT1 (sister paralog)", "JPT"),
    ("jpt1", 8364, "JPT1 (sister paralog)", "JPT"),
    ("jpt1", 7955, "JPT1 (sister paralog)", "JPT"),
    ("HN1", 9913, "JPT1 (sister paralog)", "JPT"),
    # --- the symbol-collision trap (family.py:SYMBOL_COLLISIONS) ---
    ("CRAMP1", 9606, "symbol-collision trap", "JPT"),
    # --- the Lsm/Sm fold set: ancient, deep, and not LSM12 ---
    ("LSM1", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM2", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM3", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM4", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM5", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM6", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM7", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM8", 9606, "Lsm/Sm fold set", "LSM12"),
    ("LSM14A", 9606, "Lsm/Sm fold set", "LSM12"),
    ("SNRPD1", 9606, "Lsm/Sm fold set", "LSM12"),
    ("SNRPD2", 9606, "Lsm/Sm fold set", "LSM12"),
    ("SNRPD3", 9606, "Lsm/Sm fold set", "LSM12"),
    ("SNRPE", 9606, "Lsm/Sm fold set", "LSM12"),
    ("SNRPF", 9606, "Lsm/Sm fold set", "LSM12"),
    ("SNRPG", 9606, "Lsm/Sm fold set", "LSM12"),
    ("ATXN2L", 9606, "Lsm/Sm fold set", "LSM12"),
    # --- unrelated proteins inside the 120-280 aa band (the D22 test) ---
    ("CALM1", 9606, "in-band unrelated", "BOTH"),
    ("PFN1", 9606, "in-band unrelated", "BOTH"),
    ("CFL1", 9606, "in-band unrelated", "BOTH"),
    ("RHOA", 9606, "in-band unrelated", "BOTH"),
    ("RAC1", 9606, "in-band unrelated", "BOTH"),
    ("CDC42", 9606, "in-band unrelated", "BOTH"),
    ("HRAS", 9606, "in-band unrelated", "BOTH"),
    ("KRAS", 9606, "in-band unrelated", "BOTH"),
    ("TPT1", 9606, "in-band unrelated", "BOTH"),
    ("SOD1", 9606, "in-band unrelated", "BOTH"),
    ("PPIA", 9606, "in-band unrelated", "BOTH"),
    ("RPS3", 9606, "in-band unrelated", "BOTH"),
    ("RPL7", 9606, "in-band unrelated", "BOTH"),
    ("MYL6", 9606, "in-band unrelated", "BOTH"),
    ("TAGLN2", 9606, "in-band unrelated", "BOTH"),
    ("Calm1", 10090, "in-band unrelated", "BOTH"),
    # --- out-of-band sanity checks ---
    # TTN (34,350 aa) was in this list on the first run and had to come
    # out: one protein 180x the family's length inflates the MAFFT
    # alignment to 34,367 columns and drags every full-alignment identity
    # in the panel toward zero. Measured, kept as a result, and replaced
    # by decoys whose out-of-band-ness is real but bounded — CRAMP1
    # (1,269 aa), ATXN2L (1,075), ALB (609), LSM14A (463), and the Sm
    # proteins at 76-133 aa below the band. See
    # `alignment_width_effect.tsv` and s1_benchmark.py:GIANT_ACC.
    ("ALB", 9606, "out-of-band unrelated", "BOTH"),
    ("HSPA5", 9606, "out-of-band unrelated", "BOTH"),
]

#: Screening band used when picking a positive. Wider than either
#: partition's own band on purpose: the band must not be what decides
#: which entry is the right one (D22), only what excludes a 1,269 aa
#: synonym match.
POSITIVE_SCREEN_BAND = (100, 400)


def _variant(hit, symbol: str, taxid: int, note: str, kind: str,
             partition: str, reason: str) -> ProteinVariant:
    prefix = "DECOY" if kind == "decoy" else "CONTROL"
    return ProteinVariant(
        source="UniProt",
        accession=hit.accession,
        gene_symbol=(hit.gene_names[0] if hit.gene_names else symbol),
        species=hit.organism,
        taxon_id=taxid,
        length_aa=hit.length or None,
        description=f"{prefix} [{note}] {hit.protein_name}",
        sequence="",
        url=f"https://www.uniprot.org/uniprotkb/{hit.accession}",
        raw={"panel_note": note, "panel_kind": kind, "queried_symbol": symbol,
             "partition": partition, "reviewed": "SP" if hit.reviewed else "TR",
             "uniprot_pfam": "+".join(hit.pfam), "pick_reason": reason,
             "entry_name": hit.entry_name},
    )


def _fetch_sequence(accession: str) -> str:
    """The FASTA sequence for one accession (the search fields call above
    omits it to keep the query small)."""
    import requests
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
    r = requests.get(url, timeout=45,
                     headers={"User-Agent": "naadp_binder_genes/S1"})
    r.raise_for_status()
    return "".join(r.text.splitlines()[1:])


#: Every synonym collision this panel build ran into, for committing.
COLLISIONS: list[dict] = []


def _primary_first(hits, symbol: str, taxid: int, note: str):
    """Split hits into those whose PRIMARY gene symbol is the query and
    those that matched on a synonym, recording the latter.

    `gene_exact:` matches synonyms, not just primary symbols, and this is
    not a quirk of HN1L. Measured here on the first unrelated control
    chosen for the decoy panel: `gene_exact:ALB AND taxonomy_id:9606`
    returns FBF1 (Q8TES7, 1,133 aa), which carries ALB as a synonym,
    alongside albumin (P02768, 609 aa) — and a reviewed-first,
    longest-tie-break pick selects FBF1. Same failure as
    family.py:SYMBOL_COLLISIONS, on a gene nobody flagged in advance.
    """
    u = symbol.upper()
    primary = [h for h in hits if h.gene_names and h.gene_names[0].upper() == u]
    synonym = [h for h in hits if h not in primary]
    for h in synonym:
        if h.reviewed and primary and h.length > max(p.length for p in primary):
            COLLISIONS.append({
                "queried_symbol": symbol, "taxon_id": taxid, "note": note,
                "collider": h.accession,
                "collider_symbol": h.gene_names[0] if h.gene_names else "",
                "collider_len": h.length,
                "correct": primary[0].accession,
                "correct_symbol": symbol, "correct_len": primary[0].length,
                "why": ("matched on a gene synonym and is longer than the "
                        "primary-symbol entry, so a longest-first pick "
                        "selects it"),
            })
    return primary, synonym


def _pick_decoy(hits, symbol: str, taxid: int, note: str):
    """Primary symbol first, then reviewed, then longest.

    Decoys are named proteins we want verbatim — including the 1,269 aa
    CRAMP1 that the HN1L synonym collides with, which is why no band
    screen is applied here. But a *synonym* match is never preferred over
    the protein that actually carries the symbol."""
    if not hits:
        return None, "no hit"
    primary, synonym = _primary_first(hits, symbol, taxid, note)
    pool = primary or hits
    fell_back = not primary
    pool = sorted(pool, key=lambda h: (h.reviewed, h.length), reverse=True)
    if fell_back:
        return pool[0], (f"NO primary-symbol hit among {len(hits)}; fell back "
                         f"to synonym match {pool[0].accession}")
    reason = ("single hit" if len(hits) == 1
              else f"primary-symbol hit, reviewed-first of {len(primary)}"
                   f" ({len(synonym)} synonym match(es) rejected)")
    return pool[0], reason


def fetch_panel(spec, kind: str, cache_dir: Path, log=print
                ) -> list[ProteinVariant]:
    """Fetch (or reload) one panel. `kind` is 'positive' or 'decoy'."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"panel_{kind}s.json"
    if cache.exists():
        records = json.loads(cache.read_text())
        log(f"[panel:{kind}] loaded {len(records)} from cache {cache.name}")
        return [ProteinVariant(**r) for r in records]

    out: list[ProteinVariant] = []
    missing: list[dict] = []
    for symbol, taxid, note, partition in spec:
        try:
            hits, _url = gene_exact_query(symbol, taxid)   # taxonomy_id, D23
        except RuntimeError as exc:
            log(f"[panel:{kind}] {symbol}/{taxid}: query failed ({exc})")
            missing.append({"symbol": symbol, "taxon_id": taxid, "note": note,
                            "partition": partition, "reason": f"query failed: {exc}"})
            continue
        if kind == "positive":
            pfam = list(FAMILY_PARTITIONS.get(partition, {}).get("pfam", []))
            primary, _syn = _primary_first(hits, symbol, taxid, note)
            # Screen on the wide band, not the partition band: a real
            # ortholog outside its family's declared band is a finding,
            # not something to silently drop.
            best, reason = pick_best(primary or hits, pfam,
                                     POSITIVE_SCREEN_BAND)
            if not primary and best is not None:
                reason = f"no primary-symbol hit; {reason}"
        else:
            best, reason = _pick_decoy(hits, symbol, taxid, note)
        if best is None:
            log(f"[panel:{kind}] {symbol}/{taxid}: unresolved — {reason}")
            missing.append({"symbol": symbol, "taxon_id": taxid, "note": note,
                            "partition": partition, "reason": reason})
            continue
        parts = [partition] if partition != "BOTH" else list(FAMILY_PARTITIONS)
        seq = _fetch_sequence(best.accession)
        for pkey in parts:
            v = _variant(best, symbol, taxid, note, kind, pkey, reason)
            v.sequence = seq
            out.append(v if len(parts) == 1 else copy.deepcopy(v))
        log(f"[panel:{kind}] {best.accession} {best.gene_names[0] if best.gene_names else symbol:<10} "
            f"{best.organism:<26} {best.length:>5} aa [{'SP' if best.reviewed else 'TR'}] "
            f"{'/'.join(parts):<10} {note}")
        time.sleep(0.1)

    cache.write_text(json.dumps([v.__dict__ for v in out], indent=1))
    _write_fasta(cache_dir / f"panel_{kind}s.fasta", out)
    if missing:
        (cache_dir / f"panel_{kind}s_missing.tsv").write_text(
            "symbol\ttaxon_id\tnote\tpartition\treason\n" +
            "".join(f"{m['symbol']}\t{m['taxon_id']}\t{m['note']}\t"
                    f"{m['partition']}\t{m['reason']}\n" for m in missing))
    log(f"[panel:{kind}] cached {len(out)} records "
        f"({len(missing)} unresolved) → {cache.name}")
    return out


def _write_fasta(path: Path, variants: list[ProteinVariant]) -> None:
    seen: set[str] = set()
    with path.open("w") as f:
        for v in variants:
            key = f"{v.accession}|{v.raw.get('partition','')}"
            if key in seen:
                continue
            seen.add(key)
            f.write(f">{v.accession}|{v.gene_symbol}|"
                    f"{v.species.replace(' ', '_')}|{v.raw.get('partition','')}"
                    f"|{v.raw.get('panel_note','')}\n")
            for i in range(0, len(v.sequence), 60):
                f.write(v.sequence[i:i + 60] + "\n")


def write_collisions(cache_dir: Path) -> int:
    """Commit every synonym collision the panel build hit (D21-adjacent:
    a symbol is not an identity)."""
    cols = ["queried_symbol", "taxon_id", "note", "collider",
            "collider_symbol", "collider_len", "correct", "correct_symbol",
            "correct_len", "why"]
    path = cache_dir / "symbol_collisions.tsv"
    with path.open("w") as f:
        f.write("\t".join(cols) + "\n")
        for r in COLLISIONS:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    return len(COLLISIONS)


if __name__ == "__main__":
    out_dir = PROJECT_ROOT / "results" / "benchmark_controls"
    fetch_panel(POSITIVE_SPEC, "positive", out_dir)
    fetch_panel(DECOY_SPEC, "decoy", out_dir)
    n = write_collisions(out_dir)
    print(f"[panel] {n} synonym collision(s) recorded → symbol_collisions.tsv")
