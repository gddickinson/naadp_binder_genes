# FINDINGS.md — what this project has discovered

A dated, plain-language entry per completed task: what changed in the
biological story, findings before methods, unconfirmed claims marked
*(pending: which task confirms it)*. Methods and file paths stay out of it.

---

## 2026-08-18 — Project set up; the problem, stated plainly

**The receptor that took twenty years to find.** NAADP is the most powerful
calcium-releasing signal known inside cells, and for two decades nobody
could say what it binds to. The obvious candidate — a channel called the
two-pore channel — turned out to be the thing NAADP *opens*, not the thing
it *touches*. What it actually touches are two very small proteins, JPT2 and
LSM12, which sit between the signal and the channel. This project is a
census of those two proteins; its sibling is a census of the channel.

**They are two strangers that do the same job.** JPT2 and LSM12 are not
relatives. They have no shared structure, no shared ancestry anyone can
detect, nothing in common except that both bind the same small molecule.
That is unusual enough to be interesting on its own — a signal with two
unrelated readers — and it makes the analysis awkward, because almost every
tool for studying a protein family assumes the family's members can be
compared to each other. These two cannot. *(pending: S1, S6, S7)*

**The hardest part is a protein that looks identical and does nothing.**
JPT2 has a close relative, JPT1, that carries the same structural signature
and is nearly the same size — and does not bind NAADP. Every standard way of
recognising a protein family says these two are the same thing. Only their
detailed sequence can tell them apart. Finding what that difference is, and
whether evolution has protected it, is the sharpest question here: if a
specific patch of JPT2 is conserved across all vertebrates and absent from
JPT1, that patch is very likely where NAADP binds. *(pending: S9, S17)*

**A question neither project can answer alone.** If these proteins exist to
make a channel respond to NAADP, then the proteins and the channel should
travel together through evolution — species with one should have the other.
Checking that requires both censuses side by side, and it is the reason
these two projects were built as a pair. *(pending: S23)*

## 2026-08-18 — S0: the baseline holds, but two of the "absences" were ours

**The published story checks out, with one date corrected and one credit
reassigned.** Every claim this project rests on was traced back to the paper
that first made it. NAADP really is the most potent calcium-releasing
messenger known — it works at around thirty billionths of a molar. The
two-pore channel really was proposed as its receptor and then shown not to
touch NAADP at all: when researchers used a light-activated tag to catch
whatever NAADP grabs onto, the channel was never among the catch, and the
catching still happened in animals engineered to have no channel. And JPT2
and LSM12 really are what NAADP grabs.

Two details were wrong in our own summary. We had written that the receptor
went unidentified "for roughly two decades"; it was **twenty-six years** from
the moment the messenger was named, and thirty-four from the first hint of
it. And we had credited both proteins with acting on the ryanodine receptor.
Only JPT2 does. LSM12's reported partner is the two-pore channel alone.

**The decoy problem is real, and it has now been measured by someone else.**
The whole project is built around JPT1 — the protein that looks like JPT2 by
every family test and does not bind NAADP. It turns out this was tested
directly and published: JPT1 shows no measurable grip on NAADP at all, while
JPT2 and LSM12 both bind it at around one billionth of a molar, and removing
JPT1 from cells changes nothing. So the premise holds. What is new, and what
makes the task harder than expected, is the number that came with it: **JPT1
and JPT2 are about 40 % identical**. That is the gap any method here has to
see across — not a chasm, a hairline.

**Two of the blank cells in our species table were not absences at all.**
We had a table of which species have which protein, and a row of blanks for
yeast, flies, worms and plants. Two of those blanks have now closed without
any new data being gathered.

Yeast has an LSM12. It is a reviewed, well-annotated protein carrying both
of the structural signatures we look for, and we could not see it because of
how the question was phrased — we asked about the species and the protein is
filed under a particular laboratory strain of it. Flies have a Jupiter-family
protein too; in fact the whole family is *named* after the fly protein. It
simply is not called JPT2.

Neither of these is a discovery about biology. Both are a warning about the
census: **the blanks in a table of gene names are statements about naming,
not about genomes** — and this project's headline claim is going to be a
statement about which lineages have these proteins and which do not. Every
remaining blank now has to be re-tested by sequence rather than by name.
*(pending: S2, S20)*

**The net we planned to cast has a hole in it.** We intended to enumerate the
whole JPT family using one structural signature. That signature turns out to
cover **fewer than half** the proteins in its own family — and, more
pointedly, it misses the mouse version of JPT2, which is as well-studied a
member as exists. Had the census run as planned, it would have quietly
excluded a known true member of the very family it was counting. The wider
family-level catalogue entry recovers it, and that is what will be used.
*(pending: S2)*

