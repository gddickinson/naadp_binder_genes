# PUBLICATION_ROADMAP.md — publication-grade NAADP-binder census

**Goal.** Enumerate and validate every JPT-family and LSM12-family gene
across a declared genome scope, and answer what the records cannot currently
answer: each binder's true taxonomic range, **whether binder presence tracks
two-pore-channel presence lineage by lineage**, what distinguishes JPT2 from
its non-binding paralog JPT1 at sequence level, when that duplication
happened, and how badly a two-family subject distorts a one-family pipeline.

**How the claim is scoped.** "A systematic census across N vertebrate
genomes and M eukaryotic reference proteomes" (N fixed in S4, M in S3/S20),
never an unbounded "all NAADP binders". Every absence claim is a claim about
a *declared* search space — and, here, about a declared symbol set.

**The biology this rests on** is `docs/naadp_binder_background.md`.

**The two things that will bite you.**

1. **This is two unrelated families in one repo.** JPT2 and LSM12 share a
   ligand and nothing else. Every distance, tree and novelty score must be
   computed within a partition (`family.py:FAMILY_PARTITIONS`) and never
   across. See Decisions **D14**.
2. **The decoy is inside the family and no domain separates it.** JPT1
   carries JPT2's Pfam, is the same size, and does not bind NAADP. A domain
   hit is a family call, never a function call, and the size band
   (120–280 aa) excludes almost nothing. See Decisions **D21**.

**The sibling project is half the experiment.** `../naadpr_genes` censuses
the two-pore channels. The co-occurrence question — does the machinery to
sense NAADP travel with the channel it gates — needs both, and S20/S23 here
are written to join against that project's ledger rather than duplicate it.

---

## Session protocol

Claude: follow this protocol in every session that touches this project.

### Start of session
0. Open the project dashboard: `python3 scripts/dashboard.py --open` and
   start its watcher in the background (`python3 scripts/dashboard.py
   --watch` as a background task) so the page stays live through the
   session. Stdlib-only — no conda env needed.
1. Read this file top to bottom. Read `docs/session_briefs.md` for the brief
   of the task you are about to work.
2. `git pull`.
3. Run `python -m src.utils.data_root --require`. It exits non-zero if the
   bulk-storage drive is not attached. **If it fails, stop and tell the
   user** — do not download anything, and do not "temporarily" use the
   internal disk. Note free space (`df -h`) before any bulk task.
4. Pick the task: the single ledger row whose Status is `in_progress`, else
   the topmost `pending` row whose dependencies are all `completed`.
   Announce it to the user. Set its Status to `in_progress` (commit at
   session end).
5. Work **only that task** until its completion criteria pass. Do not start
   the next task even if time remains — spend surplus on tests, docs, or
   hardening of the current task.

### During the session
- Big/raw files → `get_data_root()` subdirs, never the repo. Committed
  artefacts: summaries, TSV/CSV ≤ ~20 MB, figures, manifests, code.
- Record every load-bearing number and file path in the task's Results
  column (link out to a file under `results/` if long).
- Write `results/session_live.json` from any long-running driver
  (`{"task": "S5", "workers": 2, "steps": [{"label": ..., "done": ...}]}`)
  so the dashboard shows real progress.
- New leads, surprises, or scope changes → add a row to **Emergent tasks**.
  Never silently expand the current task.
- A task that proves too large for one session: split it in the ledger
  (S5 → S5a/S5b), complete the first part properly, leave the rest `pending`
  with a note. Splitting is normal; half-done is not.
- Anything needing an interactive login or sudo: ask the user to run it via
  the `!` prefix.

### End of session (checklist — do all of it)
1. Completion criteria all pass → Status `completed` + date. Not all passing
   → stays `in_progress` with a NEXT note giving the exact resume point.
2. Update this file (ledger, Results, Emergent, Decisions).
3. Append a dated entry to `SESSION_LOG.md` (what ran, what resulted, what's
   next).
