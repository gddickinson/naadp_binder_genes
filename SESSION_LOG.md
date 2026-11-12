# SESSION_LOG.md — running notes per session

One entry per session: what ran, what resulted, what is next. Appended at
session end by the protocol in `PUBLICATION_ROADMAP.md`, never rewritten.

---

## 2026-08-18 — S-setup: project created

**What this is.** A fourth instance of the census-and-discovery pipeline
first built for PIEZO (`../piezo_genes`), then pointed at the IP3 receptors
(`../ip3r_genes`, S0–S1 complete) and the two-pore channels
(`../naadpr_genes`, created the same day). This one is pointed at the two
proteins that actually bind NAADP. The app, figure style, dashboard,
manuscript-assembly tooling and session protocol are ported; no result is.

**What was ported.** `src/` (58 modules) unchanged except
`src/utils/family.py`, rewritten from scratch; `scripts/` limited to the
family-agnostic tooling. The `s0_*`/`s1_*` analysis scripts were
deliberately **not** ported. Three hard-coded ITPR strings were removed on
the way in rather than carried forward — census filenames now derive from
`family.py:FAMILY_NAME`, and the investigation module's next-step prose is
family-appropriate.

**Setup verification (live, 2026-08-18).** Re-derived by S0; nothing here is
quoted from memory.

* **The binders.** JPT2 Q9H910 190 aa (PF17054) and LSM12 Q3MHD2 195 aa
  (PF09793 + PF21166), both reviewed, both resolving across mammals,
  amphibia and fish. LSM12 reaches further by symbol than JPT2 does — it
  resolves in *Drosophila* (Q9VYR0, 217 aa) where JPT2 does not.
* **The decoy.** JPT1 (HN1) Q9UK76, 154 aa, **carries PF17054 — JPT2's exact
  signature** — and is not a NAADP binder. No domain call can separate them,
  and the size band (120–280 aa) contains both. This became Decisions D21
  and D22.
* **A symbol collision.** `gene_exact:HN1L` returns Q9H910 (the real JPT2,
  190 aa) *and* CRAMP1 (Q96RY5, **1,269 aa**), which matches on a synonym
  alone. A longest-first pick selects the wrong protein — the same shape of
  bug the sibling ITPR project hit when a "reviewed" test matched
  "unreviewed". Recorded in `family.py:SYMBOL_COLLISIONS`.

**The structural problem this project is built around.** JPT2 and LSM12 are
**not one family**. They share a ligand and nothing else — no common domain,
no detectable similarity, no alignable ancestry. The ported scorer measures
each candidate's identity to its "nearest known paralog" over whatever is in
the set, so running both families at once makes every candidate an outlier
by construction. `family.py:FAMILY_PARTITIONS` declares the split and
nothing reads it yet; until S1 does, every run must be launched one
partition at a time (the `jpt` and `lsm12` presets). Logged as Decisions D14
and D14a.

**Two smaller things already known to be wrong.** The `size+15` scorer
component will fire on nearly every candidate here, real or not — score
without information (D22, and an Emergent row asking S1 to measure it before
deciding). And the chicken/zebrafish JPT1 and chicken JPT2 blanks are more
likely annotation or naming than absence, given LSM12 resolves in all of
them.

**One dependency crosses repos.** The co-occurrence deliverable (S23 — does
binder presence track channel presence?) joins against `../naadpr_genes`'s
per-genome ledger, which does not exist until that project reaches its own
S5. Tracked as an Emergent row so it does not stall silently.

**Verification.** `python run.py --headless --preset _smoke` returned 29
variants from live UniProt for JPT2 + LSM12 in human, so the ported app runs
end to end in this repo.

**Next session: S0** — audit every `[lit]` claim in
`docs/naadp_binder_background.md`, re-derive every `[db]` number, smoke-test
the app against live NCBI, Ensembl and UniProt. No bulk storage needed.

---

## 2026-08-18 — S0: literature baseline + scope confirmation

**Status: completed.** All four completion criteria met, with the smoke-test
criterion met for two of three sources and the third documented as a live
outage (below).

