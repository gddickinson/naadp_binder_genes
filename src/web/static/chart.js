// Inline-SVG dot chart (one row per category, one dot per record), used for scores and bait margins.
// Identity colours follow the repo's figure palette (scripts/figstyle.py PARALOG), validated for the dark surface.
import { esc } from './core.js';

export const COLORS = { JPT2: 'var(--jpt2)', LSM12: 'var(--lsm12)', JPT1: 'var(--jpt1)', deep: 'var(--deep)', other: 'var(--other)' };

// Map a scores.tsv / bait_margin.tsv group or truth label onto a colour key.
export function colourKey(g) {
  g = String(g || '');
  if (g.startsWith('JPT1')) return 'JPT1';
  if (g === 'JPT2' || g === 'bait') return 'JPT2';
  if (g === 'LSM12') return 'LSM12';
  if (g === 'deep_grade') return 'deep';
  return 'other';
}

export function legend(items) {
  return `<div class="legend">${items.map(([label, key, hollow]) =>
    `<span><i class="${hollow ? 'hollow' : ''}" style="background:${COLORS[key]};border-color:${COLORS[key]}"></i>${esc(label)}</span>`).join('')}</div>`;
}

// rows: [{y, x, key, hollow, tip}] ; yOrder: category order ; dom: [min, max] ; threshold: optional x line.
export function dotChart({ rows, yOrder, dom, threshold = null, thrLabel = null, xLabel = '', yLabels = {} }) {
  const W = 760, left = 190, right = 20, top = 26, rowH = 34, H = top + rowH * yOrder.length + 40;
  const sx = v => left + (v - dom[0]) / (dom[1] - dom[0]) * (W - left - right);
  const ticks = [];
  const step = niceStep(dom[1] - dom[0]);
  for (let t = Math.ceil(dom[0] / step) * step; t <= dom[1] + 1e-9; t += step) ticks.push(+t.toFixed(6));
  const yi = Object.fromEntries(yOrder.map((y, i) => [y, i]));
  const seen = {};
  const dots = rows.filter(r => r.y in yi && Number.isFinite(r.x)).map(r => {
    const k = r.y + '|' + r.x; const n = (seen[k] = (seen[k] || 0) + 1) - 1;
    const cy = top + yi[r.y] * rowH + rowH / 2 + ((n % 5) - 2) * 5;  // stack ties so every record stays visible
    const c = COLORS[r.key] || COLORS.other;
    return `<circle class="dot" tabindex="0" cx="${sx(r.x).toFixed(1)}" cy="${cy}" r="5" fill="${r.hollow ? 'var(--panel)' : c}"
      stroke="${c}" stroke-width="${r.hollow ? 2 : 1}" data-tip="${esc(r.tip)}" aria-label="${esc(r.tip.replace(/<br>/g, ' · '))}"></circle>`;
  }).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(xLabel)} by ${esc(yOrder.join(', '))}">
    ${ticks.map(t => `<line class="grid" x1="${sx(t)}" x2="${sx(t)}" y1="${top}" y2="${H - 30}"/>
      <text x="${sx(t)}" y="${H - 16}" text-anchor="middle">${t}</text>`).join('')}
    ${yOrder.map((y, i) => `<text x="${left - 10}" y="${top + i * rowH + rowH / 2 + 4}" text-anchor="end">${esc(yLabels[y] || y)}</text>`).join('')}
    ${threshold != null ? `<line class="thr" x1="${sx(threshold)}" x2="${sx(threshold)}" y1="${top}" y2="${H - 30}"/>
      <text x="${sx(threshold) + 4}" y="${top - 10}" style="fill:var(--warn)">${esc(thrLabel ?? `threshold ${threshold}`)}</text>` : ''}
    ${dots}<text x="${(left + W - right) / 2}" y="${H - 2}" text-anchor="middle">${esc(xLabel)}</text></svg>`;
}

function niceStep(span) {
  const raw = span / 8, p = 10 ** Math.floor(Math.log10(raw)), m = raw / p;
  return (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * p;
}
