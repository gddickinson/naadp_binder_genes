# S0 — literature baseline + scope confirmation

*Rendered by `scripts/s0_report.py` on 2026-08-18 from the tables in this directory (Decisions D13). Every number below is read back out of a committed TSV.*

## Headline

- **The setup snapshot reproduces.** 13 of the 30 symbol-table cells resolve to exactly the accessions and lengths recorded at setup; 1 further cell(s) resolve only after the query fix below. No setup number was contradicted.
- **The census signature for the JPT partition is wrong.** PF17054 covers less than half its own InterPro family entry, and misses a reviewed true positive. See *Signature scope*.
- **A query field, not a genome, produced one of the absences.** Switching `organism_id` to `taxonomy_id` changes the call in 1 of 30 cells — and the cell it recovers is a reviewed entry. See *The organism-field artefact*.
- 8 literature claims audited against 19 references; the background document needs one correction, one refinement, one re-tag.
- **A blocking app bug was found and fixed**: every `Bio.Entrez` call in the repo had no timeout. See *Smoke test*.

## The symbol table, re-derived

Source: `symbol_table.tsv` (30 cells), `symbol_table_raw.tsv` (every hit before screening). Queried live on the date above; screened by length and Pfam, never by rank (`family.py:SYMBOL_COLLISIONS`).

| Species | JPT2 | LSM12 | JPT1 |
|---|---|---|---|
| human | Q9H910 190 aa (SP) PF17054 | Q3MHD2 195 aa (SP) PF09793;PF21166 | Q9UK76 154 aa (SP) PF17054 |
| mouse | Q6PGH2 190 aa (SP) **no Pfam** | Q9D0R8 195 aa (SP) PF09793;PF21166 | P97825 154 aa (SP) PF17054 |
| chicken | *not found by symbol* | Q5ZML5 194 aa (SP) PF09793;PF21166 | *not found by symbol* |
| X. tropicalis | A0A6I8PKV3 192 aa (TR) PF17054 | Q6P833 194 aa (SP) PF09793;PF21166 | I7KJP8 143 aa (TR) **no Pfam** |
| zebrafish | F1Q6E4 218 aa (TR) PF17054 | Q6PBA2 196 aa (SP) PF09793;PF21166 | *not found by symbol* |
| fly | *not found by symbol* | Q9VYR0 217 aa (SP) PF09793;PF21166 | *not found by symbol* |
| worm | *not found by symbol* | *not found by symbol* | *not found by symbol* |
| Arabidopsis | *not found by symbol* | *not found by symbol* | *not found by symbol* |
| yeast | *not found by symbol* | P38828 187 aa (SP) PF09793;PF21166 | *not found by symbol* |
| Dictyostelium | *not found by symbol* | *not found by symbol* | *not found by symbol* |

## The organism-field artefact

UniProt's `organism_id` matches **one taxonomy node exactly**; `taxonomy_id` matches the node **and its descendants**. The setup snapshot used the first. Both were run here and both are recorded in `symbol_table.tsv` (`organism_id_result` / `field_changes_call`).

| Cell | taxonomy_id (subtree) | organism_id (exact node) |
|---|---|---|
| yeast / LSM12 | found — P38828 (187 aa, SP, PF09793;PF21166) | not found by symbol |

One cell, and it is a reviewed Swiss-Prot entry carrying both declared LSM12 signatures. It was invisible because the reviewed entry sits under the strain node while the project's species table carries the species node. **This is a false absence produced by a query field.** The remaining blanks are genuine naming differences, not this artefact.

## Signature scope — can the planned census signature see the family?

Source: `signature_scope.tsv`, `signature_recall.tsv`. S2 plans to enumerate the census from the Pfam IDs in `family.py`. This asks whether those IDs span their families.

| Partition | Signature | Proteins | InterPro entry | Type | InterPro proteins | Fraction |
|---|---|---:|---|---|---:|---:|
| JPT | PF17054 | 1360 | IPR033335 Microtubule-associated protein Jupiter | family | 2944 | 0.462 |
| LSM12 | PF09793 | 3161 | IPR019181 LSM12, anticodon-binding domain | domain | 3166 | 0.998 |
| LSM12 | PF21166 | 1718 | IPR048478 LSM12, LSM domain | domain | 1718 | 1.0 |
| JPT | (family-level entry) | — | IPR033335 Microtubule-associated protein Jupiter | family | 2944 | — |
| LSM12 | (family-level entry) | — | IPR039683 Protein Lsm12-like | family | 3165 | — |

**PF17054 sees 46.2 % of the InterPro Jupiter family entry it belongs to** (1,360 of 2,944 proteins; the PANTHER member covers the rest). The LSM12 signatures are effectively complete for their own entries. So the two partitions need different treatment, and the asymmetry is not something the roadmap anticipated.

Recall against known true positives (13 proteins, 2 missed):

