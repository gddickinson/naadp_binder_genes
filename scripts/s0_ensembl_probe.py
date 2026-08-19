#!/usr/bin/env python
"""S0 — probe the Ensembl REST endpoints the app depends on, with timings.

`INTERFACE.md` records that the symbol-resolution path was changed because
`/xrefs/symbol/homo_sapiens/…` stalls while `/lookup/symbol` works. That
claim needs its evidence file in this repo, and the app's own smoke test
needs to know which endpoint is the slow one.

Each probe is bounded by an explicit timeout and records the wall-clock time
and the outcome, so a stall is reported as a stall rather than waited on.

Writes `results/s0_baseline/ensembl_endpoint_probe.tsv`.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.s0_lib import write_tsv  # noqa: E402

OUT = ROOT / "results" / "s0_baseline"
BASE = "https://rest.ensembl.org"
HEADERS = {"Content-Type": "application/json",
           "User-Agent": "naadp_binder_genes/S0"}

#: (label, path) pairs. Both symbol-resolution routes are probed on the same
#: gene in the same species so the comparison is like-for-like, plus the
#: control gene INTERFACE.md names (BRCA2) and a non-human species.
PROBES = [
    ("lookup/symbol human LSM12",   "/lookup/symbol/homo_sapiens/LSM12"),
    ("xrefs/symbol human LSM12",    "/xrefs/symbol/homo_sapiens/LSM12"),
    ("lookup/symbol human JPT2",    "/lookup/symbol/homo_sapiens/JPT2"),
    ("xrefs/symbol human JPT2",     "/xrefs/symbol/homo_sapiens/JPT2"),
    ("lookup/symbol human BRCA2",   "/lookup/symbol/homo_sapiens/BRCA2"),
    ("xrefs/symbol human BRCA2",    "/xrefs/symbol/homo_sapiens/BRCA2"),
    ("lookup/symbol mouse Lsm12",   "/lookup/symbol/mus_musculus/Lsm12"),
    ("xrefs/symbol mouse Lsm12",    "/xrefs/symbol/mus_musculus/Lsm12"),
    ("lookup/symbol zfish lsm12",   "/lookup/symbol/danio_rerio/lsm12"),
    ("xrefs/symbol zfish lsm12",    "/xrefs/symbol/danio_rerio/lsm12"),
    ("ping",                        "/info/ping"),
]

TIMEOUT_S = 30


def probe(label: str, path: str) -> dict:
    t0 = time.time()
    try:
        r = requests.get(BASE + path, headers=HEADERS, timeout=TIMEOUT_S)
        dt = time.time() - t0
        n = 0
        try:
            j = r.json()
            n = len(j) if isinstance(j, list) else 1
        except Exception:
            n = 0
        return {"probe": label, "path": path, "status": r.status_code,
                "seconds": round(dt, 2), "n_records": n,
                "outcome": "ok" if r.ok else f"HTTP {r.status_code}"}
    except requests.Timeout:
        return {"probe": label, "path": path, "status": "",
                "seconds": round(time.time() - t0, 2), "n_records": 0,
                "outcome": f"TIMEOUT at {TIMEOUT_S}s"}
    except Exception as exc:  # noqa: BLE001
        return {"probe": label, "path": path, "status": "",
                "seconds": round(time.time() - t0, 2), "n_records": 0,
                "outcome": f"error: {type(exc).__name__}"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, path in PROBES:
        r = probe(label, path)
        rows.append(r)
        print(f"  {r['outcome']:>16}  {r['seconds']:>6.2f}s  "
              f"{r['n_records']:>3} rec  {label}")
        time.sleep(0.3)

    write_tsv(OUT / "ensembl_endpoint_probe.tsv", rows,
              ["probe", "path", "status", "seconds", "n_records", "outcome"])

    lookups = [r for r in rows if r["probe"].startswith("lookup")]
    xrefs = [r for r in rows if r["probe"].startswith("xrefs")]

    def mean(rs):
        ok = [r["seconds"] for r in rs if r["outcome"] == "ok"]
        return sum(ok) / len(ok) if ok else float("nan")

    print(f"\n  lookup/symbol: {sum(1 for r in lookups if r['outcome']=='ok')}"
          f"/{len(lookups)} ok, mean {mean(lookups):.2f}s")
    print(f"  xrefs/symbol : {sum(1 for r in xrefs if r['outcome']=='ok')}"
          f"/{len(xrefs)} ok, mean {mean(xrefs):.2f}s")
    print(f"\n[S0] wrote {OUT / 'ensembl_endpoint_probe.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
