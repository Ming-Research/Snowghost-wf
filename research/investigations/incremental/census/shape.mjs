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
    const q = (a, p) => { const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
    const els = Array.from(document.querySelectorAll('*')).filter((e) => e.getClientRects().length);
    const kids = els.map((e) => Array.from(e.children).filter((c) => c.getClientRects().length).length);
    const depth = els.map((e) => { let d = 0; for (let p = e.parentElement; p; p = p.parentElement) d++; return d; });
    const wide = els.map((e, i) => [e, kids[i]]).filter(([, k]) => k > 100).map(([e, k]) => e.localName + (e.id ? '#' + e.id : '') + ':' + k).slice(0, 8);
    const kidsOfWide = kids.filter((k) => k > 100).reduce((a, b) => a + b, 0);
    return { boxes: els.length, maxKids: kids.reduce((a, b) => Math.max(a, b), 0), kidsP99: q(kids, .99), containersOver100: kids.filter((k) => k > 100).length, boxesUnderContainersOver100: kidsOfWide, depthMedian: q(depth, .5), depthP90: q(depth, .9), depthMax: depth.reduce((a, b) => Math.max(a, b), 0), wide, scrollHeight: document.documentElement.scrollHeight };
  });
  console.log(name, JSON.stringify(r));
  await context.close();
}
await browser.close();
