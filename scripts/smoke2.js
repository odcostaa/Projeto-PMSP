const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1000, height: 900 }, deviceScaleFactor: 1 });
  const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.addInitScript(() => {
    const store = {}; const subs = [];
    const snapDoc = (id, d) => ({ id, exists: true, data: () => d });
    const notify = () => subs.forEach(s => s());
    window.claude = { use: async (n) => {
      if (n === 'user') return { id: async () => 'u1', canEdit: async () => true, isOwner: () => true };
      if (n === 'db') return {
        collection: (path) => ({ onSnapshot: (cb) => { const f = () => cb({ docs: Object.keys(store).filter(k => k.startsWith(path + '/') && k.split('/').length === path.split('/').length + 1).map(k => snapDoc(k.split('/').pop(), store[k])) }); subs.push(f); setTimeout(f, 0); } }),
        doc: (path) => ({ get: async () => store[path] ? { exists: true, data: () => store[path] } : { exists: false }, set: async (d) => { store[path] = JSON.parse(JSON.stringify(d)); notify(); }, delete: async () => { delete store[path]; notify(); } })
      };
      return null; } };
  });
  await pg.route('**/fonts.googleapis.com/**', r => r.abort()); await pg.goto('http://localhost:8765/index.html'); await pg.waitForSelector('.q');
  await pg.selectOption('#pp','50');
  const jobs=[['2026','PMES2601-09'],['2026','PMES2601-33'],['2017','PMES1703-29']];
  for (const [ano,id] of jobs) { await pg.selectOption('#f-ano', ano); await pg.waitForTimeout(400); const c = pg.locator('.q', {hasText: id}); console.log(id, await c.count()); if (await c.count()) await c.first().screenshot({ path: '/home/claude/work/c_' + id + '.png' }); }
  await pg.selectOption('#f-ano',''); await pg.fill('#f-busca','Ironizado na charge'); await pg.waitForTimeout(500); console.log('charge', await pg.locator('.q').count()); if (await pg.locator('.q').count()) await pg.locator('.q').first().screenshot({path:'/home/claude/work/c_PMES1903-43.png'});
  console.log(errs); await b.close(); })();
