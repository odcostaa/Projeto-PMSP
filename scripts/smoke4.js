const { chromium } = require('playwright'); const fs=require('fs');
(async () => {
  const ids = JSON.parse(fs.readFileSync('/home/claude/work/fb.json'));
  const qs = JSON.parse(fs.readFileSync('/home/claude/site/questoes.json'));
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 760, height: 900 } });
  await pg.addInitScript(() => {
    const store = {}; const subs = []; const notify = () => subs.forEach(s => s());
    window.claude = { use: async (n) => {
      if (n === 'user') return { id: async () => 'u1', canEdit: async () => true, isOwner: () => true };
      if (n === 'db') return { collection: (p) => ({ onSnapshot: (cb) => { const f = () => cb({ docs: Object.keys(store).filter(k => k.startsWith(p + '/')).map(k => ({ id: k.split('/').pop(), exists: true, data: () => store[k] })) }); subs.push(f); setTimeout(f, 0); } }),
        doc: (p) => ({ get: async () => store[p] ? { exists: true, data: () => store[p] } : { exists: false }, set: async (d) => { store[p] = JSON.parse(JSON.stringify(d)); notify(); }, delete: async () => { delete store[p]; notify(); } }) };
      return null; } };
  });
  await pg.route('**/fonts.googleapis.com/**', r => r.abort());
  await pg.goto('http://localhost:8765/index.html'); if (process.env.TH) await pg.evaluate(t => document.documentElement.dataset.theme = t, process.env.TH); await pg.waitForSelector('.q');
  for (const id of ids) { const q = qs.find(x => x.id === id); await pg.fill('#f-busca', q.enunciado.split('\n')[0].slice(0, 60)); await pg.waitForTimeout(350);
    const c = pg.locator(`.q[data-q="${id}"]`); if (await c.count()) await c.first().screenshot({ path: `/home/claude/work/v_${id}.png` }); else console.log('nao achou', id); }
  await b.close();
})();
