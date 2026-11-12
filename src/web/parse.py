"""Parsers for the committed outputs: TSV/CSV tables, the roadmap ledger, and FINDINGS.md pending markers.

Pure functions over text; reading (and provenance) is done by committed.py. Nothing here computes a new number: it
only turns committed text into rows the browser can lay out.
"""
from __future__ import annotations

import csv
import io
import re

ROW_CAP = 2000  # largest committed table today is scores.tsv at 546 rows; cap keeps the static site small


def table(text: str, delimiter: str = "\t", cap: int = ROW_CAP) -> dict:
    """{'columns': [...], 'rows': [[...]], 'n_rows': total, 'truncated': bool} from delimited text."""
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [r for r in reader if r]
    if not rows:
        return {"columns": [], "rows": [], "n_rows": 0, "truncated": False}
    cols, body = rows[0], rows[1:]
    return {"columns": cols, "rows": body[:cap], "n_rows": len(body), "truncated": len(body) > cap}


def records(text: str, delimiter: str = "\t") -> list[dict]:
    return list(csv.DictReader(io.StringIO(text), delimiter=delimiter))


def delimiter_for(path: str) -> str:
    return "," if path.endswith(".csv") else "\t"


# --- markdown tables (roadmap ledger) --------------------------------------------------------------------------------
def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def md_tables(text: str) -> list[dict]:
    """Every pipe table in a markdown document, with the nearest heading above it."""
    out, heading, lines, i = [], "", text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            cols = _cells(line)
            j, rows = i + 2, []
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = _cells(lines[j])
                rows.append(dict(zip(cols, cells + [""] * (len(cols) - len(cells)))))
                j += 1
            out.append({"heading": heading, "columns": cols, "rows": rows})
            i = j
            continue
        i += 1
    return out


def status_kind(status: str) -> str:
    """Map the repo's own status words onto a display class (the words themselves are always shown verbatim)."""
    s = re.sub(r"[*`]", "", status).strip().lower()
    if s.startswith("completed") or s.startswith("closed"):
        return "done"
    if s.startswith("in_progress") or s.startswith("in progress"):
        return "active"
    if s.startswith("open"):
        return "open"
    return "pending"


def ledger(text: str) -> dict:
    """The task ledger, the analysis block and the emergent-task table from PUBLICATION_ROADMAP.md."""
    main, analysis, emergent = [], [], []
    for t in md_tables(text):
        cols = t["columns"]
        if cols[:2] == ["ID", "Task (one session each)"]:
            main = [_task(r, "Task (one session each)") for r in t["rows"]]
        elif cols[:2] == ["ID", "Task"] and "Priority" in cols:
            analysis = [_task(r, "Task") for r in t["rows"]]
        elif cols[:3] == ["Added", "From", "Task"]:
            emergent = [{**r, "kind": status_kind(r.get("Status", ""))} for r in t["rows"]]
    m = re.search(r"^> \*\*Next session: ([^*]+)\*\*", text, re.M)
    return {"main": main, "analysis": analysis, "emergent": emergent, "next": m.group(1).strip(" .") if m else None}


def _task(row: dict, task_col: str) -> dict:
    status = row.get("Status", "")
    return {"id": re.sub(r"[*]", "", row.get("ID", "")), "task": row.get(task_col, ""), "depends": row.get("Depends", ""),
            "priority": row.get("Priority", ""), "status": status, "kind": status_kind(status),
            "result": row.get("Results (headline)", row.get("Results", ""))}


# --- FINDINGS.md pending markers -------------------------------------------------------------------------------------
PENDING_RE = re.compile(r"\(pending:\s*([^)]+)\)")
TASK_RE = re.compile(r"\bS\d+[a-z]?\b")


def pending_markers(text: str) -> list[dict]:
    """Every '(pending: ...)' marker in FINDINGS.md with the entry heading it sits under and the tasks it names."""
    out, heading = [], ""
    for n, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            heading = line[3:].strip()
        for m in PENDING_RE.finditer(line):
            if m.group(1).strip().startswith("which task"):  # the file's own description of the convention
                continue
            out.append({"line": n, "entry": heading, "marker": m.group(0), "tasks": TASK_RE.findall(m.group(1))})
    return out
