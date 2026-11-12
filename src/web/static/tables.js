// Table browser: every TSV/CSV committed under results/, each with row/column counts and provenance.
import { api, app, esc, list, route } from './core.js';
import { prov, tableHtml, wireTables } from './ui.js';

route('tables', async () => {
  const d = await api('/tables');
  app().innerHTML = `<p class="kicker">sources</p><h1>All committed tables</h1>
    <p class="lead">${d.tables.length} tables under <code>results/</code> at this commit. Open one to browse, sort and filter it.</p>
    <div class="scroll"><table><thead><tr><th>table</th><th>rows</th><th>cols</th><th>commit</th></tr></thead><tbody>
    ${list(d.tables, t => `<tr><td><a href="#/table/${t.path.split('/').map(encodeURIComponent).join('/')}">${esc(t.path)}</a></td>
      <td>${t.rows}</td><td>${t.columns}</td><td class="mono small">${esc(t.provenance.commit)} · ${esc(t.provenance.date || '')}</td></tr>`)}
    </tbody></table></div>`;
});

route('table', async args => {
  const path = args.join('/');
  const d = await api('/table/' + path);
  const root = app();
  root.innerHTML = `<p><a href="#/tables">&larr; all tables</a></p><h1 class="mono" style="font-size:20px">${esc(path)}</h1>
    ${prov(d.provenance)}${tableHtml(d.table)}`;
  wireTables(root);
});
