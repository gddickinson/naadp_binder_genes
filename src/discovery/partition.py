"""Run the discovery scorer once per family, never once across both (D14).

`candidates.py:discover_novel_paralogs` now *refuses* a set that spans the
JPT and LSM12 families. This module is the other half of that change: the
route a mixed set is supposed to take.

The important design point is that partitioning happens **before the
alignment**, not after it. Subsetting a joint distance matrix would still
leave the matrix itself — and every cell in it a JPT2-vs-LSM12 "identity"
that some later analysis could read. Instead each partition gets its own
MSA, its own identity matrix and its own tree, so a cross-family number has
nowhere to exist. That also makes the alignments better in their own right:
MAFFT aligning two unalignable families produces a wide, mostly-gap matrix
whose conservation columns are meaningless for either.

What comes back is one `PartitionRun` per family, each carrying its own
analysis and report, plus the unassignable records as an explicit list —
never silently dropped, because this project's headline deliverable is an
absence claim and a quiet drop is indistinguishable from a real absence
(the D24 lesson, applied to partitioning).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

from ..analysis.pipeline import AnalysisResult, _label_for, analyse
from ..core.models import ProteinVariant
from ..utils.family import FAMILY_PARTITIONS
from ..utils.partitions import assign_partition, split_by_partition
from .candidates import (Candidate, DiscoveryConfig, DiscoveryReport,
                         build_signature_set, discover_novel_paralogs)


@dataclass
class PartitionRun:
    """One family's analysis + discovery, and nothing from the other."""

    key: str
    variants: list[ProteinVariant] = field(default_factory=list)
    analysis: Optional[AnalysisResult] = None
    report: Optional[DiscoveryReport] = None
    label_map: dict[str, str] = field(default_factory=dict)
    signature_blocks: int = 0
    note: str = ""

    def candidates(self) -> list[Candidate]:
        return list(self.report.candidates) if self.report else []


def known_for_partition(key: str, known_paralogs: Iterable[str]) -> list[str]:
    """The subset of `known_paralogs` that actually belongs to `key`.

    Passing "LSM12" as a known paralog into the JPT run would make every
    JPT candidate's "identity to nearest known" a JPT-vs-LSM12 number —
    the exact quantity D14 forbids — so the known set is partitioned too.
    """
    members = {m.upper() for m in FAMILY_PARTITIONS[key]["members"]}
    return [p for p in known_paralogs if p.upper() in members]


def _label(v: ProteinVariant) -> str:
    return f"{v.source}|{v.accession}|{v.gene_symbol}"


def run_partitioned_discovery(
    variants: Iterable[ProteinVariant],
    known_paralogs: Iterable[str],
    domain_hits: Optional[dict] = None,
    foldseek_hits: Optional[list[ProteinVariant]] = None,
    use_mafft: bool = True,
    identity_threshold: float = 0.4,
    max_variants: Optional[int] = None,
    config_overrides: Optional[dict] = None,
    unassigned_to: Optional[str] = None,
    signature_sets: Optional[dict] = None,
    analyse_fn: Optional[Callable] = None,
    log: Callable[[str], None] = print,
) -> tuple[dict[str, PartitionRun], list[ProteinVariant]]:
    """Analyse and score each family separately.

    Returns `({partition key: PartitionRun}, unassignable variants)`. A
    partition with fewer than two sequences gets a `PartitionRun` with no
    report and a `note` saying why — an empty result and a skipped result
    must not look the same.
    """
    variants = list(variants)
    known_paralogs = list(known_paralogs)
    domain_hits = domain_hits or {}
    analyse_fn = analyse_fn or analyse
    buckets = split_by_partition(variants, domain_hits,
                                 unassigned_to=unassigned_to)
    unassigned = buckets.pop(None, [])
    if unassigned:
        log(f"[partition] {len(unassigned)} record(s) unassignable to either "
            f"family — reported, not scored: "
            f"{', '.join(v.accession for v in unassigned[:6])}"
            f"{' …' if len(unassigned) > 6 else ''}")

    runs: dict[str, PartitionRun] = {}
    for key, members in buckets.items():
        run = PartitionRun(key=key, variants=members)
        runs[key] = run
        with_seq = [v for v in members if v.sequence]
        if len(with_seq) < 2:
            run.note = (f"skipped — {len(with_seq)} sequence(s) in this "
                        f"partition, too few to align or score")
            log(f"[partition:{key}] {run.note}")
            continue

        log(f"[partition:{key}] {len(members)} records "
            f"({len(with_seq)} with sequence) — aligning…")
        run.analysis = analyse_fn(
            members, identity_threshold=identity_threshold,
            use_mafft=use_mafft,
            max_variants=max_variants if max_variants else len(members))
        run.label_map = {_label(v): _label_for(v) for v in members}
        known_here = known_for_partition(key, known_paralogs)
        # A caller may supply a signature set derived elsewhere — the
        # benchmark carries the set built from *named* members into the
        # anonymised run, because that is how production works: the family
        # has named members and the candidate does not. Deriving it from
        # an anonymised set instead yields one row and no PSSM at all.
        sset = ((signature_sets or {}).get(key)
                or build_signature_set(members, run.analysis.msa,
                                       run.label_map, known_here))
        run.signature_blocks = len(sset.signatures) if sset else 0
        cfg = DiscoveryConfig(known_paralogs=known_here, partition=key,
                              **(config_overrides or {}))
        run.report = discover_novel_paralogs(
            members, cfg, analysis_label_for=run.label_map,
            distances=run.analysis.distances, domain_hits=domain_hits,
            foldseek_hits=foldseek_hits, signature_set=sset)
        promoted = sum(1 for c in run.report.candidates if c.score >= 40)
        log(f"[partition:{key}] {len(run.report.candidates)} candidates, "
            f"{promoted} promoted (known here: "
            f"{', '.join(known_here) or 'none'})")
    return runs, unassigned


def merge_reports(runs: dict[str, PartitionRun]) -> DiscoveryReport:
    """Flatten per-partition reports into one ranked list for display.

    Every candidate keeps a `partition` evidence line, because a score is
    only interpretable next to the family it was computed in (D14). The
    merged report is for *presentation*; nothing may recompute a distance
    from it.
    """
    merged: list[Candidate] = []
    cfg: Optional[DiscoveryConfig] = None
    notes: list[str] = []
    for key, run in runs.items():
        if run.report is None:
            notes.append(f"[{key}] {run.note}")
            continue
        cfg = cfg or run.report.config
        notes.extend(f"[{key}] {n}" for n in run.report.notes)
        for c in run.report.candidates:
            c.evidence["partition"] = (
                f"{key} family — scored only against {key} members "
                "(roadmap D14)")
            merged.append(c)
    merged.sort(key=lambda c: -c.score)
    return DiscoveryReport(config=cfg or DiscoveryConfig(known_paralogs=[]),
                           candidates=merged, notes=notes)


def partition_table(variants: Iterable[ProteinVariant],
                    domain_hits: Optional[dict] = None) -> list[dict]:
    """Per-record partition assignment with the reason it was made — the
    auditable form of the split, for committing alongside any result."""
    rows = []
    for v in variants:
        key, why = assign_partition(v, domain_hits)
        rows.append({
            "accession": v.accession, "gene_symbol": v.gene_symbol,
            "species": v.species, "length_aa": v.length_aa or "",
            "partition": key or "unassigned", "assigned_by": why,
        })
    return rows
