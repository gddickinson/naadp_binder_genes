"""Which family a protein belongs to — and the guard that makes a
cross-family number impossible rather than merely discouraged (D14 / D14a).

`family.py:FAMILY_PARTITIONS` declares the two unrelated families this
project studies. Until S1 nothing read it, so `discover_novel_paralogs`
happily measured a JPT2 against an LSM12 and called the result "identity".
It is not identity; it is the residue-agreement rate of two unalignable
proteins, and it lands every candidate in the twilight zone by construction.

This module supplies three things:

* **assignment** — `assign_partition()`, a *provenance-first* call. The
  partition is a property of the search that surfaced a record (S2
  enumerates JPT from IPR033335 and LSM12 from IPR039683), so a declared
  `raw["partition"]` wins. Failing that: the family Pfam it carries, then
  its gene symbol, then nothing.
* **the guard** — `assert_single_partition()` raises `CrossPartitionError`
  when a set spans both families. `discover_novel_paralogs` calls it on
  every run, so the D14-violating run has to be *asked for* explicitly
  (`allow_cross_partition=True`) rather than happening by omission.
* **the split** — `split_by_partition()`, which is how a mixed set is made
  runnable: one analysis and one scorer run per family, never a joint one.

Note what assignment deliberately is **not**: a binder call. Assigning a
protein to the JPT partition says it is a Jupiter-family protein, which
JPT1 also is (D21). Partition membership and NAADP binding are different
columns and this module only fills the first.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, Optional

from .family import FAMILY_PARTITIONS, SISTER_PARALOGS

#: Partition keys in a fixed order, so reports and tables are stable.
PARTITION_KEYS: list[str] = list(FAMILY_PARTITIONS)

#: Symbols that name a partition member but are not the member's own
#: primary symbol. HN1L/HN1 are the pre-2019 names still worn by many
#: TrEMBL entries; `jupiter` is the fly gene the Pfam is named after and
#: the ancestral single-copy grade of the JPT partition.
PARTITION_SYMBOL_ALIASES: dict[str, str] = {
    "HN1L": "JPT", "HN1": "JPT", "JUPITER": "JPT", "JPT": "JPT",
    "LSM-12": "LSM12", "LSM12A": "LSM12", "LSM12B": "LSM12",
}


class CrossPartitionError(RuntimeError):
    """A number was about to be computed across the JPT/LSM12 boundary.

    Raised rather than warned: roadmap D14 makes this a correctness bug,
    and the failure mode it prevents (every candidate scoring as novel
    because its nearest "paralog" is an unrelated protein) is silent.
    """


def _pfam_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for key, spec in FAMILY_PARTITIONS.items():
        for pf in spec.get("pfam", []):
            idx[pf.upper()] = key
    return idx


def _symbol_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for key, spec in FAMILY_PARTITIONS.items():
        for sym in spec.get("members", []):
            idx[sym.upper()] = key
    for sym in SISTER_PARALOGS:          # JPT1 / HN1 are JPTs, not binders
        idx.setdefault(sym.upper(), "JPT")
    idx.update(PARTITION_SYMBOL_ALIASES)
    return idx


PFAM_TO_PARTITION = _pfam_index()
SYMBOL_TO_PARTITION = _symbol_index()


def partition_of_pfam(pfam_id: str) -> Optional[str]:
    return PFAM_TO_PARTITION.get((pfam_id or "").strip().upper())


def partition_of_symbol(symbol: str) -> Optional[str]:
    """Exact match, then longest-prefix — so `jpt2b` resolves but `LSM1`
    does not accidentally match `LSM12`."""
    u = (symbol or "").strip().upper()
    if not u:
        return None
    if u in SYMBOL_TO_PARTITION:
        return SYMBOL_TO_PARTITION[u]
    for sym in sorted(SYMBOL_TO_PARTITION, key=len, reverse=True):
        if len(sym) >= 4 and u.startswith(sym):
            return SYMBOL_TO_PARTITION[sym]
    return None


def _declared_pfams(variant, domain_hits: Optional[dict] = None) -> list[str]:
    """Every family Pfam attached to a variant, from any of the three
    places the pipeline puts them."""
    out: list[str] = []
    for h in (domain_hits or {}).get(getattr(variant, "accession", ""), []) or []:
        pid = getattr(h, "pfam_id", "")
        if pid:
            out.append(pid)
    raw = getattr(variant, "raw", None) or {}
    for field in ("pfam_id", "pfam"):
        val = raw.get(field)
        if isinstance(val, str):
            out.extend(x for x in val.replace(",", "+").split("+") if x)
        elif isinstance(val, (list, tuple)):
            out.extend(str(x) for x in val if x)
    return out


def assign_partition(variant, domain_hits: Optional[dict] = None
                     ) -> tuple[Optional[str], str]:
    """Return (partition key or None, the reason it was assigned).

    Order is provenance → signature → symbol, and the reason is returned
    so every table can carry how the call was made. `None` means the
    record is unassignable from what is on it — reported, never guessed.
    """
    raw = getattr(variant, "raw", None) or {}
    declared = str(raw.get("partition", "") or "").upper()
    if declared in FAMILY_PARTITIONS:
        return declared, "declared by the search that surfaced it"

    for pf in _declared_pfams(variant, domain_hits):
        key = partition_of_pfam(pf)
        if key:
            return key, f"carries {pf.upper()}"

    key = partition_of_symbol(getattr(variant, "gene_symbol", ""))
    if key:
        return key, f"gene symbol {variant.gene_symbol}"
    return None, "no partition signature, symbol or provenance"


def partitions_present(variants: Iterable, domain_hits: Optional[dict] = None
                       ) -> set[str]:
    """The set of partitions an iterable of variants spans (unassignable
    records do not count — they are candidates, not evidence of a mix)."""
    return {p for p, _ in (assign_partition(v, domain_hits) for v in variants)
            if p}


def split_by_partition(variants: Iterable, domain_hits: Optional[dict] = None,
                       unassigned_to: Optional[str] = None
                       ) -> "OrderedDict[Optional[str], list]":
    """Split a mixed set into one bucket per partition.

    Unassignable records go to their own `None` bucket unless
    `unassigned_to` names a partition to fold them into. They are never
    silently dropped and never duplicated across partitions: a candidate
    scored twice against two unrelated families is the D14 error wearing a
    different hat.
    """
    buckets: "OrderedDict[Optional[str], list]" = OrderedDict(
        (k, []) for k in PARTITION_KEYS)
    buckets[None] = []
    for v in variants:
        key, _ = assign_partition(v, domain_hits)
        if key is None and unassigned_to in FAMILY_PARTITIONS:
            key = unassigned_to
        buckets[key].append(v)
    return buckets


def assert_single_partition(variants: Iterable,
                            domain_hits: Optional[dict] = None,
                            context: str = "this analysis") -> Optional[str]:
    """Raise unless every assignable record belongs to one partition.

    Returns the partition key (or None if nothing was assignable), so the
    caller can record which family a number came from — D14 requires every
    report to say so.
    """
    present = partitions_present(variants, domain_hits)
    if len(present) > 1:
        counts = {k: len(v) for k, v in
                  split_by_partition(variants, domain_hits).items() if v}
        raise CrossPartitionError(
            f"{context} spans {len(present)} unrelated families "
            f"({', '.join(sorted(present))}; counts {counts}). JPT and LSM12 "
            "share a ligand and nothing else — no common domain, no "
            "detectable similarity, no alignable ancestry — so an identity, "
            "a tree or a novelty score computed across them is noise wearing "
            "a decimal point (roadmap D14). Run one partition at a time "
            "(src.discovery.partition.run_partitioned_discovery), or pass "
            "allow_cross_partition=True if you are deliberately measuring "
            "the distortion."
        )
    return next(iter(present), None)
