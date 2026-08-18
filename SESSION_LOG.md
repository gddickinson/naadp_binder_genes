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
