// Static-site data layer: every API path is an exported JSON file (scripts/build_static.py). Nothing is computed here.
const files = new Map();
export async function staticApi(path, body) {
  if (body) throw new Error('This dashboard is read-only.');
  const clean = path.split('?')[0].replace(/^\/+|\/+$/g, '');
  if (!files.has(clean)) {
    files.set(clean, fetch('api/' + clean + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${clean}`); return r.json(); }));
  }
  return files.get(clean);
}
