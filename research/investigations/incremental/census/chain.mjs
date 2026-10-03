// Ancestor-chain census: for one edit, how far does a size change propagate up the ancestor chain, where does it stop,
// and how many following siblings does it push at each level. Cheap (rects of the ancestor chain only), so large samples.
// node chain.mjs PAGE.html OUT.json N [SHEET=file ...]
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const PAGE_URL = 'http://snowghost.test/page/index.html';
const [pagePath, outPath, nS, ...maps] = process.argv.slice(2);
const sheets = maps.map((m) => { const at = m.lastIndexOf('='); return { suffix: m.slice(0, at), body: readFileSync(m.slice(at + 1)) }; }).sort((a, b) => b.suffix.length - a.suffix.length);
const pageBody = readFileSync(pagePath);
const here = new URL('.', import.meta.url).pathname;
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true });
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
await page.evaluate(readFileSync(here + 'inpage.js', 'utf8'));
await page.evaluate(() => { __fan.init(); __fan.buildCands(); });
const KINDS = ['text+word', 'text-word', 'text+sentence', 'font-size', 'width', 'insert-block', 'remove-block', 'display-none'];
const N = Number(nS);
const out = [];
for (const kind of KINDS) {
  for (let off = 0; off < N; off += 50) {
    const rs = await page.evaluate(([kind, from, to]) => {
      const { els, parent, tparent, level, makeEdit } = __fan;
      const EPS = __fan.eps();
      const box = (e) => { const l = e.getClientRects(); if (!l.length) return null; let x0 = 1e18, y0 = 1e18, x1 = -1e18, y1 = -1e18; for (const r of l) { x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); } return { x: x0, y: y0, w: x1 - x0, h: y1 - y0, n: l.length }; };
      const res = [];
      for (let k = from; k < to; k++) {
        const ed = makeEdit(kind, 7000 + 13 * k + kind.length);
        // starting element of the chain: parent of the edit site
        let start = ed.ttarget >= 0 ? tparent[ed.ttarget] : (ed.touched >= 0 ? ed.touched : parent[ed.target]);
        const chain = []; for (let a = ed.target >= 0 && ed.touched < 0 ? ed.target : start; a >= 0; a = parent[a]) chain.push(a);
        // for insert/remove: the chain begins at the touched parent (its children change)
        const before = chain.map((a) => box(els[a]));
        // following-sibling counts (block-level siblings with a box) per chain element, in baseline
        const foll = chain.map((a) => { let n = 0; for (let s = els[a].nextElementSibling; s; s = s.nextElementSibling) { const l = s.getClientRects(); if (l.length) n++; } return n; });
        const disp = chain.map((a) => getComputedStyle(els[a]).display);
        const pos = chain.map((a) => { const cs = getComputedStyle(els[a]); return cs.position + '/' + cs.overflowY ; });
        ed.apply();
        const after = chain.map((a) => box(els[a]));
        ed.revert();
        const rec = { descr: ed.descr, len: chain.length, steps: [] };
        for (let i = 0; i < chain.length; i++) {
          const b = before[i], a = after[i];
          if (!b || !a) { rec.steps.push({ d: disp[i], s: 'nobox', f: foll[i] }); continue; }
          const dw = a.w - b.w, dh = a.h - b.h;
          rec.steps.push({ d: disp[i], p: pos[i], dw: Math.abs(dw) > EPS ? dw : 0, dh: Math.abs(dh) > EPS ? dh : 0, dy: a.y - b.y, f: foll[i] });
        }
        res.push(rec);
      }
      return res;
    }, [kind, off, Math.min(N, off + 50)]);
    for (const r of rs) { r.kind = kind; out.push(r); }
  }
  console.error(kind, out.filter((r) => r.kind === kind).length);
  writeFileSync(outPath, JSON.stringify(out));
}
await browser.close();
