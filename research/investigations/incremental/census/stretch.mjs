import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const PAGE_URL = 'http://snowghost.test/page/index.html';
const dir = 'build/research/concurrency/';
const pageBody = readFileSync(dir + 'ecma262.html');
const sheets = [['assets/css/ecmarkup.css', 'ecma262-ecmarkup.css'], ['assets/css/print.css', 'ecma262-print.css']].map(([s, f]) => ({ suffix: s, body: readFileSync(dir + f) }));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true });
const page = await (await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 720 } })).newPage();
await page.route('**/*', (route) => { const url = route.request().url(); if (url === PAGE_URL) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody }); const s = sheets.find((c) => url.endsWith(c.suffix)); if (s) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: s.body }); return route.abort(); });
await page.goto(PAGE_URL, { waitUntil: 'load' });
console.log(JSON.stringify(await page.evaluate(() => {
  const out = [];
  const flex = Array.from(document.querySelectorAll('*')).filter((e) => getComputedStyle(e).display === 'flex' && e.children.length >= 2 && e.getClientRects().length);
  const kinds = {}; for (const e of flex) kinds[e.localName + '.' + e.className.toString().slice(0, 20)] = (kinds[e.localName + '.' + e.className.toString().slice(0, 20)] || 0) + 1;
  out.push(Object.entries(kinds).sort((a, b) => b[1] - a[1]).slice(0, 5));
  let tested = 0, stretched = 0;
  for (const e of flex.slice(0, 400)) {
    const kids = Array.from(e.children).filter((c) => c.getClientRects().length);
    if (kids.length < 2) continue;
    // grow the text of the first descendant text node of kids[0] by 40 words
    const w = document.createTreeWalker(kids[0], NodeFilter.SHOW_TEXT); const t = w.nextNode(); if (!t) continue;
    const before = kids.slice(1).map((k) => k.getBoundingClientRect().height); const h0 = kids[0].getBoundingClientRect().height;
    const old = t.data; t.data = old + ' lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'.repeat(2);
    const after = kids.slice(1).map((k) => k.getBoundingClientRect().height); const h1 = kids[0].getBoundingClientRect().height;
    t.data = old;
    if (h1 > h0 + 1) { tested++; if (after.some((a, i) => Math.abs(a - before[i]) > 1)) stretched++; }
  }
  out.push({ tested, siblingsHeightChangedToo: stretched });
  return out;
})));
await browser.close();