3a. **Append a biological-findings entry to `FINDINGS.md`** — what the task
   changed in the biological story, in plain language, findings before
   methods, unconfirmed claims marked *(pending: which task confirms it)*.
   Keep methods and paths out of it.
3b. **Refresh `README.md`** — it is the state-of-the-project summary for
   anyone arriving cold. Update the status board row, and if the session
   produced a result worth showing, add it to **Findings so far** with a link
   and an embedded figure. Delete what the session made obsolete.
4. `git add -A && git commit` (message: `S<n>: <one-line outcome>`) and
   `git push` if a remote is configured.
5. Tell the user: task status, headline results, what the next session does.

---

## Storage

- Active bulk-data root: see `data_root.txt`, read via
  `src/utils/data_root.py:get_data_root()`. Currently
  `/Volumes/FANTOM/NAADP_BP_DATA` — **an external drive that must be attached
  before any bulk session**. Moving it later is a one-line edit; the
  directory layout recreates itself.
- `require_data_root()` raises rather than falling back. Anything that
  downloads or sweeps must call it, so an unplugged drive stops the session
  at the top instead of after 200 GB has landed on the laptop.
- Expected bulk footprint, from the PIEZO project's measured equivalents:
  vertebrate assemblies ~400 GB (fetch → search → delete keeps the live
  footprint near 20 GB), reference proteomes ~10 GB, per-genome sweep
  evidence ~30 GB, HMMER raw output ~12 GB, structures ~2 GB.
- Budget rule: any single download > 20 GB needs a note in Decisions with
  the running disk total.

---

## Task ledger

Statuses: `pending` / `in_progress` / `completed YYYY-MM-DD`.
Full step-by-step briefs: `docs/session_briefs.md`.

> **Next session: S1.** S0 is complete: the literature baseline is verified
> (`docs/naadp_binder_review_2026.md`), every `[db]` number re-derived, and
> two blocking app bugs fixed. **Read `results/s0_baseline/report.md`
> before S1** — it carries three things S1 needs: the measured ~40 %
> JPT1/JPT2 identity (the difficulty the sister-margin has to beat), the
> census-denominator change (**D25**), and the fact that Ensembl REST was
> degraded on 2026-08-18, so S1 should not depend on it.
>
> **Read the sibling ITPR project's `results/benchmark_controls/report.md`
> before S1.** It measured what happens when a scorer's domain component
> fires on a signature the decoys also carry: 6/6 decoys promoted. Here the
> decoy carries the *identical* signature and is nearly the same length, so
> the same failure is expected in a sharper form and the fix cannot be a
> length filter.
>
> **The external drive** (`data_root.txt` → `/Volumes/FANTOM/NAADP_BP_DATA`)
> is not needed for S0–S2 and is required from S3 on. These proteins are
> ~190 aa, so this project's bulk footprint is a small fraction of the
> sibling projects'.

