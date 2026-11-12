// Reports: the committed report.md files (each rendered by its stage from committed tables, D13) and the S0 review.
import { api, app, esc, list, route } from './core.js';
import { prov } from './ui.js';
import { renderMd } from './md.js';

route('reports', async () => {
  const d = await api('/reports');
  app().innerHTML = `<p class="kicker">sources</p><h1>Rendered reports</h1>
    <p class="lead">Each stage renders its report purely from its committed tables (roadmap decision D13). Shown here as committed.</p>
    <div class="grid wide">${list(d.reports, r => `<a class="card" href="#/report/${r.path.split('/').map(encodeURIComponent).join('/')}">
      <b>${esc(r.path.split('/').slice(-2).join('/'))}</b><small>${esc(r.path)}</small>
      <span class="mono small">commit ${esc(r.provenance.commit)} · ${esc(r.provenance.date || '')}</span></a>`)}</div>`;
});

route('report', async args => {
  const path = args.join('/');
  const d = await api('/report/' + path);
  const base = path.split('/').slice(0, -1).join('/');
  app().innerHTML = `<p><a href="#/reports">&larr; all reports</a></p>${prov(d.provenance)}
    <article class="panel md">${renderMd(d.markdown, base)}</article>`;
});
