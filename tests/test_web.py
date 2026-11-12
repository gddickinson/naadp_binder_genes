"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- project-specific: provenance, read-only, committed-only, numbers traceable --------------------------------------
from src.web import committed as C  # noqa: E402
from src.web import pages  # noqa: E402
from src.web.parse import md_tables, pending_markers, status_kind, table  # noqa: E402


def test_overview_tiles_carry_provenance_or_pending():
    for t in client.get("/api/overview").json()["tiles"]:
        assert t["how"], t
        assert t["provenance"] or t.get("pending"), t
        for p in t["provenance"]:
            assert p["commit"] and len(p["sha256"]) == 16


def test_every_panel_has_provenance():
    for page in ("/baseline", "/literature", "/benchmark"):
        for p in client.get("/api" + page).json()["panels"]:
            assert p["provenance"], (page, p["id"])


def test_jpt1_headline_agrees_across_two_committed_tables():
    """The sister-test headline is counted from scores.tsv; summary.json records the same experiment independently."""
    tiles = {t["label"]: t["value"] for t in client.get("/api/overview").json()["tiles"]}
    s = json.loads(C.read_text("results/benchmark_controls/summary.json"))
    off = s["part_nosister_jpt1_n"] - s["part_nosister_jpt1_pass"]
    on = s["part_baseline_jpt1_n"] - s["part_baseline_jpt1_pass"]
    assert tiles["JPT1 decoys promoted, sister test OFF"] == f'{off}/{s["part_nosister_jpt1_n"]}'
    assert tiles["JPT1 decoys promoted, sister test ON"] == f'{on}/{s["part_baseline_jpt1_n"]}'


def test_ledger_statuses_parsed_from_roadmap():
    d = client.get("/api/ledger").json()
    ids = [t["id"] for t in d["main"] + d["analysis"]]
    assert "S0" in ids and "S7" in ids and len(ids) == d["counts"]["total"]
    for t in d["main"] + d["analysis"]:
        assert t["kind"] == status_kind(t["status"])


def test_pending_markers_name_ledger_tasks():
    d = client.get("/api/findings").json()
    assert d["markers"], "FINDINGS.md has (pending: ...) markers"
    for m in d["markers"]:
        assert m["tasks"] and all(t["status"] != "not in ledger" for t in m["task_status"]), m


def test_reads_come_from_git_head_only():
    with pytest.raises(FileNotFoundError):
        C.read_bytes("results/not_committed_anywhere.tsv")
    assert C.read_text("PUBLICATION_ROADMAP.md")


def test_only_committed_figures_and_tables_are_served():
    assert client.get("/api/file/data_root.txt").status_code == 404
    assert client.get("/api/file/results/../data_root.txt").status_code == 404
    assert client.get("/api/table/requirements.txt").status_code == 404
    assert client.get("/api/report/README.md").status_code == 404
    for p in pages.figure_paths():
        r = client.get("/api/file/" + p)
        assert r.status_code == 200 and r.content[:4] == b"\x89PNG"


def test_trees_page_reports_pending_when_none_committed():
    d = client.get("/api/trees").json()
    if not d["trees"]:
        assert any(t["id"] == "S7" for t in d["tasks"])


def test_parsers():
    t = table("a\tb\n1\t2\n3\t4\n", cap=1)
    assert t["columns"] == ["a", "b"] and t["rows"] == [["1", "2"]] and t["n_rows"] == 2 and t["truncated"]
    md = md_tables("## H\n\n| ID | X |\n|---|---|\n| S1 | **y** |\n")
    assert md[0]["heading"] == "H" and md[0]["rows"][0]["X"] == "**y**"
    assert status_kind("completed 2026-08-18") == "done" and status_kind("**closed 2026-08-18 (S1)**") == "done"
    assert status_kind("in_progress") == "active" and status_kind("open (S2)") == "open"
    assert status_kind("pending") == "pending"
    marks = pending_markers("intro *(pending: which task confirms it)*\n## E\nx *(pending: S2, S20)*\n")
    assert [m["tasks"] for m in marks] == [["S2", "S20"]] and marks[0]["entry"] == "E"


def test_static_site_is_small(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    size = sum(f.stat().st_size for f in (tmp_path / "site").rglob("*") if f.is_file())
    assert size < 50e6
    for p in pages.figure_paths():
        assert (tmp_path / "site" / "api" / "file" / p).exists()