| Protein | Accession | Status | Length | Planned Pfam | Annotated Pfam | InterPro |
|---|---|---|---:|---|---|---|
| mouse_JPT2 | Q6PGH2 | SP | 190 | PF17054 | NONE | IPR033335 |
| X. tropicalis_JPT1 | I7KJP8 | TR | 143 | PF17054 | NONE | IPR033335 |

Mouse JPT2 is a **reviewed Swiss-Prot** entry and the canonical mouse ortholog of the human binder. A census built on PF17054 would not contain it. Both misses carry IPR033335, so the family-level entry recovers them.

## The HN1L symbol collision, re-measured

Source: `symbol_collision.tsv`.

| Accession | Length | Status | Pfam | Correct? | Longest-first pick? |
|---|---:|---|---|---|---|
| Q96RY5 | 1269 | SP | PF27753 | False | True |
| Q9H910 | 190 | SP | PF17054 | True | False |

Reproduced exactly. A longest-first pick selects the wrong protein; the Pfam screen separates them cleanly, since the decoy carries an unrelated signature.

## Pfam counts (S2's denominator)

| Pfam | Partition | UniProt proteins |
|---|---|---:|
| PF17054 | JPT | 1,360 |
| PF09793 | LSM12 | 3,164 |
| PF21166 | LSM12 | 1,718 |

## Literature audit

Source: `lit_claims.tsv`, `references.tsv`. Full text: `../../docs/naadp_binder_review_2026.md`.

| Claim | Verdict | Action |
|---|---|---|
| L1 — NAADP is the most potent Ca2+-mobilising second messenger known.… | verified, with a qualification | Keep, but attribute. The superlative is a comparative statement from a review, not a head-to-head pr… |
| L2 — For roughly two decades its receptor was unidentified — the 'mis… | **corrected** | Correct to 'for more than a quarter of a century (1995-2021)'.… |
| L3 — Two-pore channels were proposed and widely accepted as the answe… | verified | Keep as written.… |
| L4 — NAADP binds two small accessory proteins, JPT2 (also HN1L) and L… | verified, wording refined | Refine: attach the ryanodine-receptor clause to JPT2 alone, not to both binders.… |
| L5 — The channel and the receptor are different molecules.… | verified | Keep as written.… |
| L6 — JPT1 (HN1), 154 aa, carries PF17054 — the same signature as JPT2… | **re-tagged** | Split the tag: [db] for the signature and length, [lit] for the non-binder status. D21 rests on the … |
| L7 — JPT1 and JPT2 share ~40% amino acid identity.… | verified | Add to the background document. This is the number that calibrates the S1 sister-margin: binder and … |
| L8 — The blank cells in the species table are symbol-query artefacts,… | verified | Keep the [open] tag on the table's blanks and add these two worked counter-examples. Adopt taxonomy_… |

## Smoke test

| Partition | Preset | Variants | Sources returning | Bundle |
|---|---|---:|---|---|
| JPT | `jpt` | 642 | NCBI=ok(356), UniProt=ok(286) | 2026-08-18_183358_s0_smoke_jpt |
| JPT | `jpt` | 46 | UniProt=ok(22), NCBI=ok(24), Ensembl=error(0) | 2026-08-18_184510_s0_smoke_jpt_human |
| LSM12 | `lsm12` | 25 | UniProt=ok(16), NCBI=ok(9), Ensembl=empty(0) | 2026-08-18_184544_s0_smoke_lsm12_human |
| LSM12 | `lsm12` | 242 | UniProt=ok(122), NCBI=ok(120) | 2026-08-18_184901_s0_smoke_lsm12 |

NCBI and UniProt returned on every run. **Ensembl did not**, and the failure is server-side rather than in this repo: the S0 endpoint probe (`ensembl_endpoint_probe.tsv`) measured `/info/ping` at 0.61 s while `lookup/symbol` averaged 19.8 s over five calls and `xrefs/symbol` returned two timeouts and one HTTP 503. In the runs above Ensembl returned HTTP 500 for the JPT symbols and an empty result for LSM12. The completion criterion 'NCBI, Ensembl and UniProt all return' is therefore **met for two of three sources**, with the third documented as a live outage and its behaviour now correctly recorded rather than silently dropped.

Read the four runs together: the two `Homo sapiens` runs were made **after** the D24 fix and name Ensembl explicitly with its status (`error` / `empty`); the two full-panel runs were made **before** it and Ensembl is simply *absent* from their `per_source` list — which is the bug D24 describes, preserved here as its own evidence.

**A blocking bug was found here and fixed.** Every `Bio.Entrez` call in the repo passed no timeout, and Biopython hands `urlopen` none by default, so a stalled NCBI read blocks its worker thread forever. The first smoke-test attempt sat for 15 minutes at 0 % CPU in `PySSL_select` with the orchestrator's main thread waiting on it. Fixed in `src/databases/entrez_util.py`, which every Entrez call in the repo now goes through.

## Provenance

- Queries issued for the database snapshot: 67 (each URL logged in `snapshot_meta.json`).
- Snapshot date: 2026-08-18; Python 3.11.15.