**Data root.** `python -m src.utils.data_root --require` **exited 1** —
`/Volumes/FANTOM/NAADP_BP_DATA` is not attached. The roadmap ledger scopes
S0–S2 as not needing it, so the session continued; S0 wrote only small
committed artefacts (`results/` grew by 1.6 MB). **The drive must be
attached before S3.**

### What ran

| Script | Output |
|---|---|
| `s0_db_snapshot.py` | 67 live queries → `symbol_table.tsv` (30 cells, both organism fields), `symbol_table_raw.tsv` (50 pre-screen hits), `symbol_collision.tsv`, `pfam_counts.tsv`, `pfam_taxonomy.tsv`, `snapshot_meta.json` |
| `s0_signature_scope.py` | `signature_scope.tsv`, `signature_recall.tsv` |
| `s0_lit_audit.py` | `lit_claims.tsv` (8 claims), `references.tsv` (19 refs) |
| `s0_ensembl_probe.py` | `ensembl_endpoint_probe.tsv` (11 probes, timed) |
| `run.py --headless` ×4 | 4 bundles → `smoke_test.json` |
| `s0_report.py` | `results/s0_baseline/report.md`, `docs/naadp_binder_review_2026.md` |

### What resulted

**The setup snapshot reproduces.** 13 of 30 symbol-table cells resolve to
exactly the accessions and lengths recorded at setup; no setup number was
contradicted. The HN1L collision reproduces exactly (Q96RY5, 1,269 aa, is
still the longest-first pick and still wrong; the Pfam screen separates them
cleanly since CRAMP1 carries PF27753).

**Literature: 8 claims, 19 references, 5 clean.** One **corrected** — the
receptor was unidentified for 26 years (1995→2021), not "roughly two
decades". One **refined** — the ryanodine-receptor arm belongs to JPT2 alone
[PMID:33758062]; LSM12's reported targets are TPC1/2. One **re-tagged** —
"JPT1 is not a NAADP binder" was carried as `[db]`; the signature half is
`[db]`, the non-binder half is `[lit]` and is verified by a direct test
[PMID:37607218]. One **qualified** — "most potent" is a review-level
superlative, hedged in its source; the primary datum is the ~30 nM EC50
[PMID:7836444].

**New for S1: JPT1 and JPT2 are ~40 % identical** [PMID:37607218], with JPT1
showing no measurable NAADP binding against 1.09 nM (JPT2) and 0.703 nM
(LSM12). That 40 % is the gap the S1 sister-margin has to resolve inside.

**D25 — the census denominator was wrong.** PF17054 annotates 1,360 proteins
against 2,944 in IPR033335, the family entry it belongs to (**0.462**), and
misses reviewed mouse JPT2 (Q6PGH2), which carries IPR033335 and no Pfam
cross-reference at all. The LSM12 Pfams are effectively complete for their
own entries (0.998, 1.000), so **the partitions are asymmetric** — not
anticipated by the roadmap. S2 enumerates from IPR033335 / IPR039683.

**D23 — one "absence" was a query field.** `organism_id` matches one
taxonomy node exactly; `taxonomy_id` matches its descendants. Yeast LSM12
(P38828, 187 aa, reviewed, PF09793+PF21166) is filed under the S288c strain
node (559292) while `species.py` carries the species node (4932). Switching
field changes exactly one of thirty cells — and that cell is a reviewed
entry. Both fields are now run and committed so the artefact stays visible.
Separately, the fly JPT2 blank is a naming artefact: Q9I7K0 (JUPIT_DROME,
208 aa, reviewed) carries PF17054, and the Pfam is named after it
[PMID:16518797].

### Two app bugs, both found by the smoke test

**1. Every `Bio.Entrez` call had no timeout.** Biopython passes none to
`urlopen`, so a stalled NCBI read blocks its worker thread forever and the
orchestrator waits on it. The first smoke attempt sat 15 minutes at 0 % CPU;
`sample(1)` showed the worker in `PySSL_select` and the main thread in
`lock_PyThread_acquire_lock`. Fixed in **`src/databases/entrez_util.py`** —
`ensure_socket_timeout()` + `entrez_call()` with retries, raising rather than
returning an empty result that would read as a real absence. All six call
sites (`ncbi.py` ×3, `blast.py`, `literature.py` ×3) now route through it.