| ID | Task (one session each) | Depends | Status | Results (headline) |
|----|-------------------------|---------|--------|--------------------|
| S0 | Literature baseline + scope confirmation: verify every `[lit]` claim, build `docs/naadp_binder_review_2026.md`, smoke-test the app | — | completed 2026-08-18 | **8 lit claims audited / 19 refs** (1 corrected, 1 refined, 1 re-tagged, 5 verified) → `docs/naadp_binder_review_2026.md`. **PF17054 covers only 46.2 % of IPR033335** and misses reviewed mouse JPT2 (Q6PGH2) → census denominator changed (**D25**). **Yeast LSM12 P38828 recovered** — `organism_id` vs `taxonomy_id` false absence (**D23**). **JPT1 vs JPT2 ≈ 40 % identity** [PMID:37607218] — calibrates S1. Two app bugs fixed: Entrez calls had **no timeout** (hung the pipeline), and an unreturned source was **silently dropped** (**D24**). All tables + `report.md` in `results/s0_baseline/`. |
| S1 | Toolchain install + control benchmark **per partition**, with JPT1 as the sharp decoy, and a measurement of the cross-family distortion | S0 | pending | |
| S2 | Uncapped Pfam enumeration (PF17054; PF09793/PF21166) → census v2, with a partition call and a binder-vs-paralog call on every record | S1 | pending | |
| S3 | Profile-HMM sweep (jpt.hmm, jpt1-decoy profile, lsm12.hmm) over reference proteomes + jackhmmer-to-convergence → census v3 | S1, S2 | pending | |
| S4 | Genome scope: declared assembly manifest + download tooling | S1 | pending | |
| S5 | Genomic tblastn + miniprot sweep → per-genome ledger + novel gene models → census v4. **Small genes hide in short exons — expect a worse annotation rate than the sibling projects** | S4 | pending | |
| S20 | **Non-vertebrate sweep** — each binder's true range, symbol artefacts removed | S3 | pending | |
| S23 | **Co-occurrence with the channel** — join this census against `../naadpr_genes`'s per-genome TPC ledger: which lineages have binder + channel, binder only, channel only, neither | S20 | pending | |
| S6 | Alignment upgrade: MAFFT L-INS-i + trimAl, **one alignment per partition, never a joint one** | S2, S3, S5, S20 | pending | |
| S7 | ML phylogeny: IQ-TREE 2 + ModelFinder + 1000 UFBoot — **two trees, JPT rooted on the wider Jupiter family, LSM12 on the Lsm fold set** | S6, S23 | pending | |
| S8 | Synteny across the JPT1/JPT2 and LSM12 loci | S2, S5 | pending | |
| S9 | ML selection: PAL2NAL + codeml, HyPhy RELAX — **is JPT2 under different constraint from JPT1** | S6 | pending | |
| S10 | Annotation-bug molecular validation for the two worst cases S5/S18 surface | S5 | pending | |
| S11 | Structures: AFDB coverage (should be near-total at ~190 aa), the NAADP-binding surface, Foldseek sweep | S2, S6 | pending | |
| S12 | Expression evidence for whichever binder or lineage the census leaves in doubt | S5 | pending | |
| S13 | Gene-tree/species-tree reconciliation — date the JPT1/JPT2 duplication | S7 | pending | |
| S14a | **Manuscript assembly** | S3, S5, S7, S8, S9, S10, S11, S20, S23, S15–S19 | pending | |
| S24 | Supplementary figures + figure-by-figure audit | S14a | pending | |
| S14b | **Deposit + release** | S14a | pending | **Human-gated.** |

### Analysis & synthesis block (S15–S22)

| ID | Task | Depends | Priority | Status | Results |
|----|------|---------|----------|--------|---------|
| S15 | **Loss dynamics** — ancestral-state reconstruction per binder, ORF-integrity screen | S5, S13 | high | pending | |
| S16 | **Duplication history** — when JPT2 separated from JPT1, and whether LSM12 has an equivalent paralog | S7, S8, S13 | high | pending | |
| S17 | **The binder-vs-paralog signature** — the residues that distinguish JPT2 from JPT1 across the vertebrates, mapped onto the predicted structure. **The project's central positive result if it exists** | S6, S9, S11 | high | pending | |
| S18 | **Annotation-quality audit** — how often a real binder locus is missing, fragmentary or filed under the wrong paralog. Small single-exon-ish genes are badly served by gene finders; quantify it | S5, S15 | high | pending | |
| S19 | **Methods results** — per-method contribution, and **how much a one-family scorer distorts a two-family subject** (the S1 measurement, at census scale) | S5, S15, S18 | medium | pending | |
| S21 | **Gene architecture** across the genome scope | S5, S18 | medium | pending | |
| S22 | **Ligand-site evolution** — is the NAADP-binding surface more constrained than the rest of the protein, and does it differ between JPT2 and LSM12 despite the shared ligand | S9, S17 | medium | pending | |
| S14c | **Manuscript rewrite pass** | S14a, S24 | medium | pending | |

---

## Emergent tasks & new aims

