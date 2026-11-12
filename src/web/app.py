"""FastAPI web app for the NAADP-binder census dashboard: the front end in static/ and a read-only JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8175, local only). Every response is built from files committed at git
HEAD (see committed.py), never from the working tree. `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON, and every path in STATIC_FILES as bytes, for the GitHub Pages site.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from . import committed as C
from . import pages, panels

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="NAADP binder census")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


def _guard(fn, *a):
    try:
        return fn(*a)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/api/info")
def info():
    return {"title": "NAADP binder census", "repo": C.REPO_URL, "head": C.head()}


@app.get("/api/overview")
def overview():
    return pages.overview()


@app.get("/api/ledger")
def ledger():
    return pages.ledger_data()


@app.get("/api/baseline")
def baseline():
    return panels.baseline()


@app.get("/api/literature")
def literature():
    return panels.literature()


@app.get("/api/benchmark")
def benchmark():
    return panels.benchmark()


@app.get("/api/findings")
def findings():
    return pages.findings()


@app.get("/api/trees")
def trees():
    return pages.trees()


@app.get("/api/reports")
def reports():
    return pages.reports()


@app.get("/api/report/{path:path}")
def report(path: str):
    return _guard(pages.report, path)


@app.get("/api/tables")
def tables():
    return pages.tables()


@app.get("/api/table/{path:path}")
def table(path: str):
    return _guard(pages.one_table, path)


@app.get("/api/file/{path:path}")
def file(path: str):
    """A committed figure (PNG under results/*/figures/), served from HEAD."""
    if path not in pages.figure_paths():
        raise HTTPException(404, "not a committed figure")
    return Response(C.read_bytes(path), media_type="image/png")


def static_endpoints() -> list[str]:
    fixed = ["/info", "/overview", "/ledger", "/baseline", "/literature", "/benchmark", "/findings", "/trees",
             "/reports", "/tables"]
    return fixed + [f"/report/{p}" for p in pages.report_paths()] + [f"/table/{p}" for p in pages.table_paths()]


# GET paths (without the /api prefix) written to the static site as api/<path>.json, and binary files as api/<path>.
STATIC_ENDPOINTS = static_endpoints()
STATIC_FILES = [f"/file/{p}" for p in pages.figure_paths()]
