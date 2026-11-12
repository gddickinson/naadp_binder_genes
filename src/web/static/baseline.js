// S0 database baseline: the species x symbol grid plus every S0 snapshot table, each with its provenance.
import { api, app, esc, list, route } from './core.js';
import { panelHtml, tableHtml, wireTables, wireTips } from './ui.js';

function grid(p) {
  const cell = (sp, sy) => {
    const c = p.grid[`${sp}|${sy}`];
    if (!c) return '<td class="mute">not queried</td>';
    const found = c.result === 'found';
    const tip = esc(`${c.accession || '-'} · ${c.length_aa || '-'} aa · ${c.status || ''} · Pfam ${c.pfam || 'none'}` +
      `<br>organism_id gives: ${c.organism_id_result}${c.screen_note ? '<br>' + c.screen_note : ''}`);
    return `<td class="${found ? 'found' : 'miss'}" tabindex="0" data-tip="${tip}">${esc(c.result)}
      <small>${esc(c.accession || '')}${c.length_aa ? ' · ' + esc(c.length_aa) + ' aa' : ''}</small>
      ${c.field_changes_call === 'True' ? '<small class="ok">field changes call (D23)</small>' : ''}</td>`;
  };
  return `<div class="scroll"><table class="grid-sym"><thead><tr><th>species</th>${list(p.symbols, s => `<th>${esc(s)}</th>`)}</tr></thead>
    <tbody>${list(p.species, sp => `<tr><th scope="row">${esc(sp)}</th>${list(p.symbols, sy => cell(sp, sy))}</tr>`)}</tbody></table></div>`;
}

route('baseline', async () => {
  const d = await api('/baseline');
  const root = app();
  root.innerHTML = `<p class="kicker">S0 · completed</p><h1>Database baseline</h1>
    <p class="lead">Every [db] number in the background document, re-derived live at S0 and committed under
    <code>results/s0_baseline/</code>. Hover or focus a grid cell for the record's details.</p>
    ${list(d.panels, p => panelHtml(p, p.grid ? grid(p) : tableHtml(p.table)))}`;
  wireTables(root); wireTips(root);
});