| Added | From | Task | Status |
|-------|------|------|--------|
| 2026-08-18 | setup | **The ported scorer has no notion of partitions.** `discover_novel_paralogs` computes "identity to nearest known paralog" over whatever is in the set, so running both families at once makes every candidate an outlier by construction. `family.py:FAMILY_PARTITIONS` is declared and nothing reads it | open (S1) |
| 2026-08-18 | setup | **The size band is declared but nearly useless** (120–280 aa, with JPT1 at 154 and JPT2 at 190 inside it). The `size+15` scorer component will fire on almost every candidate, real or not — a component contributing no information but plenty of score. Decide in S1 whether to zero it for this family and record the decision | open (S1) |
| 2026-08-18 | setup | Chicken and zebrafish JPT1, and chicken JPT2, did not resolve by symbol. Given LSM12 resolves in all of them, this is more likely annotation or naming than absence — resolve by sequence | open (S2) |
| 2026-08-18 | setup | **The co-occurrence deliverable depends on a sibling repo.** S23 joins against `../naadpr_genes`'s per-genome ledger, which does not exist until that project reaches its own S5. Track the dependency across repos or S23 will stall | open (S23) |
| 2026-08-18 | S0 | **The JPT census denominator is wrong.** PF17054 covers 1,360 proteins against 2,944 in its own InterPro family entry IPR033335 (0.462), and misses reviewed mouse JPT2 (Q6PGH2), which carries IPR033335 and no Pfam cross-reference. LSM12's signatures are effectively complete for their entries, so **the two partitions need different denominators**. Settled as **D25**; S2 implements it | open (S2) |
| 2026-08-18 | S0 | **Ensembl REST was degraded on 2026-08-18** and the app cannot currently rely on it: `/info/ping` 0.61 s, but `lookup/symbol` averaged 19.8 s over five calls and `xrefs/symbol` gave 2 timeouts + 1 HTTP 503; the full-panel smoke run lost Ensembl to the 900 s deadline. Evidence `results/s0_baseline/ensembl_endpoint_probe.tsv`. Re-probe at the start of S1; if still degraded, S2/S3 must not take Ensembl as a required source | open (S1) |
| 2026-08-18 | S0 | **UniProt Pfam cross-references are incomplete on true family members.** Mouse JPT2 (Q6PGH2, reviewed) and *X. tropicalis* JPT1 (I7KJP8) carry IPR033335 but no Pfam xref at all. Any fetch that screens candidates by Pfam presence will drop them; `pick_best()` already falls back to the length band and records it, but S2's binder call must not treat "no Pfam" as "not in the family" | open (S2) |
| 2026-08-18 | S0 | **The zebrafish Ensembl symbol lookup returns HTTP 400** (`/lookup/symbol/danio_rerio/lsm12`), unlike human and mouse. Probably a symbol-case or ID-type issue rather than an outage, since it did not time out. Resolve when Ensembl is healthy again | open (S2) |
| 2026-08-18 | setup | **`src/gui/tools.py` is 549 lines — over the project's 500-line rule**, inherited from the sibling projects rather than introduced here (it is 549 there too). The natural seam is the Analysis-menu handlers vs `augment_bundle()`. Split it before adding any menu action | open |

---

## Decisions log

**D0 — This project inherits the PIEZO project's methodological decisions.**
They were paid for over 24 sessions and are not to be re-derived. D3–D17
below are those rules, restated for this family. A session may overturn one,
but must say so explicitly here with its reason.

**D1 — Bulk storage lives on the external drive**, `data_root.txt`
(`/Volumes/FANTOM/NAADP_BP_DATA`). Sessions call `require_data_root()`; an
unplugged drive stops the session rather than filling the internal disk.

**D2 — The repository stays private until S14b**, which flips it public
alongside the Zenodo DOI. Nothing in the repo may assume a public URL before
then.

**D3 — The discovery scorer needs an evidence gate.** A score of ≥ 40 needs
at least one family-specific component (domain / outlier / fold / split
annotation); size and novelty alone cap at 39. Implemented in
`src/discovery/candidates.py`.

**D4 — An absence claim must pass two bars, not one.** A genome-wide
contiguity floor (calibrated in S19, ~50 kb contig N50 in the PIEZO project)
*and* a local check that the paralog's own genomic neighbourhood is present.
Residual false negatives are regional, not random: a genome missing a whole
syntenic block is not evidence of gene loss.

