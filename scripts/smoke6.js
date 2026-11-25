const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/generativelanguage.googleapis.com/**', r => { const u = r.request().url();
    if (u.includes(':generateContent')) return r.fulfill({ json: { candidates: [{ content: { parts: [{ text: '## Resposta correta\n(A) ok **Gemini**' }] } }] } });
    return r.fulfill({ json: { models: [{ name: 'models/gemini-3-flash', supportedGenerationMethods: ['generateContent'] }] } }); });
  await pg.route('**/fonts.googleapis.com/**', r => r.abort());
  await pg.goto('http://localhost:8765/index.html'); await pg.waitForSelector('.q');
  const c = pg.locator('.q').first(); await c.locator('[data-let="A"]').first().click(); await c.locator('[data-resp]').click();
  await pg.locator('.q').first().locator('[data-act="com"]').click(); await pg.waitForTimeout(1200);
  console.log((await pg.locator('.q').first().locator('.ia').textContent()).slice(0, 80));
  await pg.reload(); await pg.waitForSelector('.q'); console.log('ja respondida apos reload:', await pg.locator('.ja').count());
  console.log('erros', errs); await b.close();
})();
