// S1 scorer benchmark: run metrics, every record's score per run, bait margins, distortion, identity and the tables.
import { $, api, app, esc, list, route } from './core.js';
import { colourKey, dotChart, legend } from './chart.js';
import { objTable, panelHtml, tableHtml, wireTables, wireTips } from './ui.js';

const frac = (h, n) => (h == null || n == null) ? '-' : `${h}/${n}`;
const GROUP_LEGEND = [['JPT2 (positive)', 'JPT2'], ['LSM12 (positive)', 'LSM12'], ['deep grade (positive)', 'deep'],
  ['JPT1 sister paralog (decoy)', 'JPT1', true], ['other decoys', 'other', true]];

function runsTable(p) {
  return `<p class="small">Panel: ${esc(p.panel_sizes.positive)} positive + ${esc(p.panel_sizes.decoy)} decoy records over
    ${esc(p.panel_sizes.unique)} unique accessions · promotion threshold ${esc(p.threshold)} · size band ${esc((p.size_band || []).join('-'))} aa.</p>
    <div class="scroll"><table><thead><tr><th>run</th><th>arrangement</th><th>recall</th><th>protected</th><th>specificity</th><th>JPT1 decoys held back</th></tr></thead>
    <tbody>${list(p.runs, r => `<tr><td class="mono small">${esc(r.run)}</td><td class="small">${esc(r.note)}</td>
      <td>${frac(r.recall_hit, r.recall_n)}</td><td>${esc(r.recall_protected ?? '-')}</td><td>${frac(r.specificity_hit, r.specificity_n)}</td>
      <td class="${r.jpt1_pass === 0 ? 'err' : ''}">${frac(r.jpt1_pass, r.jpt1_n)}</td></tr>`)}</tbody></table></div>`;
}

function scoresChart(p, part) {
  const rows = p.rows.filter(r => r.partition === part && r.score !== 'n/a' && r.score !== '');
  const runs = [...new Set(rows.map(r => r.run))];
  return dotChart({
    rows: rows.map(r => ({ y: r.run, x: +r.score, key: colourKey(r.group), hollow: r.panel_kind === 'decoy',
      tip: `<b>${esc(r.gene_symbol || r.accession)}</b> ${esc(r.accession)}<br>${esc(r.species)} · ${esc(r.length_aa)} aa<br>` +
        `${esc(r.group)} (${esc(r.panel_kind)})<br>score ${esc(r.score)} · promoted ${esc(r.promoted)}` +
        (r.sister_margin ? `<br>sister margin ${esc(r.sister_margin)}` : '') })),
    yOrder: runs, dom: [0, 100], threshold: p.threshold, xLabel: `discovery score (${part} partition)` });
}

function marginChart(p, covered) {
  const k = covered ? 'margin_cov' : 'margin';
  const rows = p.rows.filter(r => r.truth !== 'bait');
  const xs = rows.map(r => parseFloat(r[k])).filter(Number.isFinite);
  const lim = Math.max(0.1, ...xs.map(Math.abs));
  return dotChart({
    rows: rows.map(r => ({ y: r.run, x: parseFloat(r[k]), key: colourKey(r.truth), hollow: r.truth === 'JPT1',
      tip: `<b>${esc(r.gene_symbol)}</b> ${esc(r.accession)}<br>${esc(r.species)} · truth ${esc(r.truth)}<br>` +
        `${esc(k)} ${esc(r[k])} -> call ${esc(covered ? r.call_cov : r.call)}${(covered ? r.correct_cov : r.correct) ? ' (correct: ' + esc(covered ? r.correct_cov : r.correct) + ')' : ''}` })),
    yOrder: [...new Set(rows.map(r => r.run))], dom: [-lim, lim], threshold: 0, thrLabel: 'equidistant (0)',
    xLabel: covered ? 'margin, covered-columns identity (JPT2 bait minus JPT1 bait)' : 'margin, full-alignment identity (JPT2 bait minus JPT1 bait)' });
}

route('benchmark', async () => {
  const d = await api('/benchmark');
  const P = Object.fromEntries(d.panels.map(p => [p.id, p]));
  const rest = d.panels.filter(p => p.table);
  const root = app();
  root.innerHTML = `<p class="kicker">S1 · completed</p><h1>Scorer benchmark</h1>
    <p class="lead">The discovery scorer, run per partition against ${esc(P.runs.panel_sizes.positive)} true members and ${esc(P.runs.panel_sizes.decoy)} decoys led by JPT1, the paralog
    with JPT2's exact signature that does not bind NAADP. Every value is from <code>results/benchmark_controls/</code>.</p>
    ${panelHtml(P.runs, runsTable(P.runs))}
    ${panelHtml(P.scores, `<div class="seg" role="group" aria-label="Partition">${list(['JPT', 'LSM12', 'JOINT'], (x, i) =>
      `<button type="button" data-part="${x}" class="${i ? '' : 'on'}">${x}</button>`)}</div>
      ${legend(GROUP_LEGEND)}<div id="sc">${scoresChart(P.scores, 'JPT')}</div>
      <details class="raw"><summary>table view</summary>${tableHtml(objTable(P.scores.rows))}</details>`)}
    ${panelHtml(P.margin, `<div class="seg" role="group" aria-label="Identity metric"><button type="button" class="on" data-cov="0">full alignment</button>
      <button type="button" data-cov="1">covered columns</button></div>
      ${legend([['JPT2 ortholog', 'JPT2'], ['JPT1 (decoy)', 'JPT1', true], ['other (truth = other)', 'other']])}
      <div id="mc">${marginChart(P.margin, false)}</div>
      <details class="raw"><summary>table view</summary>${tableHtml(objTable(P.margin.rows))}</details>`)}
    ${panelHtml(P.distortion, tableHtml(objTable(P.distortion.rows.map(r => ({ ...r, flipped: (r.flipped || []).join(', ') }))), { filter: false }))}
    ${panelHtml(P.identity, tableHtml(objTable(P.identity.rows), { filter: false }))}
    ${list(rest, p => panelHtml(p, tableHtml(p.table)))}
    ${panelHtml(P.figure, list(P.figure.figures, f => `<img class="fig" src="api/file/${esc(f)}" alt="Figure S1 scorer validation, as committed at ${esc(f)}" loading="lazy">`))}`;
  const rewire = host => { wireTips(host); };
  root.querySelectorAll('[data-part]').forEach(b => b.addEventListener('click', () => {
    root.querySelectorAll('[data-part]').forEach(x => x.classList.toggle('on', x === b));
    $('#sc').innerHTML = scoresChart(P.scores, b.dataset.part); rewire($('#sc'));
  }));
  root.querySelectorAll('[data-cov]').forEach(b => b.addEventListener('click', () => {
    root.querySelectorAll('[data-cov]').forEach(x => x.classList.toggle('on', x === b));
    $('#mc').innerHTML = marginChart(P.margin, b.dataset.cov === '1'); rewire($('#mc'));
  }));
  wireTables(root); wireTips(root);
});
