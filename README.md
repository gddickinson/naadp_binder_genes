# naadp_binder_genes — a publication-grade census of the NAADP-binding proteins

> **Status board and findings are at the bottom.** This README is the
> state-of-the-project summary and is refreshed at the end of every session.

**Status: S-setup complete — the project exists, nothing has been measured.**
The app, the figure style, the dashboard and the manuscript-assembly chain
are ported from the sibling IP3-receptor project; the family definition
(`src/utils/family.py`) was written from scratch and verified live against
UniProt and InterPro on 2026-08-18. The next session runs **S0**.

## What this is

**Subject: JPT2 (~190 aa) and LSM12 (~195 aa)** — the small accessory
proteins that bind NAADP, the most potent Ca²⁺-mobilising second messenger
known, and confer NAADP sensitivity onto the two-pore channels.

For roughly two decades NAADP's receptor was unidentified. Two-pore channels
were proposed and widely accepted, then shown not to bind NAADP directly.
These two proteins are what actually binds it. The channel half of the story
is the sibling project, [`../naadpr_genes`](../naadpr_genes).

## Two things make this project unusual

**1. It is two unrelated families, not one.** JPT2 and LSM12 share a ligand
and nothing else — no common domain, no detectable similarity, no alignable
ancestry. The pipeline assumes one family whose members are mutually
comparable, so every distance, tree and novelty score has to be computed
*within* a partition and never across. Run the `jpt` and `lsm12` presets
separately; a run that mixes them is void until S1 makes it impossible.

**2. The decoy is inside the family, and no domain separates it.**

| | Length | Pfam | Binds NAADP? |
|---|---|---|---|
| **JPT2** (Q9H910) | 190 aa | PF17054 | **yes** |
| **JPT1** (Q9UK76) | 154 aa | **PF17054** | **no** |
| **LSM12** (Q3MHD2) | 195 aa | PF09793, PF21166 | **yes** |

JPT1 carries JPT2's exact signature at nearly its size. Where the sibling
projects could lean on a 2,000 aa separation between a real family member
and its decoy, this one cannot. **A domain hit here is a family call, never
a function call** — nothing in this repo writes "NAADP binder" on the
strength of a Pfam signature.

## Quickstart

```bash
pip install -r requirements.txt          # biopython, requests

python run.py                            # GUI
python run.py --headless --preset jpt --save-results     # one partition
python run.py --headless --preset lsm12 --save-results   # the other

python3 scripts/dashboard.py --open
python -m src.utils.data_root --require  # exit 1 = drive not attached
```

## The science

Verified live 2026-08-18 (UniProt, best entry per gene × species):

| Species | JPT2 | LSM12 | JPT1 (decoy) |
|---|---|---|---|
| human | Q9H910 (190 aa) | Q3MHD2 (195 aa) | Q9UK76 (154 aa) |
| mouse | Q6PGH2 (190 aa) | Q9D0R8 (195 aa) | P97825 (154 aa) |
| chicken | *not found by symbol* | Q5ZML5 (194 aa) | *not found by symbol* |
| *X. tropicalis* | A0A6I8PKV3 (192 aa) | Q6P833 (194 aa) | I7KJP8 (143 aa) |
| zebrafish | F1Q6E4 (218 aa) | Q6PBA2 (196 aa) | *not found by symbol* |
| fly | *not found by symbol* | Q9VYR0 (217 aa) | *not found by symbol* |

Every blank is a **symbol-query result, not a genome fact**. The sibling TPC
project measured exactly this class of error — a fully reviewed plant
two-pore channel invisible to a vertebrate-symbol query. Nothing here counts
as an absence until it has been re-tested by sequence.

**A symbol trap, measured:** `gene_exact:HN1L` returns both Q9H910 (the real
JPT2) and CRAMP1 (Q96RY5, **1,269 aa**), which matches on a synonym alone.
A longest-first pick selects the wrong protein.

### The questions

1. What is each binder's true taxonomic range, once symbol artefacts are removed?
2. **Does binder presence track two-pore-channel presence, lineage by lineage?** This joins against [`../naadpr_genes`](../naadpr_genes) and is the test neither project can run alone.
3. What distinguishes JPT2 from JPT1 at sequence level, and is it constrained? If a conserved JPT2-specific surface exists, that is the project's central positive result.
4. When did the JPT1/JPT2 duplication happen?
5. How much does a two-family subject distort a one-family scorer? (A methods result, measured in S1.)

## Project status board

| Task | Description | Status |
|---|---|---|
| S-setup | Project created, families defined and verified | ✅ completed 2026-08-18 |
| S0 | Literature baseline + scope confirmation | ⏳ pending — **next** |
| S1 | Toolchain + per-partition controls + the distortion measurement | ⏳ pending |
| S2 | Pfam enumeration → census v2 | ⏳ pending |
| S3–S13, S15–S24 | HMM sweep, genome sweep, phylogeny, selection, structures, synthesis | ⏳ pending |
| S14a/b/c | Manuscript, deposit, rewrite | ⏳ pending |

Full ledger and the Decisions log:
[`PUBLICATION_ROADMAP.md`](PUBLICATION_ROADMAP.md).

## Findings so far

Plain-language entries per task: [`FINDINGS.md`](FINDINGS.md). Nothing has
been measured in this repo yet beyond the setup verification above.

## Related projects

| Repo | Family | State |
|---|---|---|
| [`../piezo_genes`](../piezo_genes) | PIEZO1/2/3 mechanosensors | 24 sessions, manuscript assembled |
| [`../ip3r_genes`](../ip3r_genes) | ITPR1/2/3, IP₃ receptors | S0–S1 complete |
| [`../naadpr_genes`](../naadpr_genes) | TPCN1/2/3, two-pore channels | S-setup complete |
| **this repo** | JPT2, LSM12 — the NAADP binders | S-setup complete |

The method is shared; no result is.
