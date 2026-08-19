# The NAADP-binding proteins — biology baseline

Every statement carries a tag: `[db]` verified against a live database,
with the query; `[lit✓]` verified against a primary source in S0, with the
citation; `[open]` a question this project exists to answer.

**S0 audited this document on 2026-08-18.** Every `[lit]` tag is now either
`[lit✓]` with a citation or has been corrected. The audit itself, with the
evidence behind each verdict, is `naadp_binder_review_2026.md`; the
measurements are `../results/s0_baseline/report.md`. Citations are given as
`[PMID:…]` and resolve in `../results/s0_baseline/references.tsv`.

---

## The problem these proteins solved

`[lit✓]` NAADP is the most potent Ca(2+)-mobilising second messenger known.
Half-maximal Ca(2+) release occurs at **~30 nM** in sea urchin egg
homogenate, with NADP and NAAD ineffective at 10–40× higher concentrations
[PMID:7836444]. The superlative itself is a comparative statement from a
review, and its source hedges it — "NAADP is arguably the most tantalizing.
It is the most potent, often efficacious at low nanomolar concentrations"
[PMID:31182546]. **Quote the ~30 nM, not the superlative.**

`[lit✓]` **For more than a quarter of a century its receptor was
unidentified** — the "missing NAADP receptor" problem. The Ca(2+)-mobilising
activity was reported in 1987 [PMID:3496336], the active species identified
as NAADP in 1995 [PMID:7836444], and the binding proteins only in 2021
[PMID:33758061; PMID:33758062; PMID:34362892]. That is 26 years from the
messenger, 34 from the original observation. *(S0 correction: this document
previously said "roughly two decades", which understates it.)*

`[lit✓]` Two-pore channels were proposed and widely accepted as the answer
[PMID:19387438; PMID:19557428; PMID:19940116], then shown not to bind NAADP
directly. Photoaffinity labelling could not label endogenous or
overexpressed TPCs, and labelling survived in TPC1 and TPC2 knockout mouse
pancreas, implying "an accessory component within a larger TPC complex"
binds NAADP [PMID:22117075]; in sea urchin the labelled proteins are smaller
than the sea urchin TPCs [PMID:22117077]. Separately, TPCs were shown to be
PI(3,5)P2-activated Na(+)-selective channels [PMID:23063126].

`[lit✓]` The resolution: NAADP binds two small accessory proteins, **JPT2**
(also HN1L) and **LSM12**, which then confer NAADP sensitivity onto the
two-pore channels [PMID:33758061; PMID:34362892; PMID:37607218]. **The
ryanodine-receptor arm belongs to JPT2 alone** — TCR/CD3-dependent
coprecipitation of HN1L/JPT2 with RYRs in T cells [PMID:33758062] — and is
not reported for LSM12, whose described targets are TPC1/TPC2. *(S0
refinement: this document previously attached the RyR clause to both
binders.)* The channel and the receptor are different molecules
[PMID:37607218].

`[open]` Whether JPT2 and LSM12 act redundantly, in different cell types, or
on different channels — and whether either is the ancestral binder.

## What the databases hold

`[db]` UniProt, `gene_exact:<symbol> AND taxonomy_id:<taxid>`, best entry
screened **by length and Pfam** (never by rank), re-derived live 2026-08-18
by `scripts/s0_db_snapshot.py` → `../results/s0_baseline/symbol_table.tsv`:

| Species | JPT2 | LSM12 | JPT1 (decoy paralog) |
|---|---|---|---|
| human | Q9H910 190 aa (SP) PF17054 | Q3MHD2 195 aa (SP) PF09793,PF21166 | Q9UK76 154 aa (SP) PF17054 |
| mouse | Q6PGH2 190 aa (SP) **no Pfam xref** | Q9D0R8 195 aa (SP) | P97825 154 aa (SP) PF17054 |
| chicken | *not found by symbol* | Q5ZML5 194 aa (SP) | *not found by symbol* |
| *X. tropicalis* | A0A6I8PKV3 192 aa (TR) PF17054 | Q6P833 194 aa (SP) | I7KJP8 143 aa (TR) **no Pfam xref** |
| zebrafish | F1Q6E4 218 aa (TR) PF17054 | Q6PBA2 196 aa (SP) | *not found by symbol* |
| fly | *not found by symbol* (**but see below**) | Q9VYR0 217 aa (SP) | *not found by symbol* |
| yeast | *not found by symbol* | **P38828 187 aa (SP) PF09793,PF21166** | *not found by symbol* |
| worm, *Arabidopsis*, *Dictyostelium* | *not found by symbol* | *not found by symbol* | *not found by symbol* |

`[db]` **LSM12 reaches further by symbol than JPT2 does** — it resolves in
*Drosophila* and in *S. cerevisiae*, where JPT2 does not.

### Two blanks were not absences, and S0 proved it without leaving the desk

`[db]` **Yeast LSM12 exists and the setup query could not see it.** P38828
(LSM12_YEAST, 187 aa, reviewed) carries **both** declared LSM12 signatures.
It was invisible because UniProt's `organism_id` matches **one taxonomy node
exactly** while `taxonomy_id` matches the node **and its descendants**: the
reviewed entry sits under the S288c strain node (559292) and this project's
species table carries the species node (4932). Switching field recovers it
and changes **exactly one** of the thirty cells. Roadmap **D23**.

