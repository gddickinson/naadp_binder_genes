"""S1 report sections 5-7 — the margin, the size component, and the
limits (see s1_report.py).

Split from `s1_report_sections.py` for the 500-line rule. Same contract:
read the committed tables, compute nothing new (D13).
"""

from __future__ import annotations


def sec_margin(S, T) -> str:
    rows = [r for r in T["bait_margin"] if r["run"] == "part_baseline"]
    all_j2 = [r for r in rows if r["truth"] == "JPT2"]
    # The deep grade is a different question from the vertebrate panel and
    # must not be averaged into it — that is what "separates cleanly" would
    # otherwise be hiding.
    true_j2 = [r for r in all_j2 if r["panel_note"] != "deep_grade"]
    true_j1 = [r for r in rows if r["truth"] == "JPT1"]

    def rng(rs, col):
        vals = sorted(float(r[col]) for r in rs)
        return f"{vals[0]:+.3f}…{vals[-1]:+.3f}" if vals else "—"

    deep = [r for r in all_j2 if r["panel_note"] == "deep_grade"]
    d = deep[0] if deep else None
    narrow = min(true_j2, key=lambda r: float(r["margin_cov"])) if true_j2 else None
    return (
        "## 5. The JPT2/JPT1 labelled-bait margin (D7/D14)\n\n"
        "| Class | n | identity to JPT2 bait | identity to JPT1 bait | margin "
        "| margin (fragment-aware) | calls correct |\n|---|---|---|---|---|---|---|\n"
        f"| vertebrate JPT2 orthologs | {len(true_j2)} | "
        f"{min(float(r['id_to_jpt2_bait']) for r in true_j2):.3f}–"
        f"{max(float(r['id_to_jpt2_bait']) for r in true_j2):.3f} | "
        f"{min(float(r['id_to_jpt1_bait']) for r in true_j2):.3f}–"
        f"{max(float(r['id_to_jpt1_bait']) for r in true_j2):.3f} | "
        f"{rng(true_j2, 'margin')} | {rng(true_j2, 'margin_cov')} | "
        f"{sum(1 for r in true_j2 if r['correct'] == 'True')}/{len(true_j2)} |\n"
        + (f"| deep grade (*Drosophila* Jupiter) | {len(deep)} | "
           f"{float(d['id_to_jpt2_bait']):.3f} | {float(d['id_to_jpt1_bait']):.3f} | "
           f"{float(d['margin']):+.3f} | {float(d['margin_cov']):+.3f} | "
           f"{'1/1' if d['correct'] == 'True' else '0/1'} "
           f"({'1/1' if d['correct_cov'] == 'True' else '0/1'} fragment-aware) |\n"
           if d else "") +
        f"| JPT1 decoys | {len(true_j1)} | "
        f"{min(float(r['id_to_jpt2_bait']) for r in true_j1):.3f}–"
        f"{max(float(r['id_to_jpt2_bait']) for r in true_j1):.3f} | "
        f"{min(float(r['id_to_jpt1_bait']) for r in true_j1):.3f}–"
        f"{max(float(r['id_to_jpt1_bait']) for r in true_j1):.3f} | "
        f"{rng(true_j1, 'margin')} | {rng(true_j1, 'margin_cov')} | "
        f"{sum(1 for r in true_j1 if r['correct'] == 'True')}/{len(true_j1)} |\n\n"
        f"Overall {S['bait_margin_correct']}/{S['bait_margin_n']} correct "
        f"under the full-alignment metric and "
        f"{S['bait_margin_correct_covered']}/{S['bait_margin_n']} under the "
        "fragment-aware one. The two classes separate cleanly on the "
        "vertebrate panel: the narrowest vertebrate-JPT2 margin is "
        f"{min(float(r['margin']) for r in true_j2):+.3f} "
        f"({min(float(r['margin_cov']) for r in true_j2):+.3f} "
        "fragment-aware) against a least-negative JPT1 margin of "
        f"{max(float(r['margin']) for r in true_j1):+.3f} "
        f"({max(float(r['margin_cov']) for r in true_j1):+.3f}), a gap of "
        f"{min(float(r['margin']) for r in true_j2) - max(float(r['margin']) for r in true_j1):.3f} "
        f"and {min(float(r['margin_cov']) for r in true_j2) - max(float(r['margin_cov']) for r in true_j1):.3f} "
        "respectively. Two of the five JPT1 records are the labelled baits "
        "themselves and are excluded from the count.\n\n"
        "**But the deep branch is not callable.** " +
        (f"*Drosophila* Jupiter — a genuine Jupiter-family protein — has a "
         f"margin of {float(d['margin']):+.3f} on the full alignment and "
         f"{float(d['margin_cov']):+.3f} under the fragment-aware metric, "
         "i.e. **inside the D7 no-call band both ways, and pointing at the "
         "wrong family under the metric S6 adopts.** It is not excluded (the "
         "test needs a margin beyond ±0.10 to act, and it correctly does "
         "nothing here), so Jupiter is promoted at 65 on domain evidence — "
         "but the margin contributes nothing to that call. "
         if d else "") +
        (f"And the vertebrate panel is not comfortable either: zebrafish "
         f"`{narrow['accession']}` {narrow['gene_symbol']} has a margin of "
         f"{float(narrow['margin_cov']):+.3f} under the fragment-aware "
         "metric — a true JPT2 also inside the D7 no-call band. "
         if narrow else "") +
        "**The labelled-bait margin is a vertebrate instrument.** For the "
        "non-vertebrate range question (S20) it must be replaced or "
        "supplemented by best-profile assignment (`jpt.hmm` vs a JPT1 decoy "
        "profile, S3), which is therefore not optional. Table: "
        "`bait_margin.tsv`.\n\n"
        "*(The two bait accessions are marked `bait` and excluded from the "
        "correctness count: with a single JPT2 bait, its own identity to "
        "'the nearest JPT2 bait' is 0 by construction and would score as a "
        "failure that means nothing.)*\n\n"
    )


