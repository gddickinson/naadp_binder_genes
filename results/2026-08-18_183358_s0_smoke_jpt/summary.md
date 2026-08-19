# Search Results — 2026-08-18 18:33:58

## Query

- **Genes**: JPT2, JPT1, HN1L
- **Species**: (any)
- **Sources**: NCBI, Ensembl, UniProt
- **Max per source**: 120
- **Sequences fetched**: yes

_Notes_: Headless run of preset 'jpt'.

## Per-source results

| Source | Status | Variants | Elapsed (s) | Message |
|--------|--------|----------|-------------|---------|
| NCBI | ok | 356 | 0.0 | (cached) |
| UniProt | ok | 286 | 0.0 | (cached) |

**Total variants**: 642

## Variants by gene × source (length range in aa)

| Gene | Source | Hits | Length range | Example accession |
|------|--------|------|--------------|--------------------|
| HN1L | NCBI | 116 | 52 – 1285 | NP_001421598.1 |
| HN1L | UniProt | 40 | 52 – 1285 | Q96RY5 |
| JPT1 | NCBI | 120 | 75 – 543 | XP_086786906.1 |
| JPT1 | UniProt | 123 | 44 – 359 | Q9UK76 |
| JPT2 | NCBI | 120 | 114 – 324 | XP_086797431.1 |
| JPT2 | UniProt | 123 | 70 – 1338 | Q9H910 |

## Cross-database length discrepancies

Same gene reported with significantly different max protein lengths across sources — flags incomplete annotation, which in a ~2,700-residue gene is the commonest way a real paralog goes uncounted.

| Gene | Per-source max length | Δ | Flag |
|------|----------------------|---|------|
| HN1L | NCBI=1285, UniProt=1285 | 0 | ok |
| JPT1 | NCBI=543, UniProt=359 | 184 | ⚠️ check annotations |
| JPT2 | NCBI=324, UniProt=1338 | 1014 | ⚠️ check annotations |

## Genes with zero hits

_All requested genes returned at least one variant._

