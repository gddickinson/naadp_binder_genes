"""Persist a `DiscoveryReport` to disk.

Split out of `candidates.py` so the scorer file stays under the project's
500-line rule. Shared by the CLI, the domain scan, the exhaustive hunt and
the GUI bundle writer, so the on-disk schema is identical everywhere — a
second copy of this writer is how two runs of the same pipeline end up
with two different `candidates.tsv` schemas.
"""

from __future__ import annotations

from pathlib import Path


def write_discovery(out_dir: Path, report: DiscoveryReport) -> dict:
    """Persist a discovery report as `report.txt` + `candidates.tsv`.

    Shared by the CLI, the domain scan, and the GUI bundle writer so the
    on-disk schema stays identical everywhere. Returns the paths written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    text_path = out_dir / "report.txt"
    text_path.write_text(report.text_summary())
    tsv_path = out_dir / "candidates.tsv"
    with tsv_path.open("w") as f:
        f.write("score\tverdict\tlabel\taccession\tspecies\tlength_aa\treviewed\t"
                "size\tdomain\tfold\toutlier\tbreadth\tcluster\tnearest_in_set\n")
        for c in report.candidates:
            ev = c.evidence
            f.write("\t".join([
                str(c.score), c.verdict(), c.label, c.variant.accession,
                c.variant.species or "", str(c.variant.length_aa or ""),
                c.variant.raw.get("reviewed", ""),
                ev.get("size", ""), ev.get("domain", ""), ev.get("fold", ""),
                ev.get("outlier", ""), ev.get("breadth", ""), ev.get("cluster", ""),
                ev.get("nearest_in_set", ""),
            ]) + "\n")
    return {"report_txt": str(text_path), "candidates_tsv": str(tsv_path)}
