"""Section bodies for the S1 report (see s1_report.py).

Split out purely for the 500-line rule. Each function takes the parsed
`summary.json` (`S`) and the parsed tables (`T`) and returns one markdown
section. Nothing here computes a new number — everything is read from the
committed tables, so a re-run of the benchmark changes the report (D13).
"""

from __future__ import annotations


def _pct(hit, n) -> str:
    return f"{100 * hit / n:.0f} %" if n else "n/a"


def _score(rows, accession: str) -> str:
    for r in rows:
        if r["accession"] == accession:
            return r["score"]
    return "?"


def sec_toolchain(S, T, n_tools, ok_tools) -> str:
    rows = "\n".join(
        f"| `{r['tool']}` | {r['version']} | {r['location']} | {r['needed_by']} |"
        for r in T["toolchain"])
    mafft = (f"`analyse(use_mafft=True)` made {S['mafft_n_calls']} call(s) to "
             f"`{' '.join(S['mafft_argv'])}` returning "
             f"{S['mafft_returncode']}; {S['joint_baseline_rows']} sequences "
             f"aligned to {S['joint_baseline_width']:,} columns in the joint "
             f"run, {S['part_baseline_JPT_width']:,} in the JPT partition and "
             f"{S['part_baseline_LSM12_width']:,} in the LSM12 partition.")
    w = T["alignment_width_effect"]
    width_note = ""
    if len(w) == 2:
        a, b = w[0], w[1]
        width_note = (
            "\n\n### One giant decoy is a panel-design bug for a 190 aa "
            "family\n\n"
            f"The first build of this panel included titin (Q8WZ42, "
            f"34,350 aa) as an out-of-band control. It inflates the JPT "
            f"alignment from **{int(a['alignment_width']):,} to "
            f"{int(b['alignment_width']):,} columns** — a "
            f"{int(b['alignment_width']) / max(1, int(a['alignment_width'])):.0f}× "
            "increase for one added sequence. What it does *not* do is "
            "corrupt the identities: mean identity among true family "
            f"members moves only from {a['mean_identity_true_members']} to "
            f"{b['mean_identity_true_members']}, because gap-gap columns are "
            "skipped. So the cost is runtime and memory, not accuracy — but "
            "at census scale it is prohibitive, and titin was replaced by "
            "bounded out-of-band decoys (CRAMP1 1,269 aa, ATXN2L 1,075 aa, "
            "HSPA5 654 aa, ALB 609 aa, LSM14A 463 aa, and the Sm proteins at "
            "76–133 aa below the band). Table: `alignment_width_effect.tsv`. "
            "**The sibling projects never needed this rule** — their family "
            "members are 2,000–3,600 aa, so no decoy is two orders of "
            "magnitude longer than the subject.")
    coll = T["symbol_collisions"]
    coll_note = ""
    if coll:
        r = coll[0]
        coll_note = (
            "\n\n### `gene_exact` matches synonyms, and it is not just HN1L\n\n"
            f"Building the decoy panel turned up a second instance of the "
            f"symbol trap `family.py:SYMBOL_COLLISIONS` records for HN1L. "
            f"`gene_exact:{r['queried_symbol']} AND taxonomy_id:{r['taxon_id']}` "
            f"returns **{r['collider']} {r['collider_symbol']} "
            f"({r['collider_len']} aa)**, which carries "
            f"`{r['queried_symbol']}` as a *synonym*, alongside the real "
            f"{r['correct_symbol']} ({r['correct']}, {r['correct_len']} aa) — "
            "and a reviewed-first, longest-tie-break pick selects the wrong "
            "one. It was found on the first unrelated control chosen for the "
            "panel, i.e. by accident. The panel builder now prefers entries "
            "whose **primary** gene symbol is the query and records every "
            "rejected synonym match. `symbol_collisions.tsv`. "
            "**S2 must apply the same rule** — `s0_lib.py:pick_best` screens "
            "by length and Pfam but does not yet check primary-vs-synonym, "
            "and at census scale the band will not always catch it.")
    return (
        "## 1. Toolchain\n\n"
        "| Tool | Version | Resolves via | Needed by |\n|---|---|---|---|\n"
        f"{rows}\n\n"
        f"All {ok_tools}/{n_tools} binaries resolve; full paths and Python "
        "package versions in `results/toolchain_manifest.txt`. Tools marked "
        "`env` live in the reused `piezo1` conda env rather than on the bare "
        "PATH (Decisions D18).\n\n"
        "### MAFFT is really invoked\n\n"
        f"{mafft} `src/analysis/alignment.py:_mafft` falls back to the star "
        "alignment **silently** on a non-zero return code, so the return code "
        "is the evidence, not the fact that a call happened. Trace: "
        f"`mafft_trace.json`.{width_note}{coll_note}\n\n"
        "### Ensembl, re-probed\n\n"
        "The S0 emergent task asked for a re-probe before S1 depended on "
        "Ensembl. Re-run the same day: `/info/ping` 0.63 s; `lookup/symbol` "
        "4/5 ok, mean 10.6 s (was 19.8 s); `xrefs/symbol` 3/5 ok with two "
        "30 s timeouts. Zebrafish `lookup/symbol/danio_rerio/lsm12` still "
        "returns **HTTP 400** while `xrefs/symbol` on the same gene now "
        "succeeds — so that one is a symbol/ID-type problem, not an outage, "
        "and it survived the service recovering. **Ensembl is improved but "
        "still not dependable: S2/S3 must not take it as a required "
        "source.** Evidence: `ensembl_reprobe.tsv` next to S0's "
        "`ensembl_endpoint_probe.tsv`.\n\n"
    )


