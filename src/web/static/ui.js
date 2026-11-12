// Shared dashboard pieces: provenance footer, status badges, sortable/filterable tables, hover tooltip.
import { esc, list } from './core.js';

// Provenance: which committed file (and which commit) a panel's values come from.
export function prov(items) {
  if (!items || !items.length) return '';
  return `<div class="prov">source: ${list(items, p => `<span><a href="${esc(p.url || '#/tables')}" ${p.url ? 'target="_blank" rel="noopener"' : ''}>${esc(p.path)}</a>
    @ ${esc(p.commit || '?')}${p.date ? ' · ' + esc(p.date) : ''} · sha256 ${esc((p.sha256 || '').slice(0, 10))}</span>`)}</div>`;
}

// The repo's own status words, shown verbatim; `kind` only picks the colour.
export function badge(status, kind) {
  const word = String(status || '').replace(/[*`]/g, '');
  return `<span class="badge ${esc(kind || 'pending')}">${esc(word || 'pending')}</span>`;
}

// Minimal inline markdown for ledger cells and notes (bold, code, italics, links).
export function inline(s) {
  return esc(s).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/(^|[\s(])\*([^*\s][^*]*)\*/g, '$1<i>$2</i>')
    .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

export function panelHtml(p, body) {
  return `<section class="panel" id="p-${esc(p.id)}"><h2>${esc(p.title)}</h2>
    ${p.note ? `<p class="small mute">${esc(p.note)}</p>` : ''}${body}${prov(p.provenance)}</section>`;
}

// A table {columns, rows, n_rows, truncated} rendered with a filter box and click-to-sort headers.
let tblId = 0;
export function tableHtml(t, { filter = true } = {}) {
  const id = 'tb' + (++tblId);
  const note = t.truncated ? `<span class="small mute">showing ${t.rows.length} of ${t.n_rows} rows</span>`
    : `<span class="small mute">${t.n_rows} rows</span>`;
  return `<div class="tbl-tools" data-for="${id}">${filter && t.n_rows > 8 ? `<label class="small" style="margin:0">
    <span class="sr">Filter rows</span><input type="search" placeholder="filter rows" aria-label="Filter rows"></label>` : ''}${note}</div>
    <div class="tbl" id="${id}"><table><thead><tr>${list(t.columns, c => `<th scope="col" tabindex="0">${esc(c)}</th>`)}</tr></thead>
    <tbody>${list(t.rows, r => `<tr>${list(r, c => `<td${String(c).length > 80 ? ' class="long"' : ''}>${esc(c)}</td>`)}</tr>`)}</tbody></table></div>`;
}

// Wire every rendered table under root: filtering and numeric-aware sorting.
export function wireTables(root) {
  root.querySelectorAll('.tbl-tools').forEach(tools => {
    const box = root.querySelector('#' + tools.dataset.for);
    const input = tools.querySelector('input');
    if (input) input.addEventListener('input', () => {
      const q = input.value.toLowerCase();
      box.querySelectorAll('tbody tr').forEach(tr => { tr.hidden = q && !tr.textContent.toLowerCase().includes(q); });
    });
    box.querySelectorAll('th').forEach((th, i) => {
      const sort = () => {
        const tb = box.querySelector('tbody'), dir = th.dataset.dir === 'asc' ? -1 : 1;
        th.dataset.dir = dir === 1 ? 'asc' : 'desc';
        const rows = [...tb.rows];
        const key = r => r.cells[i]?.textContent ?? '';
        rows.sort((a, b) => {
          const x = key(a), y = key(b), nx = parseFloat(x), ny = parseFloat(y);
          return dir * (!isNaN(nx) && !isNaN(ny) ? nx - ny : x.localeCompare(y));
        });
        rows.forEach(r => tb.appendChild(r));
      };
      th.addEventListener('click', sort);
      th.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); sort(); } });
    });
  });
}

// Rows as objects -> table structure.
export function objTable(rows, cols) {
  cols = cols || (rows[0] ? Object.keys(rows[0]) : []);
  return { columns: cols, rows: rows.map(r => cols.map(c => r[c] ?? '')), n_rows: rows.length, truncated: false };
}

// One floating tooltip for every chart: elements with data-tip show it on hover and keyboard focus.
let tip;
export function wireTips(root) {
  if (!tip) { tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; document.body.appendChild(tip); }
  const show = (el, x, y) => { tip.innerHTML = el.dataset.tip; tip.hidden = false;
    tip.style.left = Math.min(x + 14, innerWidth - 330) + 'px'; tip.style.top = (y + 14) + 'px'; };
  root.querySelectorAll('[data-tip]').forEach(el => {
    el.addEventListener('mousemove', e => show(el, e.clientX, e.clientY));
    el.addEventListener('mouseleave', () => { tip.hidden = true; });
    el.addEventListener('focus', () => { const b = el.getBoundingClientRect(); show(el, b.right, b.bottom); });
    el.addEventListener('blur', () => { tip.hidden = true; });
  });
}