**One more thing worth saying plainly.** Two faults in our own software were
found by simply trying to run it end to end. One could hang the whole
pipeline indefinitely; the other could produce a result file that looked
like a complete survey when a third of the databases had never answered. The
second is the one that matters biologically: this project's central output is
a claim that certain species *lack* these proteins, and a tool that silently
reports "we looked and found nothing" when it never looked at all is the
exact way such a claim goes wrong. Both are fixed.

---

## S1 — 2026-08-18 · Can we tell the binder from its twin?

**The decoy wins unless we measure distance, and we now know by how much.**
JPT1 is the same size as JPT2, carries the identical structural signature,
and does not bind NAADP. We put five of them — human, mouse, rat, frog, cow
— into the discovery pipeline as deliberate impostors, alongside sixteen
unrelated proteins of the same size and the entire ancient Lsm protein
family. With the pipeline's distance test switched off, **every single JPT1
was accepted as a candidate binder**, three of them at the highest
confidence the scorer can express. With the test switched on, all five were
rejected, and nothing else in the panel moved. This is the sharpest possible
statement of the project's central problem: *no structural signature
separates the NAADP binder from its non-binding twin*. What separates them
is how close each sits to a correctly-labelled example — and that is a much
more fragile instrument than a domain.

**How fragile is now measured, and it fails exactly where the interesting
biology is.** The distance test works cleanly across the vertebrates, where
JPT2 and JPT1 stay comfortably apart. It breaks on the deep branch. The
fruit-fly Jupiter protein — the founding member of the family, the one it is
named after — sits so close to the midpoint that the test refuses to call
it, and under the more sensitive measurement we plan to adopt later it
actually points to the wrong side. **So the further back in evolutionary
time we look, the less this method can tell us**, and the non-vertebrate
range question is precisely where we expect the novel biology to be. That
question will have to be answered by profile models rather than by distance.
*(pending: S3, S20)*

**A third of our JPT2s are invisible to the catalogue.** Mouse, rat and cow
JPT2 are real, well-studied proteins — the mouse one is manually reviewed —
and none of them carries the structural signature the census was going to
use to find them. Search for the family that way and you lose half your
vertebrate examples without any warning that you have. We built a fallback
that recognises members by the conserved sequence blocks the known members
share, and it recovered all three, with no cost in false positives. **The
census will therefore not treat "no signature" as "not in the family"** —
which, for a project whose headline output is a list of species that *lack*
these proteins, is the difference between a result and an artefact.

**The two families interfere with each other, but only under one specific
condition — and it is the condition we are heading into.** We have insisted
from the start that JPT2 and LSM12 must never be compared to each other,
since they share a ligand and nothing else. Testing that assumption produced
a more precise answer than expected. As long as *each* family has at least
one correctly-named member in the search, mixing them changes essentially
nothing: every protein finds its real relatives and the unrelated family is
simply too distant to interfere. But the moment one family has **no named
member** — which is exactly what happens when we sweep genomes of flies,
fungi and plants where nothing carries a recognisable name — the pipeline
starts scoring those proteins against the *other* family, and nearly every
score changes. Two genuine LSM12s were promoted on evidence borrowed from an
unrelated human protein. The separation is now enforced in code rather than
by convention: the software refuses to compare across the boundary at all.

**A warning we have written down before it can bite us.** We plan to switch
to a more sensitive way of measuring similarity, because it handles partial
sequences better. Measured on the current data, that switch would raise the
apparent similarity between JPT2 and LSM12 — two proteins with no common
ancestry — from at most 11 % to as much as 39 %, and would put one in eight
cross-family comparisons into the range the software treats as evidence of
an exciting new relative. Nothing is wrong with the more sensitive
measurement; what would be wrong is using it without the family boundary
enforced. *(pending: S6)*

**And one small, slightly embarrassing lesson about names.** While assembling
a list of ordinary unrelated proteins to use as controls, we asked the
database for albumin and it returned a completely different, twice-as-long
protein that happens to list "ALB" among its alternative names — and our
selection rule preferred it. We already knew about one such trap in this
project, involving JPT2's own alias. Finding a second one by accident, on
the first ordinary gene we happened to pick, says the problem is common
rather than special. Every name-based lookup in the census now has to
confirm it got the protein that actually *has* that name, not one that
merely answers to it.
