# CLAUDE.md — Project-specific instructions

@INTERFACE.md

## ⚠ Publication project — read this first every session

This project is executing a multi-session publication plan. At the start of
EVERY session:

1. Read `PUBLICATION_ROADMAP.md` and follow its **Session protocol**
   exactly: open the dashboard (`python3 scripts/dashboard.py --open` plus a
   background `--watch`), `git pull`, verify the data root
   (`python -m src.utils.data_root --require` — it exits non-zero if the
   external drive is not attached, and **that is a stop, not a warning**),
   pick the single next task from the ledger (first `in_progress`, else
   first unblocked `pending`), announce it, and work only that task to its
   completion criteria.
2. Detailed task instructions live in `docs/session_briefs.md`.
3. At session end, without being asked: update the roadmap ledger +
   Results (+ Emergent tasks for anything new), append to `SESSION_LOG.md`,
   **append a biological-findings entry to `FINDINGS.md`**, refresh
   `README.md`, then `git add -A`, commit (`S<n>: <one-line outcome>`), and
   push if a remote exists.
4. Bulk data goes under `get_data_root()` (`src/utils/data_root.py`) —
   never into the repo.

## Project summary

A GUI app for enumerating every protein isoform / ortholog of a gene across
NCBI, Ensembl, UniProt, AlphaFold DB and (opt-in) Foldseek, plus the
publication pipeline built on top of it. **Subject: the NAADP-binding
proteins, JPT2 (~190 aa) and LSM12 (~195 aa)** — the small accessory
proteins that bind NAADP and confer NAADP sensitivity onto the two-pore
channels (sibling project `../naadpr_genes`).

The biology baseline is `docs/naadp_binder_background.md`; every statement
there is tagged `[db]` / `[lit]` / `[open]` by how far it can be trusted.

## ⚠ The two constraints that make this project different

**1. This is not one family. It is two, and they must never be mixed.**
JPT2 and LSM12 are unrelated proteins that share a ligand and nothing else:
no common domain, no detectable sequence similarity, no common ancestor
within reach of alignment. The app's discovery scorer assumes one family
whose members are mutually comparable, so its distance-based components
(novelty, cluster, breadth) are **meaningless across the JPT/LSM12
boundary** — with both families in one set, every candidate's "nearest known
paralog" is an unrelated protein and lands in the twilight zone by
construction. Run the scorer **once per partition**
(`family.py:FAMILY_PARTITIONS`). Never compute an identity, a tree or a
distance across the boundary. Roadmap Decisions **D14**.

**2. The sharp decoy is inside the family, and no domain separates it.**
JPT1 (HN1) carries PF17054 exactly as JPT2 does, is the same size, and is
not a NAADP binder. The sibling ITPR project's decoys at least differed in
length; here the length band excludes essentially nothing (120–280 aa) and
must not be quoted as evidence. What separates binder from non-binder is
sequence detail and, ultimately, function — so **a domain hit is a family
call, never a function call**, and no task in this repo may write "NAADP
binder" on the strength of a Pfam signature. Roadmap Decisions **D21**.

**A symbol trap, measured at setup.** `gene_exact:HN1L` returns both Q9H910
(190 aa, the real JPT2) and CRAMP1 (Q96RY5, **1,269 aa**), which matches on
a synonym. A longest-first pick selects the wrong protein. See
`family.py:SYMBOL_COLLISIONS`; screen by length and Pfam, never by rank.

**Provenance.** The app, tooling and protocol are ported from
`../ip3r_genes` and, behind it, `../piezo_genes`. Port the method; never
port a result.

## Conventions

- Every `.py` < 500 lines. Read `INTERFACE.md` before opening source files.
- The family is defined in **one** place, `src/utils/family.py` — including
  `FAMILY_PARTITIONS`, which is the partition every analysis must respect.
- Each database client subclasses `src/databases/base.py:DatabaseClient`.
- The GUI never makes network calls on the main thread.
- Analysis scripts live in `scripts/s<n>_*.py` and render their `report.md`
  purely from their committed tables (Decisions D13).

## Running

```
python run.py
python run.py --headless --preset jpt --save-results      # per partition
python run.py --headless --preset lsm12 --save-results    # per partition
python scripts/dashboard.py --open
```
