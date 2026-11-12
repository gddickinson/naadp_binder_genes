// Home: hero, headline tiles (each with the file, cell/filter and commit it came from), completed stages, page cards.
import { api, app, esc, list, route } from './core.js';
import { badge, inline, prov } from './ui.js';

function tile(t) {
  const pend = t.pending && t.pending.length;
  return `<div class="tile"><b class="${pend ? 'pend' : ''}">${esc(t.value)}</b><span>${esc(t.label)}</span>
    ${pend ? `<span class="how">${list(t.pending, p => `${esc(p.id)}: ${badge(p.status, p.kind)}`)}</span>` : ''}
    <span class="how">${esc(t.how)}</span>${prov(t.provenance)}</div>`;
}

route('home', async () => {
  const o = await api('/overview');
  app().innerHTML = `
  <section class="hero"><p class="kicker">gene census · NAADP-binding proteins</p>
    <h1 class="glow">JPT2 and LSM12, counted with their evidence</h1>
    <p class="lead">A read-only dashboard of the committed outputs of <code>naadp_binder_genes</code>: a publication census of
    the two unrelated proteins that bind NAADP, benchmarked against JPT1, the paralog that carries JPT2's signature and does
    not bind it. Every number below is read from a committed table at build time and links to the file and commit it came from.</p>
    <a class="btn" href="#/ledger">Ledger</a><a class="btn alt" href="#/benchmark">S1 benchmark</a><a class="btn alt" href="#/findings">Findings</a></section>
  <div class="callout">Project status: <b>${o.counts.done} of ${o.counts.total}</b> ledger tasks completed,
    ${o.counts.active} in progress, ${o.counts.pending} pending. Next task per the roadmap: <b>${esc(o.next || 'not stated')}</b>.
    Results from pending tasks (census counts, alignments, trees, selection, structures) do not exist yet and are not shown.</div>
  <div class="tiles">${list(o.tiles, tile)}</div>
  <h2>Completed stages</h2>
  ${list(o.stages, s => `<div class="panel"><b>${esc(s.id)}</b> ${badge(s.status, s.kind)}<p class="small">${inline(s.task)}</p>
    <p class="small mute">${inline(s.result)}</p></div>`)}
  <p class="small mute">Headlines above are the ledger's own wording (PUBLICATION_ROADMAP.md, commit ${esc(o.head.short)}).</p>
  <h2>Pages</h2>
  <div class="grid">
    <a class="card" href="#/baseline"><b>S0 database baseline</b><span>Species x symbol grid, the HN1L collision, Pfam scope (D25).</span></a>
    <a class="card" href="#/literature"><b>S0 literature audit</b><span>Each [lit] claim with its verdict and references.</span></a>
    <a class="card" href="#/benchmark"><b>S1 scorer benchmark</b><span>Recall, specificity, the JPT1 decoys and the sister test.</span></a>
    <a class="card" href="#/trees"><b>Trees</b><span>Phylogenies are pending (S7); this page says what exists.</span></a>
    <a class="card" href="#/findings"><b>Findings</b><span>FINDINGS.md with every (pending: task) marker tracked.</span></a>
    <a class="card" href="#/tables"><b>All committed tables</b><span>Browse every TSV/CSV under results/.</span></a>
  </div>`;
});