**D5 — Bait panels are screened by label, not padded for breadth.** One
correctly labelled bait per paralog above ~40 % identity recovers nearly
everything; a bait wearing the wrong clade name does real damage. Screen
every bait for chimeras (a domain-envelope check against the profile) before
it enters a panel.

**D6 — Never issue a database correction without the integrity veto.** If
the ORF-integrity screen (S15) says a locus is genuinely dead, the audit
does not tell RefSeq to resurrect it.

**D7 — Best-hit paralog assignment needs a margin.** Two baits scoring
within ~10 % of each other is not a call. This applies with extra force
here, where the binder and its non-binding paralog share a Pfam signature
and a size class.

**D8 — Representatives are chosen per clade × per kingdom**, with explicit
selection rules in a script, not "the longest sequence per species". A
longest-first pick reliably selects chimeric gene models.

**D9 — Quote an annotation claim with its annotation source.** RefSeq
(`GCF_`) gene sets and submitter-deposited GenBank (`GCA_`) gene sets are
not comparable evidence; some assemblies ship no gene set at all.

**D10 — Iterative searches need a coded kill criterion.** jackhmmer runs
that diverge must be killed by a rule recorded in code and reported, not by
eye.

**D11 — Look at the figure.** Any session that changes a figure looks at it;
any session that writes a legend looks at the figure it describes. Four
errors in the PIEZO manuscript were of a kind no table check could catch.

**D12 — Every load-bearing number in the manuscript needs a claim row** in
`scripts/s14_claims.py`, naming its source table and the operation that
recovers it. A re-run that changes a table then fails loudly.

**D13 — Reports are rendered from the committed tables**, never written by
hand alongside them, so a report and its data cannot drift.

**D14 — The two families are never mixed** (family-specific). JPT2 and
LSM12 share a ligand and nothing else: no common domain, no detectable
similarity, no alignable ancestry. Every identity, distance, tree, MSA and
novelty score is computed **within** a partition
(`family.py:FAMILY_PARTITIONS`) and never across. A number computed across
the boundary is noise wearing a decimal point, and the scorer produces one
silently — with both families in a set, each candidate's "nearest known
paralog" is an unrelated protein, so every candidate lands in the twilight
zone and scores as novel. Run once per partition; say in every report which
partition a number came from.

**D21 — A domain hit is a family call, never a function call**
(family-specific). JPT1 carries PF17054 exactly as JPT2 does, at 154 aa
against 190 aa, and does not bind NAADP. Nothing in this repo may write
"NAADP binder" on the strength of a Pfam signature, a size band or a
BLAST hit. The binder claim requires either an experimental citation or an
explicitly-labelled inference, and the tables carry the distinction in a
column rather than in prose.

**D22 — The size band is declared for machinery, not quoted as evidence.**
120–280 aa spans the binders and their decoys alike. Where the sibling
projects could lean on a 2,000 aa separation, this one cannot, so no report
here cites length as support for a family call. If the scorer's size
component is retained, S1 records why.

**D14a — D14 is not implemented, and S1 implements it.** The ported scorer
has no notion of partitions: `discover_novel_paralogs` measures each
candidate against whatever known members are in the set.
`family.py:FAMILY_PARTITIONS` is declared and nothing reads it. Until S1,
every discovery run in this repo must be launched one partition at a time
(the `jpt` and `lsm12` presets), and any run that mixes them is void.

**D18 — The project runs in the reused `piezo1` conda env**
(`/opt/anaconda3/envs/piezo1`, python 3.11.15), not a cloned `ip3r` env.
BLAST+ 2.16.0+, the NCBI `datasets` CLI and Foldseek live there rather than
on the bare PATH; MAFFT, HMMER, miniprot, trimAl and IQ-TREE 2 come from
Homebrew and work in any shell. Reused rather than cloned to avoid
duplicating several GB of an identical toolchain — the env holds tools, not
project data, so nothing about a result depends on its name. Exact versions:
`results/toolchain_manifest.txt`, regenerated by `scripts/s1_toolchain.py`.

