# The NAADP-binding proteins — biology baseline

Every statement carries a tag: `[db]` verified against a live database at
project setup (2026-08-18), with the query; `[lit]` from the literature and
**not yet verified** — S0 audits every one against a citation; `[open]` a
question this project exists to answer.

---

## The problem these proteins solved

`[lit]` NAADP is the most potent Ca(2+)-mobilising second messenger known.
For roughly two decades its receptor was unidentified — the "missing NAADP
receptor" problem. Two-pore channels were proposed and widely accepted as
the answer, then shown not to bind NAADP directly.

`[lit]` The resolution: NAADP binds two small accessory proteins, **JPT2**
(also HN1L) and **LSM12**, which then confer NAADP sensitivity onto the
two-pore channels, and in some reports onto the ryanodine receptors. The
channel and the receptor are different molecules.

`[open]` Whether JPT2 and LSM12 act redundantly, in different cell types, or
on different channels — and whether either is the ancestral binder.

## What the databases hold

`[db]` UniProt, `gene_exact:<symbol> AND organism_id:<taxid>`, best entry
(Swiss-Prot preferred, longest as tie-break), 2026-08-18:

| Species | JPT2 | LSM12 | JPT1 (decoy paralog) |
|---|---|---|---|
| human | Q9H910 190 aa (SP) PF17054 | Q3MHD2 195 aa (SP) PF09793,PF21166 | Q9UK76 154 aa (SP) PF17054 |
| mouse | Q6PGH2 190 aa (SP) | Q9D0R8 195 aa (SP) | P97825 154 aa (SP) |
| chicken | *not found by symbol* | Q5ZML5 194 aa (SP) | *not found by symbol* |
| *X. tropicalis* | A0A6I8PKV3 192 aa (TR) | Q6P833 194 aa (SP) | I7KJP8 143 aa (TR) |
| zebrafish | F1Q6E4 218 aa (TR) | Q6PBA2 196 aa (SP) | *not found by symbol* |
| fly | *not found by symbol* | Q9VYR0 217 aa (SP) | *not found by symbol* |
| worm, *Arabidopsis*, yeast, *Dictyostelium* | *not found by symbol* | *not found by symbol* | *not found by symbol* |

`[db]` **LSM12 reaches further by symbol than JPT2 does** — it resolves in
*Drosophila* where JPT2 does not.

`[open]` Every blank in that table is a **symbol-query result, not a genome
fact**. PF09793 sits in the ancient Lsm/anticodon-binding fold set, so a
true absence of LSM12 from fungi and plants would be surprising; the sibling
TPC project measured exactly this class of error (a reviewed plant two-pore
channel invisible to a vertebrate-symbol query). Nothing here is an absence
until S2/S20 has re-tested it by sequence.

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
JPT2** — and is not a NAADP binder.

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
it correspond to the NAADP-binding site?

## A symbol collision, measured

`[db]` `gene_exact:HN1L` returns **two** proteins: Q9H910 (190 aa, the real
JPT2/HN1L) and Q96RY5, "Protein cramped-like" (CRAMP1, **1,269 aa**), which
matches on the synonym alone. A longest-first pick selects the wrong
protein. Recorded in `family.py:SYMBOL_COLLISIONS`.

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
