"""Shared helpers for the S1 control benchmark (see s1_benchmark.py).

Five responsibilities:

* prove that `analyse(use_mafft=True)` really shells out to MAFFT
  (`MafftTracer`; `alignment.py:_mafft` falls back to the star alignment
  *silently* on a non-zero return code, so the return code is the
  evidence, not the fact that a call happened);
* the **anonymised hold-out** — this family's version of a name hold-out;
* look candidates up in a `DiscoveryReport` and decode which scorer
  components fired;
* the JPT2-vs-JPT1 labelled-bait margin that operationalises D14/D7;
* TSV output.

**Why the hold-out had to change.** The sibling projects hold out one
paralog name at a time and check that its orthologs still surface. That
works when a family has three members: hiding ITPR1 leaves ITPR2/ITPR3 as
the known set. Here each partition has exactly **one** binder member, so
hiding it leaves `known_paralogs` empty and every distance-based component
— outlier, cluster, and the sister-family test itself — has nothing to
measure against. The hold-out would not be testing the scorer, it would be
disabling half of it.

So the hold-out is done on the records instead of the symbol list: the
human reference keeps its name, and every other true member enters wearing
a locus-style ID (`LOC<accession>`), exactly as an unannotated ortholog
arrives from a genome sweep. That is the real use case anyway — a true
family member the symbol filter does not recognise — and it keeps one
named member per partition so the scorer's machinery still runs.
"""

from __future__ import annotations

import copy
import subprocess
from pathlib import Path
from typing import Optional

#: The labelled baits the D14/D7 margin is measured against. JPT only:
#: LSM12 has no declared sister family, which is itself a reported result.
JPT_BAIT_ACCS = ["Q9H910"]                    # human JPT2
JPT1_BAIT_ACCS = ["Q9UK76", "P97825"]         # human + mouse JPT1


