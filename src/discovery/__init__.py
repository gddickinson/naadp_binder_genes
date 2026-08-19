"""Novel-paralog discovery pipeline.

Glues together the analysis module (sequence outlier detection) with
structure / domain / orthology cross-checks to score and rank candidates
for being a *novel paralog* of the query gene family — e.g. a hypothetical
a third vertebrate NAADP binder.

Contents:
    candidates.py — composite scoring + ranked report
    writer.py     — DiscoveryReport → candidates.tsv + report.txt
    partition.py  — one analysis + one scorer run per family (D14)
"""

from .candidates import (
    DiscoveryConfig,
    DiscoveryReport,
    Candidate,
    build_signature_set,
    discover_novel_paralogs,
)
from .writer import write_discovery
from .partition import (PartitionRun, merge_reports, partition_table,
                        run_partitioned_discovery)
from .domain_scan import run_domain_scan
from .exhaustive import run_exhaustive_hunt

__all__ = [
    "DiscoveryConfig", "DiscoveryReport", "Candidate", "build_signature_set",
    "discover_novel_paralogs", "write_discovery", "run_domain_scan",
    "PartitionRun", "run_partitioned_discovery", "merge_reports",
    "partition_table",
    "run_exhaustive_hunt",
]
