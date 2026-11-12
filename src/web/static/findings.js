// Findings: FINDINGS.md as committed, with a tracker of every (pending: task) marker against the ledger's statuses.
import { api, app, esc, list, route } from './core.js';
import { badge, prov } from './ui.js';
import { renderMd } from './md.js';

route('findings', async () => {
  const d = await api('/findings');
  const ready = d.markers.filter(m => m.all_done);
  app().innerHTML = `<p class="kicker">FINDINGS.md</p><h1>Findings</h1>
    <p class="lead">The project's plain-language biological story, one dated entry per completed task. Claims that depend on
    unfinished work carry the repo's own <span class="pending mono">(pending: task)</span> marker and are shown as pending here.</p>
    <section class="panel"><h2>Pending markers (${d.markers.length})</h2>
      <p class="small mute">Each marker with the ledger status of every task it names. A marker whose tasks are all completed
      is due to be resolved in FINDINGS.md (${ready.length} today).</p>
      <div class="scroll"><table><thead><tr><th>entry</th><th>marker</th><th>task status</th></tr></thead><tbody>
      ${list(d.markers, m => `<tr><td class="small">${esc(m.entry)} <span class="mute mono">(line ${m.line})</span></td>
        <td class="mono small">${esc(m.marker)}</td><td>${list(m.task_status, t => `${esc(t.id)} ${badge(t.status, t.kind)}`, ' ')}</td></tr>`)}
      </tbody></table></div>${prov(d.provenance)}</section>
    <section class="panel md">${renderMd(d.markdown)}${prov(d.provenance.slice(0, 1))}</section>`;
});