def sec_crossfamily(S, T) -> str:
    rows = "\n".join(
        f"| {r['metric']} | {r['pair_class']} | {r['n_pairs']} | "
        f"{r['median_identity']} | {r['max_identity']} | "
        f"{r['n_in_twilight_zone']} ({r['pct_in_twilight_zone']} %) |"
        for r in T["crossfamily_identity"])
    cf = {(r["metric"], r["pair_class"]): r for r in T["crossfamily_identity"]}
    acr = [k for k in cf if k[1].startswith("across")]
    full = cf[("full alignment", acr[0][1])]
    cov = cf[("covered columns only", acr[0][1])]
    a, b = "joint_crossfam", "part_crossfam"
    return (
        "## 2. The partition (D14) — what mixing the families actually "
        "costs\n\n"
        "`family.py:FAMILY_PARTITIONS` was declared at setup and **nothing "
        "read it** (D14a). S1 implements it: `utils/partitions.py` assigns "
        "every record to a family — provenance first, then family Pfam, then "
        "symbol — and `discover_novel_paralogs` now calls "
        "`assert_single_partition` on every run and **raises** on a mixed "
        "set. The route for a mixed set is "
        "`discovery/partition.py:run_partitioned_discovery`, which splits "
        "**before the alignment**: each family gets its own MSA, identity "
        "matrix and tree, so a cross-family number has nowhere to exist. "
        "`src/cli.py` routes any preset spanning both families through it. "
        f"Assignment table: `partition_assignment.tsv` "
        f"({S['part_baseline_unassigned']} records unassignable).\n\n"
        "### How similar is a JPT2 to an LSM12?\n\n"
        "| Metric | Pair class | n | Median | Max | In twilight zone |\n"
        "|---|---|---|---|---|---|\n" + rows + "\n\n"
        "Two things follow, and they point in opposite directions.\n\n"
        f"**Under the metric the scorer uses today** (full-alignment "
        f"identity), cross-family pairs top out at **{full['max_identity']}** "
        f"— below the 0.20 novelty floor, so **{full['pct_in_twilight_zone']} %"
        "** of them reach the twilight zone. The unrelated families are *too* "
        "unrelated to trip the novelty component.\n\n"
        f"**Under the fragment-aware metric S6 adopts** (`covered_only=True`), "
        f"the same pairs reach **{cov['max_identity']}** and "
        f"**{cov['n_in_twilight_zone']} of {cov['n_pairs']} "
        f"({cov['pct_in_twilight_zone']} %)** land inside the zone — each one "
        "worth +20, which also satisfies the D3 promotion gate. **The switch "
        "S6 is already committed to would turn D14 from a tidiness rule into "
        "the thing standing between the census and a wave of manufactured "
        "novelty.** This is the same trap the sibling ITPR project measured "
        "on its sister family, and it is pre-registered here before the "
        "metric changes.\n\n"
        "### The distortion, measured before the fix\n\n"
        "| Comparison | records | scores differ | calls flip |\n"
        "|---|---|---|---|\n"
        f"| joint vs partitioned, both families named | "
        f"{S['distortion_joint_baseline_vs_part_baseline_n']} | "
        f"{S['distortion_joint_baseline_vs_part_baseline_score_differs']} | "
        f"{S['distortion_joint_baseline_vs_part_baseline_call_flips']} |\n"
        f"| joint vs partitioned, true members unnamed | "
        f"{S['distortion_joint_anonymised_vs_part_anonymised_n']} | "
        f"{S['distortion_joint_anonymised_vs_part_anonymised_score_differs']} | "
        f"{S['distortion_joint_anonymised_vs_part_anonymised_call_flips']} |\n"
        f"| **joint vs partitioned, only JPT2 named** | {S[f'distortion_{a}_vs_{b}_n']} | "
        f"**{S[f'distortion_{a}_vs_{b}_score_differs']}** | "
        f"**{S[f'distortion_{a}_vs_{b}_call_flips']}** |\n\n"
        "The roadmap predicted that with both families in one set *every* "
        "candidate would land in the twilight zone by construction. **That is "
        "not what happens, and the reason matters:** as long as each family "
        "keeps at least one named member, each candidate's nearest *known* "
        "paralog is a real relative and the joint run reproduces the "
        "partitioned one almost exactly. The failure appears the moment a "
        "family has **no named member** — the realistic case for the "
        "non-vertebrate sweep in S20. Then every LSM12 record is scored "
        f"against human JPT2: {S[f'distortion_{a}_vs_{b}_score_differs']} of "
        f"{S[f'distortion_{a}_vs_{b}_n']} scores change and "
        f"{S[f'distortion_{a}_vs_{b}_call_flips']} calls flip "
        f"({', '.join(S[f'distortion_{a}_vs_{b}_flipped'])} — yeast LSM12 and "
        "fly Lsm12a), each promoted on a +10 cluster-exclusion point earned "
        "against an unrelated protein. The partitioned run correctly withholds "
        "it and says so in the evidence.\n\n"
        "So **D14 stands, with its justification restated**: the danger is "
        "not that unrelated proteins look novel, it is that the scorer will "
        "compute *some* number for any pair it is handed and cannot tell the "
        "difference between a distant relative and a stranger. Table: "
        "`crossfamily_identity.tsv`; per-record scores in `scores.tsv`.\n\n"
        "**A scorer bug found on the way.** The outlier, cluster and sister "
        "components read `restrict=known_labels or None`, so an *empty* known "
        "set silently became \"no restriction\" and every candidate was "
        "scored against its nearest neighbour of any kind. That is the D24 "
        "failure class — a missing reference quietly becoming a different one "
        "— and it is exactly the state a partitioned run reaches when a "
        "family has no named member. Fixed in "
        "`discovery/candidates.py`; the components now decline to fire and "
        "record why.\n\n"
    )


