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
  await pg.route('**/fonts.googleapis.com/**', r => r.abort()); await pg.goto('http://localhost:8765/index.html'); await pg.waitForTimeout(1500); console.log(errs, (await pg.textContent('#lista')).slice(0,200), (await pg.textContent('#aviso')).slice(0,200)); await pg.waitForSelector('.q', {timeout:5000});
  console.log('cartoes', await pg.locator('.q').count(), await pg.textContent('#count'));
  await pg.selectOption('#pp', '50');
  // filtros
  await pg.selectOption('#f-materia', 'Matemática'); console.log('mat', await pg.textContent('#count'));
  await pg.selectOption('#f-ano', '2026'); console.log('mat 2026', await pg.textContent('#count'));
  await pg.screenshot({ path: '/home/claude/work/shot1.png' });
  // tesoura + responder
  const card = pg.locator('.q').first();
  await card.locator('[data-cut="B"]').click();
  console.log('cortada', await pg.locator('.q').first().locator('.alt.cortada').count());
  await pg.locator('.q').first().locator('[data-let="A"]').first().click();
  await pg.locator('.q').first().locator('[data-resp]').click();
  console.log('ja respondida', await pg.locator('.q').first().locator('.ja').count(), await pg.locator('.q').first().locator('.res').textContent());
  await pg.locator('.q').first().screenshot({ path: '/home/claude/work/shot2.png' });
  await pg.selectOption('#f-materia', ''); await pg.selectOption('#f-ano', '2026');
  await pg.fill('#f-busca', 'calulu');
  await pg.waitForTimeout(300);
  await pg.locator('.q').first().screenshot({ path: '/home/claude/work/shot3.png' });
  console.log('erros', errs);
  await b.close();
})();
