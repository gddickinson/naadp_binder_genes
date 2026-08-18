"""The gene family this project is built around — one definition, one place.

Everything family-specific in `src/` reads from here: the Pfam signatures a
candidate must carry, the size band a real family member falls in, the
reference proteins used as the phylogenetic comparison panel, and the
literature keyword. Porting the app to another family is an edit of this
file plus the presets, not a search-and-replace across the tree.

**This project: the NAADP-binding proteins, JPT2 and LSM12.**

NAADP is the most potent Ca(2+)-mobilising second messenger known, and for
two decades its receptor was unidentified — the "missing NAADP receptor"
problem. It was resolved by showing that NAADP does not bind the channel it
opens. It binds two small accessory proteins, JPT2 (a.k.a. HN1L, 190 aa)
and LSM12 (195 aa), which then confer NAADP sensitivity onto the two-pore
channels (the sibling project, `../naadpr_genes`) and, in some reports, on
the ryanodine receptors.

**The structural problem this project is built around.** These are not one
family. JPT2 and LSM12 are unrelated proteins that share a ligand and
nothing else — no common domain, no detectable sequence similarity, no
common ancestor within reach of alignment. The app's discovery scorer
assumes one family whose members are mutually comparable, so its
distance-based components (novelty, cluster, breadth) are **meaningless
across the JPT/LSM12 boundary** and the scorer must be run once per family.
That constraint is pre-registered as Decisions D14 in
PUBLICATION_ROADMAP.md, and measuring the damage is the first job of the
S1-equivalent benchmark.

Numbers here that come from a database (accessions, Pfam IDs, lengths) were
verified live on 2026-08-18 at project setup and are re-verified by S0 —
see `docs/session_briefs.md`.
"""

from __future__ import annotations

#: Display name of the family.
FAMILY_NAME = "NAADP-BP"

#: Long name, used in report prose.
FAMILY_LONG_NAME = "NAADP-binding protein"

#: The two declared families. `PARALOGS` is what the scorer treats as the
#: known set; `FAMILY_PARTITIONS` is the split every analysis must respect.
PARALOGS = ["JPT2", "LSM12"]

#: **The partition, and the rule that goes with it.** Each entry is
#: (family key, member symbols, Pfam signatures, size band). Nothing may
#: compute a sequence identity, a tree or a novelty score *across* two
#: partitions — the number would be noise wearing a decimal point.
FAMILY_PARTITIONS = {
    "JPT": {
        "members": ["JPT2", "JPT1"],
        "pfam": ["PF17054"],          # Jupiter / HN1 family
        "length_aa": (120, 260),
        "note": "JPT2 is the NAADP binder; JPT1 (HN1) is its close paralog "
                "and the sharp decoy — same Pfam, same size class.",
    },
    "LSM12": {
        "members": ["LSM12"],
        "pfam": ["PF09793", "PF21166"],   # Lsm12 anticodon-binding + AD
        "length_aa": (150, 280),
        "note": "PF09793 sits in the ancient Lsm/anticodon-binding fold set, "
                "so the decoy pool is deep and old.",
    },
}

#: The sharp decoy is *inside* the family, not beside it: JPT1 (HN1) carries
#: the same Pfam as JPT2, is the same size, and is not a NAADP binder. This
#: is the ITPR/RYR problem moved down to the paralog level, where the length
#: band cannot help at all.
SISTER_FAMILY = "JPT1/HN1"
SISTER_PARALOGS = ["JPT1", "HN1"]

#: Pfam signatures across both partitions. A candidate must carry at least
#: one — but note that carrying PF17054 makes a protein a JPT, not a NAADP
#: binder: no Pfam signature distinguishes the binder from its paralog.
FAMILY_PFAM_IDS = ["PF17054", "PF09793", "PF21166"]

#: Pfam IDs whose protein lists define the enumerated search space (S2).
CENSUS_PFAM_IDS = ["PF17054", "PF09793", "PF21166"]

#: Size band across both partitions, in residues. Measured at setup:
#: JPT2 190 aa (human, mouse), 192 aa (X. tropicalis), 218 aa (zebrafish);
#: JPT1 154 aa (human, mouse), 143 aa (X. tropicalis); LSM12 194-196 aa
#: across vertebrates and 217 aa in Drosophila. These proteins are small
#: enough that the band excludes almost nothing — it is close to useless as
#: evidence here, and the project says so rather than quoting it as support.
MIN_LENGTH_AA = 120
MAX_LENGTH_AA = 280

#: Reference proteins for the investigation panel — one canonical member per
#: partition, plus the decoy paralog that shares JPT2's signature.
REFERENCE_PANEL = [
    ("Hs_JPT2_Q9H910", "Q9H910"),      # 190 aa, reviewed, PF17054
    ("Hs_LSM12_Q3MHD2", "Q3MHD2"),     # 195 aa, reviewed, PF09793+PF21166
]

#: Negative-control references — the same-signature paralog and the
#: symbol-collision trap.
SISTER_PANEL = [
    ("Hs_JPT1_Q9UK76", "Q9UK76"),      # 154 aa, PF17054 — same signature
    ("Mm_JPT1_P97825", "P97825"),      # 154 aa
]

#: **A naming trap, measured at setup.** `gene_exact:HN1L` returns two
#: proteins: Q9H910 (190 aa, the real JPT2/HN1L) and Q96RY5 "Protein
#: cramped-like" (CRAMP1, 1,269 aa), which matches on the synonym alone.
#: A longest-first pick therefore selects the wrong protein — precisely the
#: failure the sibling ITPR project hit when a "reviewed" test matched
#: "unreviewed". Any symbol-driven fetch in this repo screens for it.
SYMBOL_COLLISIONS = {
    "HN1L": {"correct": "Q9H910", "collides_with": "Q96RY5",
             "reason": "CRAMP1 carries HN1L as a synonym; it is 1,269 aa"},
}

#: Literature search keyword (PubMed title/abstract).
LITERATURE_KEYWORD = "NAADP binding protein"

#: Substrings that mark a hit as an already-named family member.
KNOWN_NAME_SUBSTRINGS = [
    "jpt2", "hn1l", "jupiter microtubule associated homolog 2",
    "lsm12", "lsm-12",
]

#: Gene symbols treated as "known paralogs" by the discovery scorer unless a
#: preset overrides them.
KNOWN_PARALOGS = ["JPT2", "LSM12"]

#: These proteins are ~190 aa — small enough to fold whole. The segment
#: helper exists for the large-channel families the app was written for; it
#: is set to the full length here so nothing silently truncates.
POR_SEGMENT_FROM_END_AA = 280
