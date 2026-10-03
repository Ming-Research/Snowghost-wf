// node layers.mjs apollo11 : list Chromium's own layers with reasons and owner nodes, at several scroll offsets
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const dir = '/home/user/snowghost/build/research/concurrency/';
const pn = process.argv[2];
const SH = { apollo11: [['wikibase.client.init&only=styles&skin=vector-2022', 'apollo11-modules.css'], ['modules=site.styles&only=styles&skin=vector-2022', 'apollo11-site.css']] }[pn];
const body = readFileSync(dir + pn + '.html');
const sheets = SH.map(([s, f]) => ({ suffix: s, body: readFileSync(dir + f) }));
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true });
const ctx = await b.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 720 } });
const page = await ctx.newPage();
await page.route('**/*', (route) => { const u = route.request().url(); if (u === 'http://snowghost.test/page/index.html') return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body }); const s = sheets.find((c) => u.endsWith(c.suffix)); if (s) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: s.body }); return route.abort(); });
await page.goto('http://snowghost.test/page/index.html', { waitUntil: 'load' });
await new Promise((r) => setTimeout(r, 1500));
const cdp = await ctx.newCDPSession(page);
let layers = null;
cdp.on('LayerTree.layerTreeDidChange', (e) => { if (e.layers) layers = e.layers; });
await cdp.send('DOM.enable'); await cdp.send('LayerTree.enable');
for (const y of [0, 720, 3600, 14400]) {
  await page.evaluate((y) => scrollTo({ top: y, behavior: 'instant' }), y);
  layers = null; await new Promise((r) => setTimeout(r, 800));
  await page.evaluate(() => { scrollBy(0, 1); scrollBy(0, -1); }); await new Promise((r) => setTimeout(r, 500));
  console.log('--- scrollY', y, 'layers', layers && layers.length);
  for (const l of layers || []) {
    let rs = []; try { rs = (await cdp.send('LayerTree.compositingReasons', { layerId: l.layerId })).compositingReasons; } catch (e) {}
    let nd = ''; if (l.backendNodeId) try { const d = (await cdp.send('DOM.describeNode', { backendNodeId: l.backendNodeId })).node; nd = d.localName + (d.attributes ? ' ' + d.attributes.filter((_, i, a) => i % 2 === 0 && /^(id|class)$/.test(a[i])).map((n) => n + '=' + d.attributes[d.attributes.indexOf(n) + 1]).join(' ').slice(0, 60) : ''); } catch (e) {}
    console.log(l.layerId, l.width + 'x' + l.height, 'draws', !!l.drawsContent, nd, '|', rs.join('; '));
  }
}
await b.close();
