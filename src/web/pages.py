"""Project-level pages: overview (headline numbers), ledger, findings, trees, reports and the table browser.

Every headline number is read from a committed file at build time; each comes with the file, the exact cell/key or
row filter that produced it, and that file's commit (see committed.provenance).
"""
from __future__ import annotations

from . import committed as C
from .panels import S0, S1, figures_under, js, recs
from .parse import delimiter_for, ledger as parse_ledger, pending_markers, table

ROADMAP = "PUBLICATION_ROADMAP.md"
FINDINGS = "FINDINGS.md"
TREE_EXT = (".nwk", ".newick", ".treefile", ".contree", ".tre", ".nex")
TABLE_EXT = (".tsv", ".csv")
REPORT_DOCS = ["docs/naadp_binder_review_2026.md"]  # rendered from committed tables by s0_report.py (D13)


def ledger_data() -> dict:
    d = parse_ledger(C.read_text(ROADMAP))
    tasks = d["main"] + d["analysis"]
    d["counts"] = {k: sum(t["kind"] == k for t in tasks) for k in ("done", "active", "pending")}
    d["counts"]["total"] = len(tasks)
    d["provenance"] = C.prov(ROADMAP)
    return d


def _status_of(ids: list[str], led: dict) -> list[dict]:
    by = {t["id"]: t for t in led["main"] + led["analysis"]}
    return [{"id": i, "status": by[i]["status"] if i in by else "not in ledger",
             "kind": by[i]["kind"] if i in by else "pending"} for i in ids]


def _count(path: str, where: dict, of: dict | None = None) -> dict:
    """Rows of `path` matching `where` (and the size of the `of` subset), with the filter for provenance."""
    rows = recs(path)
    base = [r for r in rows if all(r.get(k) == v for k, v in (of or {}).items())]
    hit = [r for r in base if all(r.get(k) == v for k, v in where.items())]
    return {"value": len(hit), "of": len(base), "how": f"rows where {where} among rows where {of or 'all'}"}


def _cell(path: str, match: dict, col: str) -> dict:
    for r in recs(path):
        if all(r.get(k) == v for k, v in match.items()):
            return {"value": r[col], "how": f"column {col} where {match}"}
    raise KeyError(f"{path}: no row {match}")


def overview() -> dict:
    led = ledger_data()
    s = js(S1 + "summary.json")
    lit = js(S0 + "lit_audit_meta.json")
    trees = [p for p in C.tracked("") if p.endswith(TREE_EXT)]
    sister_on = _count(S1 + "scores.tsv", {"promoted": "True"}, {"run": "part_baseline", "group": "JPT1 (sister paralog)"})
    sister_off = _count(S1 + "scores.tsv", {"promoted": "True"}, {"run": "part_nosister", "group": "JPT1 (sister paralog)"})
    tiles = [
        {"label": "ledger tasks completed", "value": f'{led["counts"]["done"]}/{led["counts"]["total"]}',
         "how": "rows of the task ledger + analysis block whose Status starts 'completed'", "provenance": led["provenance"]},
        {"label": "literature claims audited", "value": lit["n_claims"], "how": "n_claims",
         "provenance": C.prov(S0 + "lit_audit_meta.json")},
        {"label": "references in the audit", "value": lit["n_references"], "how": "n_references",
         "provenance": C.prov(S0 + "lit_audit_meta.json")},
        {"label": "of IPR033335 covered by PF17054", **_cell(S0 + "signature_scope.tsv", {"pfam": "PF17054"},
                                                              "pfam_fraction_of_interpro"),
         "provenance": C.prov(S0 + "signature_scope.tsv")},
        {"label": "benchmark positives / decoys", "value": f'{s["n_positive_records"]}/{s["n_decoy_records"]}',
         "how": "n_positive_records / n_decoy_records", "provenance": C.prov(S1 + "summary.json")},
        {"label": "JPT1 decoys promoted, sister test OFF", "value": f'{sister_off["value"]}/{sister_off["of"]}',
         "how": sister_off["how"], "provenance": C.prov(S1 + "scores.tsv")},
        {"label": "JPT1 decoys promoted, sister test ON", "value": f'{sister_on["value"]}/{sister_on["of"]}',
         "how": sister_on["how"], "provenance": C.prov(S1 + "scores.tsv")},
        {"label": "unnamed recall, + signature fallback",
         "value": f'{s["part_anonymised_recall_hit"]}/{s["part_anonymised_recall_n"]} -> '
                  f'{s["part_anon_sigset_recall_hit"]}/{s["part_anon_sigset_recall_n"]}',
         "how": "part_anonymised_recall_hit/_n -> part_anon_sigset_recall_hit/_n", "provenance": C.prov(S1 + "summary.json")},
        {"label": "max cross-family identity (full alignment)",
         **_cell(S1 + "crossfamily_identity.tsv", {"metric": "full alignment",
                                                   "pair_class": "across families (JPT vs LSM12)"}, "max_identity"),
         "provenance": C.prov(S1 + "crossfamily_identity.tsv")},
        {"label": "phylogenetic trees committed", "value": len(trees),
         "how": f"files at HEAD ending {', '.join(TREE_EXT)}", "provenance": [],
         "pending": _status_of(["S7"], led) if not trees else []},
    ]
    return {"head": C.head(), "next": led["next"], "counts": led["counts"], "tiles": tiles,
            "stages": [t for t in led["main"] if t["kind"] != "pending"]}


def findings() -> dict:
    text = C.read_text(FINDINGS)
    led = ledger_data()
    marks = pending_markers(text)
    for m in marks:
        m["task_status"] = _status_of(m["tasks"], led)
        m["all_done"] = bool(m["tasks"]) and all(t["kind"] == "done" for t in m["task_status"])
    return {"markdown": text, "markers": marks, "provenance": C.prov(FINDINGS, ROADMAP)}


def trees() -> dict:
    led = ledger_data()
    found = [p for p in C.tracked("") if p.endswith(TREE_EXT)]
    return {"trees": [{"path": p, "provenance": C.provenance(p)} for p in found],
            "extensions": list(TREE_EXT), "tasks": _status_of(["S6", "S7", "S13", "S16"], led),
            "rows": [t for t in led["main"] + led["analysis"] if t["id"] in ("S6", "S7", "S13", "S16")],
            "provenance": led["provenance"], "head": C.head()}


def report_paths() -> list[str]:
    reps = [p for p in C.tracked("results/") if p.endswith("report.md")]
    return reps + [p for p in REPORT_DOCS if C.exists(p)]


def reports() -> dict:
    return {"reports": [{"path": p, "provenance": C.provenance(p)} for p in report_paths()]}


def report(path: str) -> dict:
    if path not in report_paths():
        raise FileNotFoundError(path)
    return {"path": path, "markdown": C.read_text(path), "provenance": C.prov(path)}


def table_paths() -> list[str]:
    return [p for p in C.tracked("results/") if p.endswith(TABLE_EXT)]


def tables() -> dict:
    out = []
    for p in table_paths():
        t = table(C.read_text(p), delimiter_for(p), cap=0)
        out.append({"path": p, "columns": len(t["columns"]), "rows": t["n_rows"], "provenance": C.provenance(p)})
    return {"tables": out}


def one_table(path: str) -> dict:
    if path not in table_paths():
        raise FileNotFoundError(path)
    return {"path": path, "table": table(C.read_text(path), delimiter_for(path)), "provenance": C.prov(path)}


def figure_paths() -> list[str]:
    return figures_under("results/")
