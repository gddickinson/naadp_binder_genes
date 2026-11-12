// About: what this dashboard is, how it gets its numbers, how to run it.
import { api, app, esc, route } from './core.js';

route('about', async () => {
  const i = await api('/info');
  app().innerHTML = `<p class="kicker">about</p><h1>About this dashboard</h1>
  <p class="lead"><code>naadp_binder_genes</code> is a publication-grade census of the NAADP-binding proteins JPT2
    and LSM12, the small accessory proteins that confer NAADP sensitivity on the two-pore channels. The channel half
    is the sibling project <code>naadpr_genes</code>.</p>
  <h2>Two rules the project turns on</h2>
  <p><b>Two unrelated families, never mixed.</b> JPT2 and LSM12 share a ligand and nothing else, so every identity, tree and
    novelty score is computed within a partition (roadmap D14).</p>
  <p><b>The decoy is inside the family.</b> JPT1 carries JPT2's Pfam signature at nearly its size and does not bind NAADP, so a
    domain hit is a family call, never a function call (D21).</p>
  <h2>Where the numbers come from</h2>
  <p>Every value on these pages is read, when the site is built, from a file committed in the repository at git HEAD (the local
    app reads <code>git show HEAD:&lt;path&gt;</code>, so uncommitted edits never appear). Each panel names its file, the last
    commit that changed it and a SHA-256 prefix of the bytes shown, linking to that exact version on GitHub. Where a headline is a
    count of table rows, the filter is printed with it. Nothing is computed or estimated beyond that, and work from tasks that
    are still pending is labelled pending with the ledger's own status words.</p>
  <p class="small mute">This build: commit ${esc(i.head.short)}${i.head.date ? ' (' + esc(i.head.date) + ')' : ''}: ${esc(i.head.subject)}.</p>
  <h2>Run it</h2>
  <pre>pip install -r requirements-web.txt
python run_web.py                     # http://127.0.0.1:8175
python scripts/build_static.py        # static site in site/</pre>
  <p>The desktop search tool and the pipeline: <code>python run.py</code>, and the stage scripts under <code>scripts/</code>
    (see the README and INTERFACE.md).</p>
  <p class="small mute">Code and results by George Dickinson; MIT licence. <a href="${esc(i.repo)}">${esc(i.repo)}</a></p>`;
});
