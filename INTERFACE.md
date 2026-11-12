# INTERFACE.md — Module Navigation Map

> Read this **before** opening any source files. Each `.py` is < 500 lines
> and has one focused responsibility.

## Top-level

| File | Purpose |
|------|---------|
| `run.py` | CLI/GUI entry — `python run.py [--email you@example.com] [--headless --preset naadp_bp]`. |
| `PUBLICATION_ROADMAP.md` | **The multi-session publication plan**: session protocol, task ledger (S0–S24), emergent tasks, and the Decisions log — including the methodological rules inherited from the PIEZO project. Read at the start of every session. |
| `docs/session_briefs.md` | Detailed per-task instructions for every ledger row: goal, steps, completion criteria, outputs. |
| `docs/naadp_bp_background.md` | **The biology baseline.** Every statement tagged `[db]` (verified against a live database, with the query), `[lit]` (literature, verified in S0) or `[open]` (a question this project answers). Includes the binder/JPT1 hazard and the database-scale snapshot. |
| `docs/analysis_catalogue.md` | **What the harvested data can answer** — the analysis menu behind ledger rows S15–S22, each with its inputs, method, deliverable and invalidating caveat, plus the report skeleton mapping analyses to manuscript sections. |
| `CLAUDE.md` | Session-start instructions, conventions, the family definition rule. |
| `INTERFACE.md` | (this file) navigation map. |
| `README.md` | User-facing docs + the project status board. |
| `SESSION_LOG.md` | Running notes per session: what ran, what resulted, what's next. |
| `FINDINGS.md` | **The biological story, task by task** — a dated plain-language entry appended after every completed task; unconfirmed claims marked *(pending: which task confirms it)*. |
| `roadmap.md` | Feature-development history of the app itself (inherited v1.0–v1.7 plus this project's changes). |
| `data_root.txt` | Path to the bulk-data root, read by `src/utils/data_root.py`. Edit one line to move storage. |
| `requirements.txt` | Third-party deps (`biopython`, `requests`). |
| `presets/` | Bundled JSON queries: `naadp_bp`, `naadp_bp_zebrafish`, `naadp_bp_discovery`, `naadp_bp_paralog_mine` (Compara paralog mine), plus the special-mode presets `naadp_bp_domain_scan` (`"mode": "domain_scan"`) and `naadp_bp_all` (`"mode": "exhaustive"` — full harvest + every analysis). Presets may carry `known_paralogs` and a `discovery` block of scorer-threshold overrides, honoured by both the CLI and the GUI Discovery dialog. |
| `cache/` | On-disk JSON cache (auto-created, gitignored). |
| `results/` | Committed analysis output — one directory per task. `s0_baseline/` holds the S0 database snapshot (`symbol_table.tsv` + the raw pre-screen hits, `symbol_collision.tsv`, `pfam_counts.tsv`, `pfam_taxonomy.tsv`), the **signature-scope measurement** (`signature_scope.tsv`, `signature_recall.tsv` — why the census denominator changed, D25), the literature audit (`lit_claims.tsv`, `references.tsv`), the Ensembl endpoint probe, the smoke-test record (`smoke_test.json`) and the rendered `report.md`. `benchmark_controls/` holds the S1 control benchmark: both panels as fetched (+ the unresolved-symbol lists and `symbol_collisions.tsv`), the InterPro domain hits, the MAFFT trace, `scores.tsv` (every record × every run), `partition_assignment.tsv`, `bait_margin.tsv`, `size_component.tsv` (the D22/D29 measurement), `crossfamily_identity.tsv` (**D28**), `alignment_width_effect.tsv`, `ensembl_reprobe.tsv`, `figures/s1_scorer_validation.png` and the rendered `report.md`. `toolchain_manifest.txt` records the exact tool versions every later task shells out to. |
| `manuscript/` | The submission package, built by `scripts/s14_assemble.py` in S14a. See `manuscript/README.md`; nothing here is hand-edited except the numbered section files. |

## `scripts/` — roadmap-session tooling (not part of the app)

Ported and ready to use from session one:

| File | Purpose |
|------|---------|
| `dashboard.py` | **Project dashboard generator** (stdlib-only) → `dashboard.html` (gitignored): overall + per-task progress parsed from the roadmap ledger, a live panel for the in-progress task driven by `results/session_live.json`, key figures (explicit list first, then auto-discovered from `results/*/figures/*.png`, base64-embedded), and FINDINGS.md rendered. Meta-refreshes every 30 s. Session protocol step 0: `--open` plus a background `--watch`. |
| `figstyle.py` | **The one figure style every publication figure goes through.** Page geometry imported from `s14_lib`, so a figure is drawn at the width it is placed at. The validated palette: `PARALOG` (the fixed JPT2 / LSM12 trio), `GROUP` (adds the non-vertebrate grade and the JPT1 outgroup in accent violet), `STATUS`/`QUALITY` (the ordered blue→grey→red evidence scales), `CLINICAL` (reserved status colours). `panel()`, `despine()`, `hgrid()`, and `save()`, which writes png+pdf at 400 dpi and **raises** rather than writing a figure whose tight bbox runs off-canvas or whose text needs a glyph the font lacks. |
| `s0_lib.py` | **S0 shared query helpers** — live UniProt / InterPro lookups that return the parsed result *and the exact URL used*, so every snapshot row carries its own provenance. `gene_exact_query()` defaults to **`taxonomy_id`** (subtree) rather than `organism_id` (exact node) — the field that decided whether yeast LSM12 existed (D23). `pick_best()` screens by length and Pfam, never by rank, and returns its reason. |
| `s0_db_snapshot.py` | **Re-derives every `[db]` number** in the background document: the species x {JPT2, LSM12, JPT1} grid run under **both** organism fields so the difference is committed rather than silently fixed, the HN1L collision, and the Pfam counts + lineage spread. → `results/s0_baseline/symbol_table*.tsv`, `symbol_collision.tsv`, `pfam_*.tsv`, `snapshot_meta.json` (every URL logged). |
| `s0_signature_scope.py` | **Asks whether the planned census signature spans its family.** Compares each family Pfam against the InterPro entry it is integrated into, and tests the known true positives for whether the planned signature actually annotates them. This is what measured PF17054 at 46.2 % of IPR033335 and caught reviewed mouse JPT2 carrying no Pfam at all (D25). |
| `s0_litsearch.py` | Europe PMC query helper — free text → structured citations (PMID / DOI / journal / year), used while auditing claims so a claim is verified against a record rather than against search-result prose. |
| `s0_lit_audit.py` | **The literature audit.** Holds every `[lit]` claim with its verdict, supporting PMIDs and evidence; fetches the citation metadata live so `references.tsv` is generated, never hand-typed. → `lit_claims.tsv`, `references.tsv`. |
| `s0_ensembl_probe.py` | **Bounded Ensembl endpoint probe with timings** — `lookup/symbol` vs `xrefs/symbol` on the same genes, plus a `ping` control. Supplies the evidence behind the ensembl notes below. → `ensembl_endpoint_probe.tsv`. |
| `s0_smoke_summary.py` | Reduces the timestamped smoke-test bundles to the small committed record the report quotes. → `smoke_test.json`. |
| `s0_report.py` | **Renders both S0 documents from the committed tables** (D13): `results/s0_baseline/report.md` and `docs/naadp_binder_review_2026.md`. Neither is hand-written. |
| `s1_toolchain.py` | **The version manifest every later task's methods section needs.** Probes each binary on PATH then in the `piezo1` conda env (D18), recording *where* it resolved. → `results/toolchain_manifest.txt` + `benchmark_controls/toolchain.tsv`. |
| `s1_panels.py` | **The S1 ground truth**, fetched live from UniProt with `taxonomy_id` (D23). Every record declares its partition, because in production the partition is a property of the *search*, not a guess about the protein; records marked `BOTH` are emitted once per family. `_primary_first()` prefers entries whose **primary** symbol is the query and logs every rejected synonym match — `gene_exact:` matches synonyms, and it caught FBF1 (1,133 aa) answering to `ALB`. |
| `s1_lib.py` | S1 helpers: `MafftTracer` (the *return code* is the evidence — `_mafft` falls back to the star alignment silently), **`anonymise()`** (this family's hold-out: one named reference per partition, every other true member wearing `LOC<accession>`, because a single-member family cannot be symbol-held-out without disabling half the scorer), `components()`, `bait_margins()`, TSV I/O. |
| `s1_runs.py` | The scorer arrangements — `run_joint` (D14-violating, needs `allow_cross_partition=True`) and `run_parts` — plus the InterPro domain cache, `crossfamily_identity()` (**the number D14 turns on**) and `alignment_width_effect()`. |
| `s1_benchmark.py` | The driver: six experiments in a fixed order, the joint runs **first** so the fix cannot erase its own evidence. Writes tables only. |
| `s1_figures.py` | The S1 figure: cross-family vs within-family identity with the twilight zone shaded, and every JPT-partition score with the sister test on/off. |
| `s1_report.py` + `s1_report_sections.py` | Render `results/benchmark_controls/report.md` from the committed tables (D13). |
| `s14_lib.py` | Manuscript-assembly shared helpers: page geometry, the section order, the main / Extended Data / Supplementary figure maps (the *plan* — source paths are where the tasks write their figures), the deposit rules, and stdlib TSV/JSON/SHA-256/PNG-size helpers. |
| `s14_figures.py` | Copies every committed figure into `manuscript/figures/` under its publication number, in every format the analysis produced. Nothing is re-plotted, so a manuscript figure cannot differ from the one in its results directory; files not in the manifest are deleted on every build. |
| `s14_claims.py` | **The manuscript's drift guard.** Every load-bearing number is declared with its source table and the op that recovers it (`count` / `cell` / `nunique` / `sum` / `json` / `grep`, with `col__startswith` and `col__in` filters). Ships with an empty `CLAIMS` list and a worked example of each op. |
| `s14_deposit.py` | Walks the deposited tree → `deposit_manifest.tsv` with size + SHA-256 per file, and `deposit_notes.md` listing the bulk classes deliberately excluded **with the command that regenerates each**. |
| `s14_pdf.py` | The typeset PDF: builds a pandoc markdown with each figure placed above its own legend, then xelatex via pandoc. Three traps are handled in code and commented there. |
| `s14_assemble.py` | The driver — ordered stages `figures → claims → stitch → deposit`; `--only` / `--from` / `--list`; non-zero exit on a missing figure, a missing section or a failed claim. |
| `build_findings_page.py` + `findings_page.css` | Renders `docs/findings_summary.md` to one self-contained HTML page, inlining every linked figure as a downscaled WebP data URI, with a paralog summary card read live from the committed tables (and omitted entirely until they exist, so it cannot show a card of zeroes). |

Each ledger task adds its own `s<n>_*.py` here. The PIEZO project's
equivalents (`../piezo_genes/scripts/`, mapped in its `INTERFACE.md`) are
reference implementations worth reading first.

## `src/utils/family.py` — the family definition

**The single place the project's subject is defined** — and for this project
it carries the constraint the whole repo turns on:

* **`FAMILY_PARTITIONS`** — the two unrelated families, `JPT` (PF17054,
  120–260 aa) and `LSM12` (PF09793 + PF21166, 150–280 aa), each with its own
  members, signatures and band. **Nothing may compute an identity, a tree or
  a novelty score across a partition boundary** (roadmap D14).
  **Implemented in S1**: `utils/partitions.py` assigns every record to a
  family and `discovery/candidates.py` raises `CrossPartitionError` on a
  mixed set, so a cross-family number cannot be produced by omission. The
  route for a mixed set is
  `discovery/partition.py:run_partitioned_discovery`, which splits *before
  the alignment*.
* `SISTER_PARALOGS = ["JPT1", "HN1"]` — the decoy is *inside* the family and
  carries the identical Pfam. No domain signature separates binder from
  non-binder (D21).
* `SYMBOL_COLLISIONS` — `gene_exact:HN1L` returns CRAMP1 (Q96RY5, 1,269 aa)
  alongside the real JPT2 (Q9H910, 190 aa). Screen by length and Pfam, never
  by rank.
* `MIN_LENGTH_AA`/`MAX_LENGTH_AA` (120–280) — declared for the machinery,
  **not quotable as evidence** (D22): the decoy sits inside the band.
* `REFERENCE_PANEL` — one canonical member per partition. `SISTER_PANEL` —
  human and mouse JPT1.

Pointing this app at another family is an edit of this file plus the presets.

## `src/core/` — data models, search orchestration, caching

| File | Key types / functions |
|------|-----------------------|
| `models.py` | `ProteinVariant`, `GeneRecord`, `SearchQuery`, `SearchResult`, `SearchStatus`. |
| `cache.py` | `DiskCache(root, ttl_s)` — JSON-file cache keyed by `(source, query)`. |
| `search.py` | `SearchOrchestrator(cache, email, …)` — fans queries across enabled DBs on worker threads, marshals results back via `queue.Queue`. Special-cases Foldseek (waits for sequence clients, harvests bait sequences). Re-exported **lazily** from `src/core/__init__.py` (PEP 562) so importing `src.utils` does not drag in biopython — the session-protocol data-root check has to run in a bare interpreter. |

## `src/databases/` — one client per source, common interface

| File | Class | Notes |
|------|-------|-------|
| `base.py` | `DatabaseClient` | Abstract; subclasses implement `search()`. |
| `ncbi.py` | `NCBIClient` | Biopython `Bio.Entrez` against the `protein` index. |
| `ensembl.py` | `EnsemblClient` | `rest.ensembl.org` `/lookup/symbol/{species}/{symbol}` → `/lookup/id?expand=1` → transcripts → translations; `xrefs` is only a fallback. **S0 re-probed this on 2026-08-18 and the picture is worse than 'xrefs is broken': the whole service was degraded.** `/info/ping` answered in 0.61 s, but `lookup/symbol` averaged **19.8 s** over five calls (27.6 s for human JPT2) and `xrefs/symbol` gave two 30 s timeouts and one HTTP 503; zebrafish `lookup/symbol` returned HTTP 400. In the smoke runs Ensembl returned HTTP 500 for the JPT symbols and empty for LSM12, and lost the full-panel run to the deadline. Evidence: `results/s0_baseline/ensembl_endpoint_probe.tsv`. **Re-probe before depending on it.** |
| `uniprot.py` | `UniProtClient` | `rest.uniprot.org/uniprotkb/search`; surfaces canonical + named isoforms. |
| `alphafold.py` | `AlphaFoldClient` | `alphafold.ebi.ac.uk/api/prediction/{acc}` — pivots off UniProt; reports pLDDT and model URLs. |
| `foldseek.py` | `FoldseekClient` | `search.foldseek.com/api/` — async structure-based remote-homology search; opt-in. |
| `compara.py` | `ComparaClient` | **Phylogenomic paralog mining** via Ensembl Compara gene trees — every within-species paralog of the query genes, regardless of naming. Flags adjacent family loci as possible split gene models. Note: binders and JPT1s share a gene tree, so its paralog lists include JPT1 orthologs by design. |
| `blast.py` | `BlastClient` | **Sequence-bait BLAST** via NCBI's public queue — blastp of the longest fetched sequence per gene against nr; finds homologs however they are named. Async, 2–10 min. |
| `entrez_util.py` | **The one place NCBI calls get a timeout.** Biopython's `Bio.Entrez` passes no timeout to `urlopen`, so a stalled NCBI read blocks its worker thread forever — measured in S0, where the first smoke test sat 15 minutes at 0 % CPU in `PySSL_select` while the orchestrator waited on it. `ensure_socket_timeout()` bounds every socket created without an explicit one; `entrez_call()` wraps each Entrez call with that bound plus retries, and **raises** rather than returning an empty result that would read as a real absence. Every `Bio.Entrez` call in the repo goes through it. |
| `interpro.py` | (functions) | InterPro/Pfam helpers — `list_proteins_with_pfam()` (census mode: `max_results=None` paginates to the API's own count, with retries, `strict` failure, raw-page `dump_dir`, `stats` out-dict), `batch_fetch_family_signatures()`, `has_family_signature()`, `fetch_uniprot_sequence()`. Not in `AVAILABLE_CLIENTS`; used by discovery + domain scan. |

`AVAILABLE_CLIENTS: dict[str, type[DatabaseClient]]` in
`databases/__init__.py` is what the orchestrator looks up by name;
`SEQUENCE_SOURCES` / `STRUCTURE_SOURCES` group them for the UI, and
`BAIT_SOURCES` (`BLAST`, `Foldseek`) marks clients the orchestrator runs
*after* the sequence DBs, feeding them the longest fetched sequence per gene
as bait.

## `src/gui/` — tkinter/ttk widgets

| File | Class | Responsibility |
|------|-------|----------------|
| `app.py` | `MainWindow` | Top-level window, menus, status bar, queue polling, export, bundle save (+ report). Exposes `run(project_root, email)` and `load_variants()`. |
| `search_panel.py` | `SearchPanel` | Gene + species + DB checkboxes + preset loader; routes `"mode": "domain_scan"` presets to `on_special_preset`. |
| `results_view.py` | `ResultsView` | Sortable / filterable `ttk.Treeview` of variants; `add_context_action()` adds right-click items. |
| `details_view.py` | `DetailsView` | Read-only labels + clickable URL + scrollable sequence preview. |
| `tools.py` | `ToolsController` | The **Analysis menu**: sequence analysis, novel-paralog discovery, domain-bait scan, deep-dive investigation, selection test (dN/dS), fold check (ESMFold), presence/absence matrix, and `augment_bundle()`. |
| `dialogs.py` | `AnalysisDialog`, `DiscoveryDialog`, `InvestigateDialog`, `DomainScanDialog`, `SelectionTestDialog`, `FoldCheckDialog` | Modal option dialogs; read `.result` after construction. |
| `task_runner.py` | `TaskRunner` | One-at-a-time worker-thread bridge, results marshalled back via queue + `after()`. |
| `text_window.py` | `TextWindow` | Reusable scrollable monospace output window with Save-as. |
| `phylo_view.py` | `PhyloWindow` | **Alignment & tree viewer**: canvas phylogram (novel tips ★-marked) over a conservation-shaded alignment overview. |

## `src/analysis/` — alignment, tree, clustering, mutations, evolution

| File | Key types / functions |
|------|-----------------------|
| `alignment.py` | `pairwise_align()`, `progressive_msa()` (star / MAFFT-optional). |
| `distance.py` | `identity_matrix(covered_only=False)` → `DistanceTable`; `covered_only=True` scores identity over mutually covered columns only (fragment-aware). |
| `tree.py` | `build_nj_tree()`, `tree_to_newick()`, `tree_to_ascii()`. |
| `clusters.py` | `cluster_variants()` → `ClusterReport` with novel-candidate flags. |
| `mutations.py` | `call_mutations()` → list of `MutationCall` vs a reference. |
| `evolution.py` | `conservation_per_column()`, `variable_regions()`. |
| `selection.py` | **dN/dS** (Nei–Gojobori 1986, pure Python): `ng86()`, `fetch_cds()`, `candidate_partners()`, `selection_test()`. |
| `presence.py` | **Presence/absence retention matrix** → `PresenceReport` (member × species counts + retention calls; auto-flags lineage-specific retention). |
| `motifs.py` | **Family-signature PSSMs**: `derive_family_signatures()` → `FamilySignatureSet.scan()` — the domain-evidence fallback for candidates absent from UniProt/InterPro. |
| `esmfold.py` | **ESMFold segment fold-check** (`api.esmatlas.com`): mean pLDDT for a ≤400 aa segment — for binders, the C-terminal pore module. |
| `figures.py` | Publication figures (matplotlib): heatmap, NJ tree, conservation, length histogram, sources bar. |
| `pipeline.py` | `analyse(variants, …)` — the full pipeline; `write_analysis()` persists artefacts. |

## `src/discovery/` — novel-paralog hunter

| File | Key types / functions |
|------|-----------------------|
| `candidates.py` | `DiscoveryConfig`, `Candidate`, `DiscoveryReport`, `discover_novel_paralogs(…)`. Composite 8-criterion scorer + **promotion evidence gate** (D3: score ≥ 40 requires ≥ 1 family-specific component — outlier / domain / fold / split — else capped at 39) + the **sister-family test** (D14/D7, added in S1): a candidate closer to a labelled JPT1 bait than to any known binder paralog, by more than `sister_margin` (0.10), is assigned to the sister family and capped at 39, with the margin recorded. It is a positive test on distances — the candidate's own gene symbol is never consulted — and the length band is deliberately not part of the call. **Measured here in S1: without it, 5/5 JPT1 decoys are promoted — at 80 for the three carrying PF17054 and 60 for the two that do not — and specificity falls 58/58 → 53/58.** (The sibling ITPR project's equivalent number was 6/6 at 45; that is *its* measurement, not this one.) **S1 also added the partition guard** — every run is checked against the JPT/LSM12 boundary and raises, with `allow_cross_partition=True` as the explicit opt-out the benchmark used to measure the distortion — the `size_component_points` knob (D29), and a fix for a scoring bug: `restrict=known_labels or None` turned an *empty* known set into "no restriction", so the outlier, cluster and sister components scored candidates against their nearest neighbour of any kind. Defaults read from `utils/family.py`. |
| `partition.py` | **One analysis and one scorer pass per family** — `run_partitioned_discovery()` splits **before the alignment**, so each family gets its own MSA, identity matrix and tree and a cross-family cell has nowhere to exist. Unassignable records come back explicitly, never dropped (the D24 lesson applied to partitioning). Takes `signature_sets=` so a signature built from *named* members can be applied to unnamed candidates (**D30**). Plus `merge_reports()` (presentation only — every candidate keeps its partition tag) and `partition_table()`. |
| `writer.py` | `write_discovery()` — split out of `candidates.py` so one on-disk schema is shared by the CLI, domain scan, exhaustive hunt and GUI. |
| `domain_scan.py` | `run_domain_scan(…)` — the fourth-paralog hunt: enumerate every protein with a family Pfam ID via InterPro, filter out known paralogs *and the non-binding paralogs*, fetch sequences, run analysis + discovery. |
| `exhaustive.py` | `run_exhaustive_hunt(…)` — the all-in-one `"mode": "exhaustive"` pipeline: Compara mine + ortholog expansion + InterPro enumeration → merged census (`naadp_bp_like_census.csv` + FASTA) → analyse + discovery + presence matrix + highlighted tree + bundle/report. |

## `src/investigation/` — deep-dive on one candidate accession

| File | Key types / functions |
|------|-----------------------|
| `pipeline.py` | `Investigator(accession, options).run(on_progress)` → `InvestigationResult`; `InvestigationOptions` (panel defaults to human JPT2 / LSM12 from `utils/family.py`). |
| `synthesis.py` | `assess_signals()`, `verdict_from_signals()`, `render_case_file()`. |
| `domain_arch.py` | Line 1 — full InterPro domain architecture. |
| `uniprot_detail.py` | Line 2 — detailed UniProt cross-refs + TM regions. |
| `structure.py` | Lines 3–4 — AlphaFold pLDDT + optional Foldseek. |
| `phylo_context.py` | Line 5 — panel MSA + NJ placement vs the known paralogs. |
| `synteny_lite.py` | Line 6 — genomic coordinates / neighbourhood. |
| `literature.py` | Line 7 — PubMed search, keyword from `utils/family.py`. |

## `src/utils/`

| File | Functions |
|------|-----------|
| `family.py` | The family definition (see above). |
| `partitions.py` | **The D14 guard.** `assign_partition()` (provenance → family Pfam → symbol, returning the reason it was made), `split_by_partition()`, `partitions_present()`, and `assert_single_partition()`, which **raises** `CrossPartitionError` rather than warning. Note what assignment is *not*: placing a protein in the JPT partition says it is a Jupiter-family protein, which JPT1 also is (D21). |
| `species.py` | `SpeciesInfo`, `SPECIES_LOOKUP`, `DEFAULT_SPECIES_PANEL`, `resolve_species()`, `ensembl_species_slug()`. Covers the model organisms, the teleost 3R lineages and the non-metazoan margins. |
| `data_root.py` | `get_data_root()` (falls back to `<project>/data` with a warning), **`require_data_root()`** (raises — use before anything bulk), `free_bytes()`. `python -m src.utils.data_root --require` is the session-protocol check. |
| `exporters.py` | `write_fasta()`, `write_csv()`, `write_json()`. |
| `results_writer.py` | `make_bundle_dir()`, `write_bundle()`. |
| `report.py` | `write_report()` — publication-style markdown + standalone HTML with embedded figures. |

## `src/web/` — read-only results dashboard (web app + static GitHub Pages site)

Reads only files committed at git HEAD; nothing here computes a result. `python run_web.py` → http://127.0.0.1:8175;
`scripts/build_static.py` exports the same pages to `site/` (published by `.github/workflows/pages.yml`).

| File | Purpose |
|------|---------|
| `committed.py` | `read_bytes()`/`read_text()` via `git show HEAD:<path>` (never the working tree), `tracked(prefix)`, `head()`, and `provenance(path)` → file, last commit touching it, date, SHA-256 prefix, GitHub link. |
| `parse.py` | `table()` (TSV/CSV → columns/rows, capped), `md_tables()`, `ledger()` (task ledger, analysis block, emergent tasks, "Next session"), `status_kind()` (the repo's status words → display class), `pending_markers()` (FINDINGS.md `(pending: …)`). |
| `panels.py` | Stage pages: `baseline()` (S0 snapshot tables + species × symbol grid), `literature()` (claims + references), `benchmark()` (summary.json run metrics, scores, bait margins, distortion, identity, S1 tables, figure). |
| `pages.py` | `overview()` (headline tiles, each with source file + cell/row filter + commit), `ledger_data()`, `findings()` (markers × ledger status), `trees()` (committed tree files, else pending tasks), `reports()`/`report()`, `tables()`/`one_table()`, `figure_paths()`. |
| `app.py` | FastAPI routes under `/api`; `STATIC_ENDPOINTS` (JSON) and `STATIC_FILES` (committed PNG figures) for the static export. |
| `static/` | Front end, plain ES modules, no build step: `index.html`, `core.js` + `style.css` (shared web kit, unchanged), `style_app.css`, `main.js`, `static_api.js`, `ui.js` (provenance, badges, tables, tooltips), `md.js` (markdown renderer), `chart.js` (SVG dot chart), one module per page: `home`, `ledger`, `baseline`, `literature`, `benchmark`, `findings`, `trees`, `reports`, `tables`, `about`. |

Also: `run_web.py`, `requirements-web.txt`, `scripts/build_static.py`, `scripts/screenshots.py` (Playwright smoke test +
README images in `docs/img/`), `tests/test_web.py`.

## `src/cli.py` — headless pipeline

`run_headless(project_root, preset, …, analyze, discover, interpro_lookup,
save_results)`: load preset → build `SearchQuery` (`"mode": "domain_scan"`
presets route to `run_domain_scan`) → `SearchOrchestrator` fans queries →
optional `analyse()` → optional `discover_novel_paralogs()` → optional
`write_bundle()` + `write_report()`.
`run_investigate(project_root, accession, …)` deep-dives one accession.

## Data Flow

```
SearchPanel.on_search ──▶ MainWindow._on_search ──▶ SearchOrchestrator.start
                                                          │
                                            ┌─────────────┼─────────────┐
                                            ▼             ▼             ▼
                                   NCBI / Ensembl / UniProt / Compara / AlphaFold
                                            │             │             │
                                            └────────┬────┴─────────────┘
                                                     ▼
                                          (sequence DBs done)
                                                     ▼
                                gather longest sequences ──▶ BLAST + Foldseek
                                                     ▼
                                                queue.Queue
                                                     ▼
                                  MainWindow._drain_queue (after())
                                                     ▼
                                              ResultsView.extend
                                                     ▼
                                                DetailsView.show
```

Post-search, the **Analysis menu** (`ToolsController` + `TaskRunner`) runs
`analyse()` / `discover_novel_paralogs()` / `run_domain_scan()` /
`Investigator` on a worker thread and shows results in `TextWindow`s.
---

## What is *not* here yet

Compared with the sibling `../ip3r_genes`:

| Missing | Why | Arrives in |
|---|---|---|
| `scripts/s2_*.py` | the census enumeration is S2's deliverable | S2 |
| `jpt.hmm` / `lsm12.hmm` profiles | S1 measured that the labelled-bait margin cannot call the deep grade (fly Jupiter is inside the D7 no-call band), so the profile route is **required**, not a cross-check | S3 |
| an LSM12 sister panel | `SISTER_PARALOGS` names only JPT1/HN1; the LSM12 partition has no equivalent positive test, and its specificity rests on the domain component alone | S2/S20 |
| any functional test | everything so far separates binder from paralog by distance to a labelled bait; nothing here can say a protein *binds NAADP* (D21) | S17 |

This project is at **S1 complete**. Read
`results/benchmark_controls/report.md` before S2 — it carries the four
constraints S2 inherits: the signature fallback (and that it must be built
from the *named* panel), `family.py:SISTER_PANEL` in every JPT search, the
primary-symbol rule for `pick_best`, and Ensembl's continued unreliability.
