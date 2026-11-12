// Ledger: the roadmap's task ledger, analysis block and emergent tasks, statuses verbatim.
import { api, app, esc, list, route } from './core.js';
import { badge, inline, prov } from './ui.js';

const rows = ts => list(ts, t => `<tr><td><b>${esc(t.id)}</b></td><td>${inline(t.task)}</td><td class="mono small">${esc(t.depends)}</td>
  <td>${badge(t.status, t.kind)}</td><td class="small">${inline(t.result || '')}</td></tr>`);

route('ledger', async () => {
  const d = await api('/ledger');
  app().innerHTML = `<p class="kicker">PUBLICATION_ROADMAP.md</p><h1>Task ledger</h1>
  <p class="lead">${d.counts.done} completed · ${d.counts.active} in progress · ${d.counts.pending} pending of ${d.counts.total}.
    Next session per the roadmap: <b>${esc(d.next || 'not stated')}</b>. Status words are the repo's own.</p>
  <section class="panel"><h2>Main ledger</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Task</th><th>Depends</th><th>Status</th><th>Results (headline)</th></tr></thead>
    <tbody>${rows(d.main)}</tbody></table></div>${prov(d.provenance)}</section>
  <section class="panel"><h2>Analysis and synthesis block (S15-S22)</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Task</th><th>Depends</th><th>Status</th><th>Results</th></tr></thead>
    <tbody>${rows(d.analysis)}</tbody></table></div>${prov(d.provenance)}</section>
  <section class="panel"><h2>Emergent tasks</h2><div class="scroll"><table><thead><tr><th>Added</th><th>From</th><th>Task</th><th>Status</th></tr></thead>
    <tbody>${list(d.emergent, e => `<tr><td class="mono small">${esc(e.Added)}</td><td>${esc(e.From)}</td><td class="small">${inline(e.Task)}</td>
      <td class="small">${badge((e.Status || '').split(/\s+—|\s+-\s/)[0], e.kind)}<br>${inline(e.Status)}</td></tr>`)}</tbody></table></div>${prov(d.provenance)}</section>`;
});