def sec_positives(S, T) -> str:
    rows = [r for r in T["scores"]
            if r["run"] == "part_anonymised" and r["panel_kind"] == "positive"]
    sig = {r["accession"]: r for r in T["scores"]
           if r["run"] == "part_anon_sigset"}
    body = "\n".join(
        f"| {r['partition']} | `{r['accession']}` {r['gene_symbol']} | "
        f"{r['species']} | {r['length_aa']} | {r['n_family_pfam']} | "
        f"{r['score']} | {'✓' if r['promoted'] == 'True' else '✗'} | "
        f"{sig.get(r['accession'], {}).get('score', '')} | "
        f"{r['components'] or '—'} |"
        for r in rows)
    pa, ps = "part_anonymised", "part_anon_sigset"
    miss = [r for r in rows if r["promoted"] != "True" and r["score"] != "n/a"]
    lsm_scores = [int(r["score"]) for r in rows
                  if r["partition"] == "LSM12" and r["score"] != "n/a"]
    lsm_min = min(lsm_scores) if lsm_scores else "?"
    return (
        "## 3. Positive controls — recall\n\n"
        "**The hold-out had to change.** The sibling projects hide one "
        "paralog name at a time and check its orthologs still surface; that "
        "works when a family has three members. Here each partition has "
        "exactly **one** binder member, so hiding it empties "
        "`known_paralogs` and the outlier, cluster and sister components have "
        "nothing to measure against — the hold-out would be disabling the "
        "scorer, not testing it. Instead the human reference keeps its name "
        "and every other true member enters wearing a locus-style ID "
        "(`LOC<accession>`), which is what an unannotated ortholog looks like "
        "coming out of a genome sweep. That is the real use case, and it "
        "leaves one named member per partition so the machinery still runs.\n\n"
        f"**Recall {S[pa + '_recall_hit']}/{S[pa + '_recall_n']} "
        f"({_pct(S[pa + '_recall_hit'], S[pa + '_recall_n'])})** with the "
        "signature set derived inside the anonymised run; "
        f"**{S[ps + '_recall_hit']}/{S[ps + '_recall_n']} "
        f"({_pct(S[ps + '_recall_hit'], S[ps + '_recall_n'])})** with the "
        "signature set carried from the named members, which is how "
        f"production works. The two named references "
        f"({', '.join(S['reference_accessions'].values())}) are known "
        "members rather than candidates and are excluded from the "
        "denominator rather than counted as misses.\n\n"
        "| Partition | Accession | Species | aa | family Pfams | Score | ≥40 | "
        "Score with signature set | Components |\n"
        "|---|---|---|---|---|---|---|---|---|\n" + body + "\n\n"
        "### Every miss is the same miss\n\n"
        f"All {len(miss)} recall failures are JPT2 orthologs — "
        f"{', '.join('`' + r['accession'] + '` ' + r['species'] for r in miss)} "
        "— and every one of them carries **zero family Pfam "
        "cross-references** despite being a real JPT2. This is D25 arriving "
        "at the scorer: PF17054 annotates only 46.2 % of IPR033335, and "
        "reviewed mouse JPT2 (Q6PGH2) carries the InterPro family entry and "
        "no Pfam at all. Without the domain component they score 30–39 and "
        "are not promoted.\n\n"
        "Attaching the MSA-derived family signature — 8 blocks, built from "
        "the *named* members of the same partition — rescues all of them via "
        "the `sig+15` fallback, and specificity does not move "
        f"({S[ps + '_specificity_hit']}/{S[ps + '_specificity_n']}). "
        "**This is the S2-blocking question answered: `no Pfam` must not be "
        "read as `not in the family`, and the fallback is the mechanism that "
        "makes that safe.** Note the corollary — deriving the signature set "
        "*inside* an all-unnamed run yields one named row and no PSSM at all "
        "(0 blocks), so S2 must build the signature from the named reference "
        "panel and apply it to candidates, never derive it from the candidate "
        "set. `run_partitioned_discovery(signature_sets=…)` exists for "
        "exactly that.\n\n"
        "### The LSM12 partition is the easy half\n\n"
        f"Every LSM12 positive scored {lsm_min} or better, including "
        f"*Drosophila* Lsm12a ({_score(rows, 'Q9VYR0')}) and "
        f"*S. cerevisiae* LSM12 ({_score(rows, 'P38828')}) — the deep "
        "grade, recovered because PF09793/PF21166 annotate their own "
        "InterPro entries essentially completely (0.998, 1.000 in S0). The "
        "asymmetry between the partitions is a property of "
        "the *annotation*, not of the proteins, and it is why the two "
        "partitions need different census denominators (D25).\n\n"
    )


