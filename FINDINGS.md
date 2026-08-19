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
