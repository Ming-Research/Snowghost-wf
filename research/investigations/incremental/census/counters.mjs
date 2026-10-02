// Counter coupling census (static, no layout): how many counter values an insert/remove of one counting element renumbers.
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const PAGE_URL = 'http://snowghost.test/page/index.html';
const dir = 'build/research/concurrency/';
const PAGES = {
  ecma262: ['ecma262.html', [['assets/css/ecmarkup.css', 'ecma262-ecmarkup.css'], ['assets/css/print.css', 'ecma262-print.css']]],
  html5: ['html5.html', []],
  apollo11: ['apollo11.html', [['wikibase.client.init&only=styles&skin=vector-2022', 'apollo11-modules.css'], ['modules=site.styles&only=styles&skin=vector-2022', 'apollo11-site.css']]],
};
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true });
for (const [name, [file, maps]] of Object.entries(PAGES)) {
  const pageBody = readFileSync(dir + file);
  const sheets = maps.map(([s, f]) => ({ suffix: s, body: readFileSync(dir + f) })).sort((a, b) => b.suffix.length - a.suffix.length);
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  await page.route('**/*', (route) => { const url = route.request().url(); if (url === PAGE_URL) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody }); const s = sheets.find((c) => url.endsWith(c.suffix)); if (s) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: s.body }); return route.abort(); });
  await page.goto(PAGE_URL, { waitUntil: 'load' });
  const res = await page.evaluate(() => {
    const q = (a, p) => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
    const els = Array.from(document.querySelectorAll('*'));
    const out = {};
    // implicit list-item counter: ordered markers renumbered by inserting/removing at item k = following list-item siblings
    const foll = []; let items = 0, ordered = 0;
    for (const e of els) {
      const cs = getComputedStyle(e);
      if (cs.display !== 'list-item') continue;
      items++;
      const lst = cs.listStyleType;
      const p = e.parentElement; if (!p || p.localName !== 'ol') continue;
      if (lst === 'none') continue;
      ordered++;
      let n = 0; for (let s = e.nextElementSibling; s; s = s.nextElementSibling) if (getComputedStyle(s).display === 'list-item') n++;
      foll.push(n);
    }
    out.listItems = items; out.orderedMarkers = ordered; out.olFollowingSiblings = [q(foll, .5), q(foll, .9), foll.length ? Math.max(...foll) : 0];
    // author counters: elements with counter-increment (not none): number of later increments of the same counter in scope (approx: same nearest reset ancestor)
    const incr = new Map(); let nIncr = 0, nReset = 0;
    for (const e of els) {
      const cs = getComputedStyle(e);
      if (cs.counterReset !== 'none') nReset++;
      if (cs.counterIncrement === 'none') continue;
      nIncr++;
      const names = cs.counterIncrement.split(/\s+/).filter((x) => isNaN(Number(x)));
      for (const nm of names) { let k = nm; (incr.get(k) || incr.set(k, []).get(k)).push(e); }
    }
    out.counterIncrementElements = nIncr; out.counterResetElements = nReset;
    out.names = {};
    for (const [nm, list] of incr) {
      // scope root: nearest ancestor-or-previous-sibling-ancestor with reset of nm; approximate by nearest ancestor whose computed counter-reset includes nm, else document
      const byRoot = new Map();
      for (const e of list) {
        let r = e.parentElement; while (r && !getComputedStyle(r).counterReset.split(/\s+/).includes(nm)) r = r.parentElement;
        const key = r || document.documentElement; (byRoot.get(key) || byRoot.set(key, []).get(key)).push(e);
      }
      const foll2 = []; for (const l of byRoot.values()) l.forEach((e, i) => foll2.push(l.length - 1 - i));
      out.names[nm] = { elements: list.length, scopes: byRoot.size, followingInScope: [q(foll2, .5), q(foll2, .9), Math.max(...foll2)] };
    }
    return out;
  });
  console.log(name, JSON.stringify(res));
  await context.close();
}
await browser.close();