**2. A source that never returned was silently dropped (D24).** The headless
driver waits on a deadline then proceeds with whatever arrived; unreturned
sources were simply absent from the bundle's `per_source`. The first
full-panel run produced "642 variants across 2 source(s)" with **no record
anywhere that Ensembl had been asked and had failed** — a partial harvest
indistinguishable from a complete one, which for a project whose deliverable
is an absence claim is the worst available failure mode. `SearchOrchestrator`
now records `started_sources` and `cli.py` synthesises an explicit `ERROR`
result for each dispatched source that did not return.

### Ensembl was down, and that is a finding for S1

`/info/ping` answered in 0.61 s, but `lookup/symbol` averaged **19.8 s** over
five calls (27.6 s for human JPT2) and `xrefs/symbol` gave two 30 s timeouts
and one HTTP 503; zebrafish `lookup/symbol` returned HTTP 400. In the smoke
runs Ensembl returned HTTP 500 for the JPT symbols and empty for LSM12, and
the full-panel runs lost it to the 900 s deadline. NCBI and UniProt returned
on every run (JPT full panel 642 variants; LSM12 full panel 242). This
sharpens the `INTERFACE.md` note, which said `xrefs` stalls while
`lookup/symbol` works — on this evidence the whole service was degraded.
**Re-probe at the start of S1** (`scripts/s0_ensembl_probe.py`).

### Scope, confirmed with the user (D26)

Vertebrate genome scope for S4 = **best reference assembly per vertebrate
order** (the PIEZO rule). The non-vertebrate range question (S20) is **in
scope as a headline result**, not supplementary.

### Next session: S1

Toolchain install + control benchmark per partition. Read
`results/s0_baseline/report.md` first — it carries the ~40 % identity, the
D25 denominator change and the Ensembl outage. Note the four open Emergent
rows S0 added. The external drive is still not required for S1.

---

## S1 — 2026-08-18 · Toolchain + control benchmark (per partition)

**Status: completed.** Data root unavailable (`/Volumes/FANTOM/NAADP_BP_DATA`
not attached, exit 1) — the roadmap declares the drive unnecessary for S0–S2,
so the session proceeded. **It is required from S3 on.**

### What ran

| Step | Script | Output |
|---|---|---|
| Ensembl re-probe (S0 emergent) | `scripts/s0_ensembl_probe.py` | `results/benchmark_controls/ensembl_reprobe.tsv` |
| Toolchain probe | `scripts/s1_toolchain.py` | `results/toolchain_manifest.txt`, `benchmark_controls/toolchain.tsv` |
| Control panels (live UniProt) | `scripts/s1_panels.py` | `panel_{positives,decoys,giants}.{json,fasta}`, `*_missing.tsv`, `symbol_collisions.tsv` |
| Six benchmark experiments | `scripts/s1_benchmark.py` + `s1_runs.py` + `s1_lib.py` | `scores.tsv`, `bait_margin.tsv`, `size_component.tsv`, `crossfamily_identity.tsv`, `alignment_width_effect.tsv`, `partition_assignment.tsv`, `domain_hits.tsv`, `mafft_trace.json`, `summary.json` |
| Figure | `scripts/s1_figures.py` | `figures/s1_scorer_validation.{png,pdf}` |
| Report (D13) | `scripts/s1_report.py` + `s1_report_sections.py` | `results/benchmark_controls/report.md` |

Benchmark wall-clock 99.5 s; 17 positive + 58 decoy panel records over 57
unique accessions. MAFFT verified by return code (`mafft --auto --quiet`,
rc=0), not by the fact a call happened.

### Code changed

* **`src/utils/partitions.py` (new)** — partition assignment (provenance →
  family Pfam → symbol) + `CrossPartitionError` + `assert_single_partition`.
* **`src/discovery/partition.py` (new)** — `run_partitioned_discovery`
  splits **before the alignment**, so each family gets its own MSA,
  identity matrix and tree and a cross-family cell has nowhere to exist;
  `merge_reports`, `partition_table`, `known_for_partition`. Accepts
  `signature_sets=` so a signature built from named members can be applied
  to unnamed candidates.