def sec_size(S, T) -> str:
    rows = T["size_component"]
    # Whether the band excludes anything is a property of the PANEL, not of
    # one run's candidate list — a named member is not a candidate, so
    # counting inside a single run would count two records and mean nothing.
    panel = {(r["accession"], r["partition"]): r for r in T["scores"]
             if r["run"] == "part_baseline"}
    pos = [r for r in panel.values() if r["panel_kind"] == "positive"]
    dec = [r for r in panel.values() if r["panel_kind"] == "decoy"]
    in_band_pos = [r for r in pos if r["in_band"] == "True"]
    in_band_dec = [r for r in dec if r["in_band"] == "True"]
    changed = [r for r in rows if r["call_changed"] == "True"]
    n_dec_changed = sum(1 for r in changed if r["panel_kind"] == "decoy")
    body = "\n".join(
        f"| {r['partition']} | `{r['accession']}` {r['gene_symbol']} | "
        f"{r['panel_kind']} | {r['score_size15']} | {r['score_size0']} |"
        for r in changed)
    return (
        "## 6. The size component (D22) — measured, and kept\n\n"
        f"The band is 120–280 aa. Across the panel it contains "
        f"**{len(in_band_pos)}/{len(pos)} true family members and "
        f"{len(in_band_dec)}/{len(dec)} decoys** — including every JPT1 "
        "(143–154 aa) alongside every JPT2 (190–218 aa), and every one of "
        "the 16 unrelated in-band proteins chosen precisely because they "
        "are 140–248 aa. The component therefore fires on almost the whole "
        "panel and separates nothing, exactly as D22 anticipated. The "
        f"{len(dec) - len(in_band_dec)} decoys it does exclude are the "
        "deliberately out-of-band ones (CRAMP1, ATXN2L, HSPA5, ALB, LSM14A "
        "and the sub-100 aa Sm proteins), none of which was ever a "
        "plausible family member.\n\n"
        f"Recomputing every score with the component zeroed changes "
        f"**{S['size_calls_changed']} of {S['size_rows']}** promotion calls, "
        f"and **all {S['size_calls_changed'] - n_dec_changed} of them are true "
        "positives lost** — no decoy call moves at all:\n\n"
        "| Partition | Record | kind | score (size+15) | score (size+0) |\n"
        "|---|---|---|---|---|\n" + body + "\n\n"
        "**Decision: retain the component at +15 for S2, and never quote the "
        "band as evidence.** The measurement says the component carries no "
        "discriminative information — but the 40-point threshold, the D3 "
        "evidence gate and the sister test were all calibrated with it in "
        "place, and the informative components alone (`pfam+20` + "
        "`breadth+15` = 35) fall below the threshold. Zeroing it without "
        "re-deriving the threshold trades a harmless constant for a real "
        "recall loss. What it is *not* is support for a family call: no "
        "report in this repo cites length as evidence, and the sister test "
        "deliberately excludes it. Re-weighting the scorer against a "
        "recalibrated threshold is logged as an emergent task rather than "
        "done silently. Table: `size_component.tsv`.\n\n"
    )


def sec_limits(S, T) -> str:
    return (
        "## 7. What this benchmark does not establish\n\n"
        "* **No functional test exists.** Everything here separates JPT2 "
        "from JPT1 by sequence distance to a labelled bait. Nothing in this "
        "repo can yet say a protein binds NAADP (D21). S17 is where a "
        "sequence-level binder signature has to come from, if there is one.\n"
        "* **The deep grade is called on domain evidence alone.** Fly "
        "Jupiter and yeast LSM12 are promoted by `pfam+20`; the distance "
        "components either abstain or point the wrong way. For S20's "
        "non-vertebrate sweep that is the whole population, so the profile "
        "route (S3) is load-bearing, not a cross-check.\n"
        "* **Decoy provenance.** Every decoy enters as a named UniProt "
        "entry. A decoy arriving via Compara or BLAST gains the +10 "
        "homology-provenance component, so read every score in the 30–39 "
        "band as a 40+ risk on that route — that includes all five JPT1 "
        "decoys, which sit at exactly 39.\n"
        "* **Unnamed sister-family loci.** The sister test needs at least "
        "one *labelled* JPT1 bait in the analysis set. Every search that "
        "expects JPT1 contamination must carry "
        "`src/utils/family.py:SISTER_PANEL` — S2 onward.\n"
        "* **The LSM12 partition has no sister panel**, so nothing "
        "equivalent protects it.\n"
        "* **Fold and split-annotation components never fired**: no Foldseek "
        "run and no split gene models in a UniProt-only panel. Their "
        "contribution is untested.\n"
        "* **Five panel members did not resolve by symbol** — chicken JPT2 "
        "and JPT1, zebrafish jpt1, *C. elegans* lsm-12, *Arabidopsis* "
        "LSM12A. Given LSM12 resolves in chicken and zebrafish, these are "
        "more likely naming or annotation than absence; they are the S2 "
        "emergent task, and they are recorded in "
        "`panel_positives_missing.tsv` / `panel_decoys_missing.tsv` rather "
        "than omitted (D24).\n"
        "* **One species per symbol, 57 accessions.** Breadth is measured on "
        "a panel, not on the census.\n"
    )
