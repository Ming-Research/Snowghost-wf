// node measure.mjs OUTDIR name=URL ...   (name=local:ecma262|html5|apollo11 for the local pages)
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const here = new URL('.', import.meta.url).pathname;
const inpage = readFileSync(here + 'inpage.js', 'utf8');
const LOCAL = '/home/user/snowghost/build/research/concurrency/';
const SHEETS = {
  ecma262: [['assets/css/ecmarkup.css', 'ecma262-ecmarkup.css'], ['assets/css/print.css', 'ecma262-print.css']],
  html5: [],
  apollo11: [['wikibase.client.init&only=styles&skin=vector-2022', 'apollo11-modules.css'], ['modules=site.styles&only=styles&skin=vector-2022', 'apollo11-site.css']],
};
const STEP_CAP = Number(process.env.STEP_CAP || 30);
const [outDir, ...sites] = process.argv.slice(2);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true });

function interleaveA(snap, rects, frames, H) {
  // snap: DOMSnapshot; rects[k] = doc rects of roots at frame k (k=0 is scroll 0); frames[k].y scroll offsets
  const S = snap.strings;
  const nodes = snap.documents[0].nodes, lay = snap.documents[0].layout;
  const nIdx = lay.nodeIndex;
  const attrName = S.indexOf('data-wf-f');
  const rootOf = new Int32Array(nodes.parentIndex.length).fill(-1);
  for (let i = 0; i < rootOf.length; i++) {
    const p = nodes.parentIndex[i];
    let r = p >= 0 ? rootOf[p] : -1;
    const at = nodes.attributes[i];
    if (at && attrName >= 0) for (let q = 0; q < at.length; q += 2) if (at[q] === attrName) r = Number(S[at[q + 1]]);
    rootOf[i] = r;
  }
  const styleNames = snap.styleNames;
  const si = (n) => styleNames.indexOf(n);
  const iBg = si('background-color'), iBi = si('background-image'), iVis = si('visibility'), iOp = si('opacity');
  const iBw = ['border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width'].map(si);
  const MEDIA = new Set(['IMG', 'VIDEO', 'CANVAS', 'svg', 'IFRAME', 'PICTURE', 'OBJECT', 'EMBED', 'INPUT', 'BUTTON', 'SELECT', 'TEXTAREA']);
  const alpha = (c) => { if (!c || c === 'transparent') return 0; const m = c.match(/rgba?\(([^)]*)\)/); if (m) { const p = m[1].split(/[ ,\/]+/); return p.length > 3 ? parseFloat(p[3]) : 1; } return 1; };
  const P = []; // paintables: {j,root,x,y,w,h,order}
  for (let j = 0; j < nIdx.length; j++) {
    const ni = nIdx[j];
    const b = lay.bounds[j];
    if (!b || b[2] <= 0 || b[3] <= 0) continue;
    const st = lay.styles[j];
    let vis = 'visible', op = 1;
    if (st && st.length) { vis = S[st[iVis]]; op = parseFloat(S[st[iOp]]); }
    if (vis === 'hidden' || vis === 'collapse' || op === 0) continue;
    let paint = false;
    const txt = lay.text[j];
    if (txt >= 0 && /\S/.test(S[txt])) paint = true;
    else if (st && st.length) {
      const nm = S[nodes.nodeName[ni]];
      if (MEDIA.has(nm) || MEDIA.has(nm.toUpperCase())) paint = true;
      else if (alpha(S[st[iBg]]) > 0 || S[st[iBi]] !== 'none') paint = true;
      else if (iBw.some((q) => parseFloat(S[st[q]]) > 0)) paint = true;
    }
    if (!paint) continue;
    P.push({ j, root: rootOf[ni], x: b[0], y: b[1], w: b[2], h: b[3], order: lay.paintOrders[j] });
  }
  const out = [];
  const r0 = rects[0];
  const less = (a, b) => (a.order !== b.order ? a.order < b.order : a.j < b.j);
  for (let k = 1; k < frames.length; k++) {
    const y0 = frames[k].y, cur = rects[k], prev = rects[k - 1];
    const moved = cur.map((c, i) => Math.abs(c[0] - prev[i][0]) > 0.5 || Math.abs(c[1] - prev[i][1]) > 0.5);
    const Svis = [], Fvis = [];
    for (const p of P) {
      if (p.root >= 0 && moved[p.root]) {
        const dx = cur[p.root][0] - r0[p.root][0], dy = cur[p.root][1] - r0[p.root][1];
        const f = { ...p, x: p.x + dx, y: p.y + dy };
        if (f.y < y0 + H && f.y + f.h > y0 && f.x < 1e5) Fvis.push(f);
      } else if (p.y < y0 + H && p.y + p.h > y0) Svis.push(p);
    }
    let inter = false, ex = null;
    if (Fvis.length) for (const f of Fvis) {
      for (const s of Svis) {
        if (!less(f, s)) continue;
        const ox = Math.min(f.x + f.w, s.x + s.w) - Math.max(f.x, s.x), oy = Math.min(f.y + f.h, s.y + s.h) - Math.max(f.y, s.y);
        if (ox > 0.5 && oy > 0.5) { inter = true; ex = { root: f.root, f: [f.j, f.order], s: [s.j, s.order] }; break; }
      }
      if (inter) break;
    }
    out.push({ k, movedRoots: moved.filter(Boolean).length, F: Fvis.length > 0, inter, ex });
  }
  return out;
}