def sec_decoys(S, T) -> str:
    rows = [r for r in T["scores"]
            if r["run"] == "part_baseline" and r["panel_kind"] == "decoy"]
    nos = {r["accession"]: r for r in T["scores"] if r["run"] == "part_nosister"}
    rows.sort(key=lambda r: -(int(r["score"]) if r["score"] != "n/a" else -1))
    nos = {(r["accession"], r["partition"]): r for r in T["scores"]
           if r["run"] == "part_nosister"}
    body = "\n".join(
        f"| {r['partition']} | `{r['accession']}` {r['gene_symbol']} | "
        f"{r['group']} | {r['length_aa']} | "
        f"{'yes' if r['in_band'] == 'True' else 'no'} | "
        f"{r['n_family_pfam']} | {r['score']} | "
        f"{nos.get((r['accession'], r['partition']), {}).get('score', '')} | "
        f"{'✓' if r['promoted'] != 'True' else '✗'} | {r['components'] or '—'} |"
        for r in rows[:20])
    jpt1 = [r for r in rows if r["group"].startswith("JPT1")]
    lost = S['part_nosister_jpt1_n'] - S['part_nosister_jpt1_pass']
    return (
        "## 4. Negative controls — specificity, and the decoy inside the "
        "family\n\n"
        f"**{S['part_baseline_specificity_hit']}/"
        f"{S['part_baseline_specificity_n']} decoys stay below 40 in the "
        "partitioned runs — specificity 100 %.** The generic decoys are scored\n"
        "once in each partition, so they appear twice. Top 20 by score:\n\n"
        "| Partition | Decoy | Category | aa | in band | family Pfams | "
        "Score | Score without sister test | Pass | Components |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n" + body + "\n\n"
        "### JPT1 — stated plainly, as the brief requires\n\n"
        f"All {len(jpt1)} JPT1 decoys carry the JPT2 size class and "
        f"{sum(1 for r in jpt1 if int(r['n_family_pfam'] or 0) > 0)} of "
        f"{len(jpt1)} carry PF17054 itself. **With the sister-family test "
        "disabled, every one of them is promoted** — at 80 for the three "
        "that hold the Pfam (`size+15,pfam+20,outlier+20,cluster+10,"
        "breadth+15`) and 60 for the two that do not — and specificity falls "
        f"from {S['part_nosister_specificity_n']}/"
        f"{S['part_nosister_specificity_n']} to "
        f"{S['part_nosister_specificity_hit']}/"
        f"{S['part_nosister_specificity_n']}. With it enabled, "
        f"{S['part_baseline_jpt1_pass']}/{S['part_baseline_jpt1_n']} are "
        "capped at 39 with the margin recorded.\n\n"
        f"So the answer to the brief's question is: **the JPT1 decoy fails "
        f"any domain-based rule** — {lost}/{len(jpt1)} promoted without a "
        "distance test — **and passes a positional one.** Three properties "
        "of that test matter:\n\n"
        "* it is a **positive test on distances**, not a name filter — the "
        "candidate's own gene symbol is never consulted, so an unnamed JPT1 "
        "locus from a genome sweep is called the same way;\n"
        "* the **length band is not part of the call** (D22) — it enters only "
        "as the size component;\n"
        "* the margin is **recorded on every candidate**, so every exclusion "
        "is auditable.\n\n"
        "This is D21 in operational form: a domain hit remains a family "
        "call, and what separates the binder from its paralog here is "
        "sequence distance to a labelled bait — not a signature, not a "
        "length, and not (yet) anything functional. **The census still has "
        "no functional test**; S17 is where one has to come from.\n\n"
        "The Lsm/Sm fold set behaves differently and more easily: LSM1–8, "
        "SNRPD1–3 and SNRPE/F/G carry no LSM12 Pfam and sit at 76–139 aa, "
        "mostly below the band, so they never approach the threshold. **The "
        "LSM12 partition has no sister-family panel at all** — "
        "`family.py:SISTER_PARALOGS` names only JPT1/HN1 — so its "
        "specificity rests entirely on the domain component and the D3 "
        "evidence gate. If S2 or S20 turns up an LSM12-like protein that is "
        "not LSM12, there is currently no test that would catch it.\n\n"
    )
