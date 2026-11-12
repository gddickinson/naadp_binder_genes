// Small markdown renderer for the committed .md files (FINDINGS.md, rendered reports). Headings, paragraphs, lists,
// pipe tables, block quotes, fenced code, images and inline marks. '(pending: ...)' markers are highlighted.
// Relative images resolve to committed figures served at api/file/<dir>/<img>; others are left as text links.
import { esc } from './core.js';

function inl(s, base) {
  let h = esc(s);
  h = h.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (m, alt, src) => img(alt, src, base));
  h = h.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  h = h.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<span class="mono" title="$2">$1</span>');
  h = h.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/(^|[\s(>])[*_]([^*_\s][^*_]*?)[*_](?=[\s).,;:]|$)/g, '$1<i>$2</i>');
  return h.replace(/\(pending:[^)]*\)/g, m => `<span class="pending">${m}</span>`);
}

function img(alt, src, base) {
  if (/^https?:/.test(src) || !base || !src.endsWith('.png')) return `<span class="mono">[figure: ${alt}]</span>`;
  const parts = (base + '/' + src).split('/'), out = [];
  for (const p of parts) { if (p === '..') out.pop(); else if (p && p !== '.') out.push(p); }
  return `<img src="api/file/${out.join('/')}" alt="${alt}" loading="lazy">`;
}

const cells = l => l.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());

export function renderMd(text, base = '') {
  const lines = text.split('\n'), out = [];
  let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (/^```/.test(l)) {
      const buf = []; i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      out.push(`<pre>${esc(buf.join('\n'))}</pre>`); i++; continue;
    }
    const h = l.match(/^(#{1,6})\s+(.*)/);
    if (h) { const n = Math.min(h[1].length + 1, 4); out.push(`<h${n}>${inl(h[2], base)}</h${n}>`); i++; continue; }
    if (/^\s*(---|\*\*\*)\s*$/.test(l)) { out.push('<hr>'); i++; continue; }
    if (/^\s*\|/.test(l) && /^\s*\|?\s*:?-{3,}/.test(lines[i + 1] || '')) {
      const head = cells(l); i += 2; const rows = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(cells(lines[i++]));
      out.push(`<div class="scroll"><table><thead><tr>${head.map(c => `<th>${inl(c, base)}</th>`).join('')}</tr></thead><tbody>${
        rows.map(r => `<tr>${r.map(c => `<td>${inl(c, base)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`);
      continue;
    }
    if (/^>\s?/.test(l)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ''));
      out.push(`<blockquote>${renderMd(buf.join('\n'), base)}</blockquote>`); continue;
    }
    if (/^\s*([-*+]|\d+\.)\s+/.test(l)) {
      const ordered = /^\s*\d+\./.test(l), items = [];
      while (i < lines.length && (/^\s*([-*+]|\d+\.)\s+/.test(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length))) {
        if (/^\s*([-*+]|\d+\.)\s+/.test(lines[i])) items.push(lines[i].replace(/^\s*([-*+]|\d+\.)\s+/, ''));
        else items[items.length - 1] += ' ' + lines[i].trim();
        i++;
      }
      const tag = ordered ? 'ol' : 'ul';
      out.push(`<${tag}>${items.map(t => `<li>${inl(t, base)}</li>`).join('')}</${tag}>`); continue;
    }
    if (!l.trim()) { i++; continue; }
    const buf = [];
    while (i < lines.length && lines[i].trim() && !/^(#{1,6}\s|```|>|\s*\||\s*([-*+]|\d+\.)\s+)/.test(lines[i])) buf.push(lines[i++]);
    if (!buf.length) buf.push(lines[i++]);
    out.push(`<p>${inl(buf.join(' '), base)}</p>`);
  }
  return out.join('\n');
}
