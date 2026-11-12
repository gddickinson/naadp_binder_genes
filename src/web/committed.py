"""Read the repo's *committed* outputs, with provenance for every file.

Everything the web dashboard shows comes through here. Files are read from the git HEAD commit (`git show HEAD:<path>`),
never from the working tree, so an uncommitted edit to a results table cannot leak onto the public site. Each read
records the path, the last commit that touched it, its date and a SHA-256 of the bytes served, which every panel
returns as `provenance`.

If git is not available (e.g. an exported tarball), files are read from disk and the provenance says so.
"""
from __future__ import annotations

import hashlib
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_URL = "https://github.com/gddickinson/naadp_binder_genes"


def _git(*args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


@lru_cache(maxsize=1)
def head() -> dict:
    """The commit everything is read from."""
    out = _git("log", "-1", "--format=%H%x09%cs%x09%s", "HEAD")
    if not out:
        return {"commit": None, "short": "working tree", "date": None, "subject": "git unavailable"}
    full, date, subject = out.strip().split("\t", 2)
    return {"commit": full, "short": full[:7], "date": date, "subject": subject}


@lru_cache(maxsize=None)
def tracked(prefix: str = "") -> tuple[str, ...]:
    """Every path committed at HEAD under `prefix` (a directory such as 'results/')."""
    out = _git("ls-tree", "-r", "--name-only", "HEAD", "--", prefix) if head()["commit"] else None
    if out is None:
        base = ROOT / prefix
        files = [p for p in base.rglob("*") if p.is_file()] if base.is_dir() else ([base] if base.is_file() else [])
        return tuple(sorted(str(p.relative_to(ROOT)) for p in files))
    return tuple(sorted(line for line in out.splitlines() if line))


@lru_cache(maxsize=None)
def read_bytes(path: str) -> bytes:
    """Bytes of `path` as committed at HEAD. Raises FileNotFoundError if it is not committed."""
    if head()["commit"]:
        if path not in tracked(path):
            raise FileNotFoundError(f"{path} is not committed at HEAD")
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{path}"], capture_output=True, timeout=30)
        if r.returncode != 0:
            raise FileNotFoundError(path)
        return r.stdout
    return (ROOT / path).read_bytes()


def read_text(path: str) -> str:
    return read_bytes(path).decode("utf-8")


def exists(path: str) -> bool:
    return path in tracked(path)


@lru_cache(maxsize=None)
def provenance(path: str) -> dict:
    """Where a shown value came from: file, last commit touching it, date, SHA-256, and a link to that version."""
    data = read_bytes(path)
    info = {"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()[:16]}
    out = _git("log", "-1", "--format=%H%x09%cs", "HEAD", "--", path) if head()["commit"] else None
    if out and out.strip():
        full, date = out.strip().split("\t")
        info.update(commit=full[:7], date=date, url=f"{REPO_URL}/blob/{full}/{path}")
    else:
        info.update(commit=head()["short"], date=head()["date"], url=None)
    return info


def prov(*paths: str) -> list[dict]:
    return [provenance(p) for p in paths]
