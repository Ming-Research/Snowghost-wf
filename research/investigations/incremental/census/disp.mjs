import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const PAGE_URL = 'http://snowghost.test/page/index.html';
const dir = 'build/research/concurrency/';
const PAGES = {
  apollo11: ['apollo11.html', [['wikibase.client.init&only=styles&skin=vector-2022', 'apollo11-modules.css'], ['modules=site.styles&only=styles&skin=vector-2022', 'apollo11-site.css']]],
  html5: ['html5.html', []],
  ecma262: ['ecma262.html', [['assets/css/ecmarkup.css', 'ecma262-ecmarkup.css'], ['assets/css/print.css', 'ecma262-print.css']]],
};
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true });
for (const [name, [file, maps]] of Object.entries(PAGES)) {
  const pageBody = readFileSync(dir + file);
  const sheets = maps.map(([s, f]) => ({ suffix: s, body: readFileSync(dir + f) }));
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  await page.route('**/*', (route) => { const url = route.request().url(); if (url === PAGE_URL) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody }); const s = sheets.find((c) => url.endsWith(c.suffix)); if (s) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: s.body }); return route.abort(); });
  await page.goto(PAGE_URL, { waitUntil: 'load' });
  const r = await page.evaluate(() => {
    const c = {}; const add = (k) => { c[k] = (c[k] || 0) + 1; };
    for (const e of document.querySelectorAll('*')) {
      if (!e.getClientRects().length) continue;
      const cs = getComputedStyle(e);
      add('display:' + cs.display);
      if (cs.float !== 'none') add('float');
      if (cs.position !== 'static') add('pos:' + cs.position);
      if (/%/.test(e.style.width || '')) add('inline-style %width');
      if (cs.columnCount !== 'auto' || cs.columnWidth !== 'auto') add('multicol');
    }
    return Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 14);
  });
  console.log(name, JSON.stringify(r));
  await context.close();
}
await browser.close();
