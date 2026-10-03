// node run.mjs PAGE.html OUT.json PERKIND [SHEET=...]
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
const CHROMIUM = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const PAGE_URL = 'http://snowghost.test/page/index.html';
const [pagePath, outPath, perKindS, ...maps] = process.argv.slice(2);
const perKind = Number(perKindS);
const kindsFilter = process.env.KINDS ? process.env.KINDS.split(',') : null;
const sheets = maps.map((m) => { const at = m.lastIndexOf('='); return { suffix: m.slice(0, at), body: readFileSync(m.slice(at + 1)) }; }).sort((a, b) => b.suffix.length - a.suffix.length);
const pageBody = readFileSync(pagePath);
const here = new URL('.', import.meta.url).pathname;
const inpage = readFileSync(here + 'inpage.js', 'utf8');
const KINDS = ['text+word', 'text-word', 'text+sentence', 'class+', 'class-', 'color', 'width', 'font-size', 'display-none', 'insert-block', 'remove-block',
  'container-color', 'container-font-size', 'container-width'];
const browser = await chromium.launch({ executablePath: CHROMIUM, headless: true });
const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, colorScheme: 'light', locale: 'en-US' });
const page = await context.newPage();
page.setDefaultTimeout(1800000);
await page.emulateMedia({ media: 'screen', colorScheme: 'light' });
await page.route('**/*', (route) => {
  const url = route.request().url();
  if (url === PAGE_URL) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody });
  const s = sheets.find((c) => url.endsWith(c.suffix));
  if (s) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: s.body });
  return route.abort();
});
await page.goto(PAGE_URL, { waitUntil: 'load' });
await page.evaluate(inpage);
const t0 = Date.now();
const info = await page.evaluate(() => __fan.init());
const cands = await page.evaluate(() => __fan.buildCands());
console.error(pagePath, JSON.stringify(info), JSON.stringify(cands), 'init ms', Date.now() - t0);
const results = [];
const rowsCap = { 'container-color': cands.cont, 'container-font-size': cands.cont, 'container-width': cands.cont };
for (const kind of KINDS) {
  if (kindsFilter && !kindsFilter.includes(kind)) continue;
  const n = kind.startsWith('container') ? Math.max(5, Math.round(perKind / 2)) : perKind;
  for (let k = 0; k < n; k++) {
    const seed = 1000 * (KINDS.indexOf(kind) + 1) + k;
    const s = Date.now();
    const r = await page.evaluate(([kind, seed, verify]) => __fan.runEdit(kind, seed, verify), [kind, seed, k % Number(process.env.VE || 1) === 0]);
    r.wallMs = Date.now() - s;
    results.push(r);
    if (k === 0 || (r.verify && (r.verify.badBoxes||r.verify.badTexts||r.verify.badStyles))) console.error(kind, 'first edit ms', r.wallMs, 'snap', r.snapMs.toFixed(0), JSON.stringify(r.verify), r.descr);
  }
  writeFileSync(outPath, JSON.stringify({ page: pagePath, info, cands, results }));
}
console.error('done', (Date.now() - t0) / 1000, 's');
await browser.close();
