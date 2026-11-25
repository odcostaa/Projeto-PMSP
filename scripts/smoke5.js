const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 900, height: 1000 } });
  const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.addInitScript(() => {
    const store = {}; const subs = []; const notify = () => subs.forEach(s => s());
    window.claude = { use: async (n) => {
      if (n === 'user') return { id: async () => 'u1', canEdit: async () => true, isOwner: () => true };
      if (n === 'db') return { collection: (p) => ({ onSnapshot: (cb) => { const f = () => cb({ docs: Object.keys(store).filter(k => k.startsWith(p + '/')).map(k => ({ id: k.split('/').pop(), exists: true, data: () => store[k] })) }); subs.push(f); setTimeout(f, 0); } }),
        doc: (p) => ({ get: async () => store[p] ? { exists: true, data: () => store[p] } : { exists: false }, set: async (d) => { store[p] = JSON.parse(JSON.stringify(d)); notify(); }, delete: async () => { delete store[p]; notify(); } }) };
      return null; } };
  });
  let calls = 0;
  await pg.route('**/generativelanguage.googleapis.com/**', r => r.abort()); await pg.route('**/aiplatform.googleapis.com/**', r => r.abort());
  await pg.route('**/fonts.googleapis.com/**', r => r.abort());
  await pg.goto('http://localhost:8765/index.html'); await pg.waitForSelector('.q');
  await pg.fill('#f-busca', 'gaveta há 24 canetas'); await pg.waitForTimeout(400);
  const c = pg.locator('.q').first();
  await c.locator('[data-let="A"]').first().click(); await c.locator('[data-resp]').click();
  await pg.locator('.q').first().locator('[data-act="com"]').click(); await pg.waitForTimeout(1500);
  await pg.locator('.q').first().locator('[data-diag]').click(); await pg.waitForTimeout(2500);
  console.log((await pg.locator('.q').first().locator('.rel').textContent()).slice(0,1800));
  await pg.click('#tab-d'); await pg.waitForTimeout(300);
  console.log('antes', (await pg.locator('#stats .big').first().textContent()));
  await pg.click('[data-rs=ask]'); await pg.click('[data-rs=go]'); await pg.waitForTimeout(800);
  console.log(await pg.locator('#rs-msg').textContent());
  await pg.click('#tab-q'); await pg.waitForTimeout(300);
  console.log('ja respondida?', await pg.locator('.ja').count());
  console.log('erros', errs); await b.close();
})();
