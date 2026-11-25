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
  await pg.route('**/generativelanguage.googleapis.com/**', r => { const u = r.request().url();
    if (u.includes(':generateContent')) { calls++; return r.fulfill({ json: { candidates: [{ content: { parts: [{ text: calls === 1 ? '## Resposta correta\n(C) teste\n## Passo a passo\n1. Calcule 1/6 de 24 = 4\n2. Some' : 'Claro! **Outro jeito**: pense em partes.' }] } }] } }); }
    return r.fulfill({ json: { models: [{ name: 'models/gemini-3-flash', supportedGenerationMethods: ['generateContent'] }] } }); });
  await pg.route('**/fonts.googleapis.com/**', r => r.abort());
  await pg.goto('http://localhost:8765/index.html'); await pg.waitForSelector('.q');
  await pg.fill('#f-busca', 'gaveta há 24 canetas'); await pg.waitForTimeout(400);
  const c = pg.locator('.q').first();
  console.log((await c.textContent()).slice(0, 400));
  await c.locator('[data-let="A"]').first().click(); await c.locator('[data-resp]').click();
  await pg.locator('.q').first().locator('[data-act="com"]').click(); await pg.waitForTimeout(800);
  await pg.locator('.q').first().locator('textarea[id^=chat-]').fill('Explique de outro jeito');
  await pg.locator('.q').first().locator('[data-chat]').click(); await pg.waitForTimeout(800);
  console.log('chat msgs', await pg.locator('.cm').count(), 'calls', calls);
  await pg.locator('.q').first().screenshot({ path: '/home/claude/work/s3a.png' });
  for (const [txt, f] of [['charge', 'c'], ['tabela', 't']]) { await pg.fill('#f-busca', txt); await pg.waitForTimeout(400); await pg.locator('.q').first().screenshot({ path: `/home/claude/work/s3${f}.png` }); }
  console.log('erros', errs); await b.close();
})();