* **`src/discovery/candidates.py`** — calls the guard on every run
  (`allow_cross_partition=True` is the explicit opt-out the benchmark used);
  `partition` and `size_component_points` config fields; **bug fix**:
  `restrict=known_labels or None` turned an *empty* known set into "no
  restriction", so outlier/cluster/sister scored candidates against their
  nearest neighbour of any kind (D24 failure class).
* **`src/discovery/writer.py` (new)** — `write_discovery` moved out to keep
  `candidates.py` under the 500-line rule; imports updated in `cli.py`,
  `domain_scan.py`, `exhaustive.py`, `__init__.py`.
* **`src/cli.py`** — a preset spanning both families now routes through
  `run_partitioned_discovery` instead of being scored in one set.

### Results (headline)

* All 12 binaries resolve. MAFFT v7.526, HMMER 3.4, BLAST+ 2.16.0+,
  miniprot 0.18-r281, trimAl v1.5.rev1, IQ-TREE 2.3.6, datasets 18.35.0,
  foldseek 10.941cd33.
* **Specificity 58/58; JPT1 5/5 — but only because of the sister test.**
  Disabled: 5/5 JPT1 decoys promote (80 for the three carrying PF17054,
  60 for the two that do not) and specificity falls to 53/58.
* **Recall 12/15** for unnamed true members, **15/15** with the
  MSA-signature fallback. All three misses are JPT2 orthologs carrying no
  Pfam cross-reference (D25 reaching the scorer).
* **Distortion is conditional (D27):** 1/57 scores differ joint-vs-partitioned
  with both families named; **44/57 with 2 call flips** when one family has
  no named member.
* **Cross-family identity (D28):** max 0.108 full-alignment (0 % in the
  twilight zone) vs 0.391 covered-only (13.1 %).
* **Size component (D29):** retained at +15; band holds 17/17 members and
  40/58 decoys; zeroing it loses 7 true positives and gains no specificity.
* `gene_exact:ALB` returns FBF1 (1,133 aa) on a synonym — the HN1L trap is
  not a one-off. Panel builder now prefers primary symbols.

### Next session: S2

Uncapped enumeration from **IPR033335** (JPT) and **IPR039683** (LSM12) →
census v2. Read `results/benchmark_controls/report.md` first. Four things
S2 must carry: the signature fallback (built from the named panel, applied
to candidates), `family.py:SISTER_PANEL` in every JPT search, the
primary-symbol rule for `pick_best`, and the fact that Ensembl is still not
dependable. The external drive is not required for S2.

---

## 2026-11-12 — Web results dashboard (not a ledger task)

Added a read-only web dashboard of the committed outputs (`src/web/`, `run_web.py` on port 8175) and a static GitHub
Pages export (`scripts/build_static.py`, `.github/workflows/pages.yml`). Pages: overview (headline tiles), ledger, S0
database baseline, S0 literature audit, S1 scorer benchmark (run metrics, per-record scores per run, bait margins,
distortion, identity, every S1 table, Figure S1), findings with a `(pending: task)` tracker, trees (none committed:
shows S6/S7/S13/S16 as pending), rendered reports, and a browser for all 26 committed tables under `results/`.

- Every value is read via `git show HEAD:<path>`, so uncommitted working-tree edits cannot reach the site; each panel
  carries its file, last commit, SHA-256 prefix and GitHub link. Headline counts print the row filter used.
- Cross-check test: the JPT1 sister-test headline counted from `scores.tsv` matches `summary.json`'s independent
  `part_*_jpt1_*` keys (5/5 promoted with the test off, 0/5 with it on).
- Static site 1.2 MB. `pytest tests/test_web.py`: all pass; screenshots.py `--static` and `--base`: all routes ok, no
  phone-width overflow.
- Noted, not changed: the ledger's S0 headline says "5 verified" literature claims; `lit_audit_meta.json` records
  4 verified + 1 qualified (+1 corrected, 1 refined, 1 re-tagged = 8). The dashboard shows the table's verdicts.
- FINDINGS.md line 25 marker `(pending: S1, S6, S7)`: S1 is now completed; S6/S7 still pending, so the marker stands.
