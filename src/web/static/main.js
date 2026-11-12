// Entry: registers the lazy page modules and starts the router. Every page reads committed outputs through api().
import { $, api, isStatic, lazy, start } from './core.js';

lazy({
  home: () => import('./home.js'), ledger: () => import('./ledger.js'), baseline: () => import('./baseline.js'),
  literature: () => import('./literature.js'), benchmark: () => import('./benchmark.js'),
  findings: () => import('./findings.js'), trees: () => import('./trees.js'), reports: () => import('./reports.js'),
  report: () => import('./reports.js'), tables: () => import('./tables.js'), table: () => import('./tables.js'),
  about: () => import('./about.js'),
});
$('#mode').textContent = isStatic() ? 'static site (snapshot of the committed outputs)' : 'local app (reads git HEAD)';
api('/info').then(i => { $('#headref').textContent = `built from ${i.head.short}${i.head.date ? ' (' + i.head.date + ')' : ''}`; })
  .catch(() => {});
start();