**D15 — The species tree is an input, not a result.** Reconciliation uses a
hand-curated, literature-calibrated topology with a source on every
calibrated node, validated by a `--check` mode before use.

**D16 — Cross-paralog comparisons are paired within genome.** Intron size,
assembly quality and annotation completeness all scale with the assembly, so
an unpaired comparison measures the assemblies.

**D17 — Permutation nulls are drawn from real genomic windows**, not from a
uniform shuffle, and the genes under test are removed from their own windows
or the test is circular.

**D23 — Symbol x organism queries use `taxonomy_id`, not `organism_id`**
(measured in S0). UniProt's `organism_id` matches **one taxonomy node
exactly**; `taxonomy_id` matches the node **and its descendants**. The setup
snapshot used the first and recorded *S. cerevisiae* LSM12 as absent. It is
not absent: P38828 (LSM12_YEAST, 187 aa, reviewed, PF09793+PF21166) sits
under the S288c strain node (559292) while `species.py` carries the species
node (4932). Switching field changes exactly one of thirty cells — but that
cell is a reviewed entry, and the project's headline deliverable is an
absence claim. Every symbol x organism query in this repo uses the subtree
field, and `s0_db_snapshot.py` runs **both** and commits the difference so
the artefact stays visible rather than being quietly fixed.

**D24 — A source that does not return is recorded as a failure, never
omitted** (measured in S0). The headless driver waits on a deadline and then
proceeds with whatever arrived; the sources that never came back were simply
absent from the bundle's `per_source` list. The first full-panel smoke run
therefore produced a bundle reading "642 variants across 2 source(s)" with
**no record anywhere that Ensembl had been asked and had failed** — a
partial harvest indistinguishable from a complete one. For a project whose
deliverable is an absence claim this is the most dangerous class of bug
available, worse than a crash. `SearchOrchestrator` now records
`started_sources`, and `cli.py` synthesises an explicit `ERROR` result for
every dispatched source that did not return.

**D25 — The census denominator is the InterPro *family* entry, not the
Pfam** (measured in S0; scope confirmed with the user). PF17054 annotates
1,360 UniProt proteins against 2,944 in IPR033335, the family entry it
belongs to — **46.2 %** — because the PANTHER member (PTHR34930) covers the
rest. It also misses a known true positive: reviewed mouse JPT2 (Q6PGH2)
carries IPR033335 and **no Pfam cross-reference at all**. So S2 enumerates
the JPT partition from **IPR033335** and the LSM12 partition from
**IPR039683**, recording the Pfam-only list as a subset so the difference
between the two denominators is itself a reported number. The partitions are
asymmetric here — the LSM12 Pfams are effectively complete for their own
entries (0.998, 1.000) — and the roadmap did not anticipate that.

**D26 — Scope, confirmed with the user in S0.** The vertebrate genome scope
(S4) is **the best reference assembly per vertebrate order**, inherited from
the PIEZO project; absence claims are scoped to that declaration. The
non-vertebrate range question (S20) is **in scope as a headline result**,
not supplementary — LSM12 already resolves in fly and yeast by symbol alone,
and PF09793 sits in an ancient fold set, so the range question is where the
novel biology most likely is, and it feeds S23.

**D0b — This project also inherits the ITPR project's measured lessons.**
Two carry directly: (1) a scorer whose domain component fires on a signature
the decoys also carry will promote the decoys — measured there as 6/6
ryanodine receptors promoted at 45, fixed by a *positional* test that never
consults a gene symbol. Here the decoy carries the identical signature at
nearly the same length, so the same failure is expected in sharper form and
the fix cannot be a length filter. (2) A "reviewed" test written as
`"reviewed" in entryType` matches `"UniProtKB unreviewed (TrEMBL)"` and
silently selects the wrong entry — test for `"unreviewed"` first. That bug
is doubly dangerous here, where `gene_exact:HN1L` also returns a 1,269 aa
protein on a synonym.
