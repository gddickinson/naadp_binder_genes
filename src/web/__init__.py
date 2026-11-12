"""Read-only web dashboard of the committed census outputs (FastAPI + plain ES modules; static export for Pages).

    committed.py  read files from git HEAD, with per-file provenance (commit, date, SHA-256, link)
    parse.py      TSV/CSV tables, roadmap ledger, FINDINGS.md pending markers
    panels.py     stage pages: S0 baseline, literature audit, S1 benchmark
    pages.py      overview tiles, ledger, findings, trees, reports, table browser
    app.py        FastAPI routes, STATIC_ENDPOINTS / STATIC_FILES for scripts/build_static.py
    static/       front end (index.html, core.js, main.js, one module per page)
"""