`[lit✓]`/`[db]` **The fly JPT2 blank is a naming artefact.** PF17054 is
named for the *Drosophila* protein Jupiter [PMID:16518797], and UniProt
Q9I7K0 (JUPIT_DROME, 208 aa, reviewed) carries PF17054 and IPR033335. The
fly has a Jupiter-family protein; it is not called JPT2.

`[open]` The remaining blanks are still **symbol-query results, not genome
facts**, and now with two demonstrated mechanisms behind them: a query-field
artefact and a naming difference. Nothing here is an absence until S2/S20
has re-tested it by sequence.

## The census signature does not span the JPT family

`[db]` Measured in S0 (`../results/s0_baseline/signature_scope.tsv`):

| Partition | Planned signature | Proteins | Its InterPro entry | InterPro proteins | Fraction |
|---|---|---:|---|---:|---:|
| JPT | PF17054 | 1,360 | IPR033335 (family) | 2,944 | **0.462** |
| LSM12 | PF09793 | 3,161 | IPR019181 (domain) | 3,166 | 0.998 |
| LSM12 | PF21166 | 1,718 | IPR048478 (domain) | 1,718 | 1.000 |

`[db]` **PF17054 sees less than half of its own family**; the PANTHER member
(PTHR34930) covers the rest. Worse, it misses a *reviewed* true positive:
**mouse JPT2 (Q6PGH2) carries IPR033335 but no PF17054 cross-reference**, as
does *X. tropicalis* JPT1 (I7KJP8). 11 of 13 known members carry their
planned Pfam; both misses are in the JPT partition and both are recovered by
the family-level entry.

`[open]` S2 therefore cannot enumerate the JPT partition from PF17054 alone.
The family-level entries are **IPR033335** (Jupiter, 2,944 proteins) and
**IPR039683** (Lsm12-like, 3,165 proteins). The two partitions need
different denominators, which the roadmap did not anticipate.

## Two families, not one

`[db]` JPT2 carries PF17054 (Jupiter/HN1 family). LSM12 carries PF09793 +
PF21166. There is no shared domain, and no alignment between them is
meaningful.

This is the project's central methodological constraint. The pipeline was
built for a family whose members are mutually comparable; here, every
distance-based measurement must be computed **within** a partition
(`family.py:FAMILY_PARTITIONS`) and never across.

`[open]` How much damage does the ported scorer take when run over both
families at once? Measuring it is S1's first job, and the answer is a
methods result in its own right.

## The decoy is inside the family

`[db]` **JPT1 (HN1), 154 aa, carries PF17054 — the same signature as
JPT2.** (Re-derived live: Q9UK76, 154 aa, reviewed, PF17054.)

`[lit✓]` **JPT1 is not a NAADP binder, and this was tested directly.**
Gunaratne *et al.* 2023 profiled JPT1 alongside JPT2 and LSM12: no selective
[32P]-NAADP binding in radioligand assays (IC50 not determinable, against
**1.09 nM for JPT2** and **0.703 nM for LSM12**); JPT1 knockout had no
effect in Ca(2+) imaging or in pseudovirus trafficking; and the paper
concludes that the data "validate both JPT2 and LSM12 (but not JPT1) as bona
fide NAADP-binding proteins" [PMID:37607218]. *(S0 re-tag: this document
previously carried the whole statement as `[db]`. The signature and length
are `[db]`; the non-binder status is `[lit✓]`, and **D21 rests on this
half**.)*

`[lit✓]` **JPT1 and JPT2 are ~40 % identical in amino acid sequence**, "the
dual representatives of this conserved gene family in higher vertebrates",
with JPT2 at 174–218 aa against JPT1 at 154 aa [PMID:37607218]. The length
range matches what S0 re-derived (190–218 aa for JPT2).

Three consequences:

1. **No domain signature distinguishes binder from non-binder.** A Pfam hit
   is a family call, never a function call.
2. **The size band is nearly useless here.** JPT1 154 aa against JPT2
   190 aa, inside a declared band of 120–280 aa; the sibling projects could
   lean on a 2,000 aa gap and this one cannot.
3. Whatever separates them is sequence detail. Finding it — the residues
   that differ between the binder and its paralog across the vertebrates —
   is a real deliverable, not a footnote.

`[open]` Is there a conserved, JPT2-specific surface absent from JPT1? Does
it correspond to the NAADP-binding site? **The ~40 % identity is the number
that sets the difficulty**: the separation S1 needs has to resolve well
inside a gap that wide.

## A symbol collision, measured

`[db]` `gene_exact:HN1L` returns **two** human proteins: Q9H910 (190 aa,
PF17054, the real JPT2/HN1L) and Q96RY5, "Protein cramped-like" (CRAMP1,
**1,269 aa**, PF27753), which matches on the synonym alone. A longest-first
pick selects the wrong protein; the Pfam screen separates them cleanly.
Re-measured in S0 (`../results/s0_baseline/symbol_collision.tsv`) and
recorded in `family.py:SYMBOL_COLLISIONS`.

## What the project sets out to answer

1. What is each binder's true taxonomic range, once symbol artefacts are
   removed?
2. **Does binder presence track two-pore-channel presence across
   lineages?** The sibling project (`../naadpr_genes`) supplies the channel
   half; this is the co-occurrence test neither can do alone.
3. What distinguishes JPT2 from JPT1 at sequence level, and is it
   constrained?
4. When did the JPT1/JPT2 duplication happen, and does LSM12 have an
   equivalent paralog problem?
5. How much does a two-family project distort a one-family scorer?
