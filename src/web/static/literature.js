// S0 literature audit: each [lit] claim with verdict, evidence and its references.
import { api, app, esc, list, route } from './core.js';
import { panelHtml, prov } from './ui.js';

route('literature', async () => {
  const d = await api('/literature');
  const [claims, refs] = d.panels;
  const byPmid = Object.fromEntries(refs.references.map(r => [r.pmid, r]));
  const v = d.meta.verdicts || {};
  app().innerHTML = `<p class="kicker">S0 · completed</p><h1>Literature audit</h1>
    <p class="lead">${esc(d.meta.n_claims)} claims audited against ${esc(d.meta.n_references)} references. Verdicts:
    ${list(Object.entries(v), ([k, n]) => `<span class="tag a">${esc(k)} ${esc(n)}</span>`)}</p>${prov(d.meta_provenance)}
    ${panelHtml(claims, list(claims.claims, c => `<div class="panel"><b>${esc(c.claim_id)}</b> <span class="tag b">${esc(c.verdict)}</span>
      <span class="small mute">${esc(c.section)}</span><p>${esc(c.claim)}</p><p class="small mute">${esc(c.evidence)}</p>
      ${c.action ? `<p class="small"><b>Action:</b> ${esc(c.action)}</p>` : ''}
      <p class="small">${list((c.pmids || '').split(';').filter(Boolean), p => byPmid[p]
        ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${esc(p)}/" target="_blank" rel="noopener">PMID ${esc(p)}</a> (${esc(byPmid[p].year)})`
        : `PMID ${esc(p)}`, ' · ')}</p></div>`))}
    ${panelHtml(refs, `<div class="scroll"><table><thead><tr><th>Year</th><th>Reference</th><th>Cited for</th></tr></thead><tbody>
      ${list(refs.references, r => `<tr><td>${esc(r.year)}</td><td><b>${esc(r.title)}</b><br><span class="small mute">${esc(r.authors)}
        <i>${esc(r.journal)}</i> · <a href="https://pubmed.ncbi.nlm.nih.gov/${esc(r.pmid)}/" target="_blank" rel="noopener">PMID ${esc(r.pmid)}</a>
        ${r.doi ? ` · <a href="https://doi.org/${esc(r.doi)}" target="_blank" rel="noopener">doi</a>` : ''}</span></td>
        <td class="mono small">${esc(r.cited_for_claims)}</td></tr>`)}</tbody></table></div>`)}`;
});