async function run(name, spec) {
  const local = spec.startsWith('local:');
  const ctx = await browser.newContext({ javaScriptEnabled: !local, viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, colorScheme: 'light', locale: 'en-US' });
  const page = await ctx.newPage();
  const res = { name, spec, local };
  const t0 = Date.now();
  try {
    let url = spec;
    if (local) {
      const pn = spec.slice(6);
      url = 'http://snowghost.test/page/index.html';
      const body = readFileSync(LOCAL + pn + '.html');
      const sheets = SHEETS[pn].map(([s, f]) => ({ suffix: s, body: readFileSync(LOCAL + f) })).sort((a, b) => b.suffix.length - a.suffix.length);
      await page.route('**/*', (route) => {
        const u = route.request().url();
        if (u === url) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body });
        const s = sheets.find((c) => u.endsWith(c.suffix));
        if (s) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: s.body });
        return route.abort();
      });
    }
    page.setDefaultTimeout(60000);
    let resp = null;
    try { resp = await page.goto(url, { timeout: 35000, waitUntil: 'load' }); } catch (e) { res.gotoErr = e.message.split('\n')[0]; }
    res.status = resp ? resp.status() : null;
    res.finalUrl = page.url();
    try { await page.waitForLoadState('networkidle', { timeout: 6000 }); } catch (e) {}
    await sleep(2500);
    res.title = (await page.title().catch(() => '')).slice(0, 80);
    await page.evaluate(inpage);
    const cdp = await ctx.newCDPSession(page);
    // ---- census
    res.census = await page.evaluate(() => window.__wf.census());
    // ---- layers
    let layers = null;
    cdp.on('LayerTree.layerTreeDidChange', (e) => { if (e.layers) layers = e.layers; });
    await cdp.send('LayerTree.enable');
    await page.evaluate(() => { scrollBy(0, 1); scrollBy(0, -1); });
    await sleep(800);
    if (layers) {
      const reasons = {}; let drawing = 0, withNode = 0;
      for (const l of layers) {
        if (l.drawsContent) drawing++;
        if (l.backendNodeId) withNode++;
        try { const r = await cdp.send('LayerTree.compositingReasons', { layerId: l.layerId }); for (const q of r.compositingReasons || []) reasons[q] = (reasons[q] || 0) + 1; } catch (e) {}
      }
      res.layers = { total: layers.length, drawsContent: drawing, withNode, reasons };
    }
    await cdp.send('LayerTree.disable').catch(() => {});
    // ---- X17
    const si = await page.evaluate(() => window.__wf.scrollInfo());
    res.scroll = si;
    const H = si.H;
    const totalSteps = Math.max(0, Math.ceil((si.scrollH - H) / H));
    const K = Math.min(STEP_CAP, totalSteps);
    res.x17 = { H, scrollH: si.scrollH, totalSteps, K, capped: totalSteps > K, canScroll: si.canScroll };
    if (K >= 1) {
      // pass 1: trigger lazy content
      for (let k = 1; k <= K; k++) { await page.evaluate((y) => window.scrollTo({ top: y, behavior: 'instant' }), k * H); await sleep(120); }
      await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
      await sleep(600);
      const si2 = await page.evaluate(() => window.__wf.scrollInfo());
      res.x17.scrollH2 = si2.scrollH;
      const K2 = Math.min(STEP_CAP, Math.max(0, Math.ceil((si2.scrollH - H) / H)));
      res.x17.K = K2; res.x17.capped = Math.ceil((si2.scrollH - H) / H) > K2;
      const nroots = await page.evaluate(() => window.__wf.prep());
      res.x17.roots = nroots;
      let snap = null;
      let r0 = null;
      if (nroots > 0) {
        r0 = await page.evaluate(() => window.__wf.rootRects());
        await cdp.send('DOMSnapshot.enable');
        snap = await cdp.send('DOMSnapshot.captureSnapshot', { computedStyles: ['background-color', 'background-image', 'visibility', 'opacity', 'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width'], includePaintOrder: true, includeDOMRects: false });
        snap.styleNames = ['background-color', 'background-image', 'visibility', 'opacity', 'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width'];
        res.x17.snapNodes = snap.documents[0].nodes.parentIndex.length;
      }
      const frames = [], rects = [];
      let prev = null;
      for (let k = 0; k <= K2; k++) {
        await page.evaluate((y) => window.scrollTo({ top: y, behavior: 'instant' }), k * H);
        await sleep(120);
        const y = await page.evaluate(() => scrollY);
        let fb;
        if (nroots > 0) fb = await page.evaluate((p) => window.__wf.frameB(p), prev);
        else fb = { cur: [], moved: [], interleavedPoints: 0, nsPoints: 0, points: 144, examples: [] };
        prev = fb.cur;
        rects.push(fb.cur);
        frames.push({ y, B: { movedRoots: fb.moved.filter(Boolean).length, nsPoints: fb.nsPoints, inter: fb.interleavedPoints, ex: fb.examples } });
      }
      // sanity: did the scroll actually advance?
      res.x17.ys = frames.map((f) => f.y);
      res.x17.rootDescr = nroots ? await page.evaluate((n) => Array.from({ length: n }, (_, i) => window.__wf.descr(i)), nroots) : [];
      res.x17.rootPos = nroots ? rects[1] ? rects[1].map((r) => r[4]) : [] : [];
      let A = [];
      if (snap && K2 >= 1) A = interleaveA(snap, rects, frames, H);
      res.x17.frames = [];
      for (let k = 1; k <= K2; k++) {
        const a = A[k - 1] || { movedRoots: 0, F: false, inter: false };
        const f = frames[k];
        res.x17.frames.push({ k, y: f.y, advanced: f.y > frames[k - 1].y, movedA: a.movedRoots, nsA: a.F, A: a.inter, exA: a.ex || null, movedB: f.B.movedRoots, nsB: f.B.nsPoints > 0, B: f.B.inter > 0, Bpts: f.B.inter, Bex: f.B.ex });
      }
    }
  } catch (e) { res.error = String(e.stack || e).split('\n').slice(0, 4).join(' | '); }
  res.ms = Date.now() - t0;
  await ctx.close();
  return res;
}
for (const s of sites) {
  const at = s.indexOf('=');
  const name = s.slice(0, at), spec = s.slice(at + 1);
  console.error(new Date().toISOString(), 'start', name);
  const r = await run(name, spec);
  writeFileSync(`${outDir}/${name}.json`, JSON.stringify(r));
  const x = r.x17 || {};
  console.error(name, 'status', r.status, 'els', r.census && r.census.R.elements, 'K', x.K, 'roots', x.roots, 'A', x.frames && x.frames.filter((f) => f.A).length, 'B', x.frames && x.frames.filter((f) => f.B).length, 'layers', r.layers && r.layers.total, r.error || '', r.gotoErr || '', r.ms, 'ms');
}
await browser.close();