class MafftTracer:
    """Record every subprocess call to mafft while active."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._orig = None

    def __enter__(self) -> "MafftTracer":
        self._orig = subprocess.run

        def traced(cmd, *args, **kwargs):
            result = self._orig(cmd, *args, **kwargs)
            prog = str(cmd[0]) if isinstance(cmd, (list, tuple)) and cmd else str(cmd)
            if "mafft" in prog:
                self.calls.append({
                    "argv": list(cmd) if isinstance(cmd, (list, tuple)) else [prog],
                    "returncode": result.returncode,
                    "stdout_bytes": len(result.stdout or ""),
                })
            return result

        subprocess.run = traced
        return self

    def __exit__(self, *exc) -> None:
        subprocess.run = self._orig

    def ok(self) -> bool:
        return bool(self.calls) and all(c["returncode"] == 0 for c in self.calls)


def anonymise(variants, keep_named: set[str]):
    """Return a copy of `variants` with every positive control's symbol
    replaced by a locus-style ID, except the accessions in `keep_named`.

    Decoys keep their symbols: in production JPT1 arrives correctly
    labelled, and the sister-family test needs at least one *labelled*
    sister bait to measure against.
    """
    out = []
    for v in variants:
        if v.raw.get("panel_kind") != "positive" or v.accession in keep_named:
            out.append(v)
            continue
        c = copy.deepcopy(v)
        c.raw["named_symbol"] = v.gene_symbol
        c.gene_symbol = f"LOC{v.accession}"
        out.append(c)
    return out


def dedup_key(v) -> tuple[str, str, Optional[int]]:
    """The key `discover_novel_paralogs` collapses candidates on."""
    return (v.gene_symbol.upper(), v.species, v.length_aa)


def score_lookup(report):
    """label → Candidate, with a dedup-key fallback."""
    if report is None:
        return lambda v: None
    by_label = {c.label: c for c in report.candidates}
    by_key = {dedup_key(c.variant): c for c in report.candidates}

    def lookup(v):
        lbl = f"{v.source}|{v.accession}|{v.gene_symbol}"
        return by_label.get(lbl) or by_key.get(dedup_key(v))

    return lookup


def components(cand) -> str:
    """Compact list of which scorer components fired, read back out of the
    evidence text. Mirrors src/discovery/candidates.py component by
    component; a change there must be reflected here."""
    if cand is None:
        return ""
    ev = cand.evidence
    flags = []
    if "within family band" in ev.get("size", ""):
        pts = ev["size"].rsplit("(+", 1)[-1].rstrip(")") if "(+" in ev["size"] else "15"
        flags.append(f"size+{pts}")
    dom = ev.get("domain", "")
    if dom.startswith("Pfam signature present"):
        flags.append("pfam+20")
    elif dom.startswith("MSA-signature fallback"):
        flags.append("sig+15")
    if "≥" in ev.get("fold", ""):
        flags.append("fold+20")
    if "paralog twilight zone" in ev.get("outlier", ""):
        flags.append("outlier+20")
    if ev.get("cluster", "").startswith("outside known paralog clusters"):
        flags.append("cluster+10")
    if ev.get("breadth", "").startswith("present in"):
        flags.append("breadth+15")
    if "homology" in ev:
        flags.append("homology+10")
    if "annotation" in ev:
        flags.append("split+10")
    if "sister_cap" in ev:
        flags.append("SISTER→39")
    if "gate" in ev:
        flags.append("GATED→39")
    return ",".join(f for f in flags if not f.endswith("+0"))


def sister_margin(cand) -> str:
    if cand is None:
        return ""
    ev = cand.evidence.get("sister_margin", "")
    return ev.split("margin ")[-1].strip() if "margin " in ev else ""


def nearest_known_identity(cand) -> str:
    """The identity-to-nearest-known figure the outlier component used."""
    if cand is None:
        return ""
    ev = cand.evidence.get("outlier", "")
    if "= " not in ev:
        return ""
    tail = ev.split("= ")[-1]
    return tail.split("%")[0].strip() if "%" in tail else ""


def nearest_in_set(cand) -> str:
    """The nearest neighbour of any kind — the number that shows what a
    cross-family run actually compared a candidate against."""
    return "" if cand is None else cand.evidence.get("nearest_in_set", "")


def bait_margins(distances, label_by_acc: dict[str, str]) -> dict[str, dict]:
    """Per-label JPT2-vs-JPT1 labelled-bait margin (roadmap D7/D14).

    For every row of the distance matrix: best identity to any human JPT2
    bait, best identity to any labelled JPT1 bait, the call and the
    margin. A bait's own row excludes itself.
    """
    if distances is None or not distances.labels:
        return {}
    idx = {lbl: i for i, lbl in enumerate(distances.labels)}
    jpt_labels = [label_by_acc[a] for a in JPT_BAIT_ACCS if a in label_by_acc]
    jpt1_labels = [label_by_acc[a] for a in JPT1_BAIT_ACCS if a in label_by_acc]

    def best(i: int, bait_labels: list[str]) -> tuple[str, float]:
        hit, score = "", 0.0
        for b in bait_labels:
            j = idx.get(b)
            if j is None or j == i:
                continue
            v = distances.identity[i][j]
            if v > score:
                hit, score = b, v
        return hit, score

    out: dict[str, dict] = {}
    for lbl, i in idx.items():
        j_hit, j_id = best(i, jpt_labels)
        d_hit, d_id = best(i, jpt1_labels)
        out[lbl] = {
            "best_jpt2_bait": j_hit, "id_to_jpt2": j_id,
            "best_jpt1_bait": d_hit, "id_to_jpt1": d_id,
            "margin": j_id - d_id,
            "call": "JPT2" if j_id > d_id else ("JPT1" if d_id > j_id else "tie"),
        }
    return out


def write_tsv(path: Path, rows: list[dict], cols: list[str] | None = None) -> int:
    """Write dict rows as TSV. Column order from `cols`, else first row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\t".join(cols or []) + "\n")
        return 0
    cols = cols or list(rows[0].keys())
    with path.open("w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")) for c in cols) + "\n")
    return len(rows)


def read_tsv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text().splitlines()
    if not lines:
        return []
    cols = lines[0].split("\t")
    return [dict(zip(cols, ln.split("\t"))) for ln in lines[1:] if ln.strip()]
