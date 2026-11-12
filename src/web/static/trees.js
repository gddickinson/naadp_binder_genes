// Trees: lists any committed phylogeny. None exists yet; the page says which ledger tasks will produce them.
import { api, app, esc, list, route } from './core.js';
import { badge, inline, prov } from './ui.js';

route('trees', async () => {
  const d = await api('/trees');
  app().innerHTML = `<p class="kicker">phylogeny</p><h1>Trees</h1>
    ${d.trees.length ? `<section class="panel"><h2>Committed tree files</h2>${list(d.trees, t => `<p class="mono">${esc(t.path)}</p>${prov([t.provenance])}`)}</section>`
      : `<div class="callout"><b>Pending.</b> No tree file is committed at ${esc(d.head.short)} (searched every committed path ending
        ${esc(d.extensions.join(', '))}). The ML phylogenies are ledger task S7, two trees, one per partition and never a joint one.
        Nothing on this site draws a tree from uncommitted or unfinished work.</div>`}
    <section class="panel"><h2>Tasks that produce the trees</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Task</th><th>Depends</th><th>Status</th></tr></thead>
      <tbody>${list(d.rows, t => `<tr><td><b>${esc(t.id)}</b></td><td class="small">${inline(t.task)}</td><td class="mono small">${esc(t.depends)}</td>
        <td>${badge(t.status, t.kind)}</td></tr>`)}</tbody></table></div>${prov(d.provenance)}</section>`;
});
