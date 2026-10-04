// Times X5's edit scripts in Chromium (DESIGN.md in this directory).
//
// usage: node chromium.mjs PAGE NODES SCRIPT [SUFFIX=SHEET ...]
//
// Loads PAGE as http://localhost/page/index.html, cross-origin isolated so
// that performance.now resolves 5 us, serving it and each
// stylesheet whose URL ends in SUFFIX from local files, in a 1280 by 720
// viewport with page scripts disabled, through the DevTools protocol of the
// Chromium build CHROME names (Playwright's 1194 build by default). NODES is
// the layout oracle's `nodes` listing of the same page: an edit's node is
// found by its position among elements and text nodes in tree order, and
// every listed text node's data is checked against the page before any edit.
// Each edit of SCRIPT is applied by DOM calls, followed by a forced style
// recalculation and layout (documentElement.offsetHeight), and prints
// `edit I us U style_us S layout_us L`: U the microseconds of the edit and
// the forced layout by performance.now (100 us resolution), S and L the
// durations of the main thread's UpdateLayoutTree and Layout trace events
// between the edit's two console.timeStamp markers; then a summary line.
// Exits 2 on any mismatch or failure.
import { spawn } from 'node:child_process';
import { readFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [pagePath, nodesPath, scriptPath, ...sheetArgs] = process.argv.slice(2);
if (!scriptPath) { console.error('usage: node chromium.mjs PAGE NODES SCRIPT [SUFFIX=SHEET ...]'); process.exit(2); }
const CHROME = process.env.CHROME || join(process.env.HOME, 'Library/Caches/ms-playwright/chromium-1194/chrome-mac/Chromium.app/Contents/MacOS/Chromium');
const PAGE_URL = 'http://localhost/page/index.html';
const sheets = sheetArgs.map((a) => { const k = a.lastIndexOf('='); return { suffix: a.slice(0, k), body: readFileSync(a.slice(k + 1)) }; });
const pageBody = readFileSync(pagePath);

// The listing: kind and node id in tree order; text data unescaped.
const unescape = (s) => s.replace(/\\(\\|n)/g, (_, c) => (c === 'n' ? '\n' : '\\'));
const listing = [];
for (const line of readFileSync(nodesPath, 'utf8').split('\n')) {
  if (line.startsWith('E ')) { const f = line.split(' '); listing.push({ kind: 'E', id: +f[1], name: f[3] }); }
  else if (line.startsWith('T ')) { const f = line.split(' '); const data = line.split(' ').slice(4).join(' '); listing.push({ kind: 'T', id: +f[1], data: unescape(data) }); }
}
let nodeCount = 0;
for (const line of readFileSync(nodesPath, 'utf8').split('\n')) if (line.startsWith('N ')) nodeCount = +line.split(' ')[1];
const script = readFileSync(scriptPath, 'utf8').split('\n').filter((l) => l.length);

const port = 9300 + Math.floor(Math.random() * 600);
const profile = mkdtempSync(join(tmpdir(), 'e1-chrome-'));
const proc = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--no-first-run', '--no-default-browser-check', 'about:blank'], { stdio: 'ignore' });
const fail = (why) => { console.error('chromium.mjs: ' + why); proc.kill(); process.exit(2); };
let targets;
for (let i = 0; i < 200; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (targets.some((t) => t.type === 'page')) break; } catch {} await new Promise((r) => setTimeout(r, 50)); }
if (!targets) fail('Chromium did not start');
const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let seq = 0; const pending = new Map(); const handlers = [];
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else for (const h of handlers) h(d); };
const send = (method, params = {}) => new Promise((r) => { const i = ++seq; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
handlers.push(async (d) => {
  if (d.method !== 'Fetch.requestPaused') return;
  const { requestId, request } = d.params;
  const css = sheets.find((s) => request.url.endsWith(s.suffix));
  if (request.url === PAGE_URL) await send('Fetch.fulfillRequest', { requestId, responseCode: 200, responseHeaders: [{ name: 'Content-Type', value: 'text/html; charset=utf-8' }, { name: 'Cross-Origin-Opener-Policy', value: 'same-origin' }, { name: 'Cross-Origin-Embedder-Policy', value: 'require-corp' }], body: pageBody.toString('base64') });
  else if (css) await send('Fetch.fulfillRequest', { requestId, responseCode: 200, responseHeaders: [{ name: 'Content-Type', value: 'text/css; charset=utf-8' }, { name: 'Cross-Origin-Resource-Policy', value: 'cross-origin' }], body: css.body.toString('base64') });
  else await send('Fetch.failRequest', { requestId, errorReason: 'BlockedByClient' });
});
let loaded = false;
const traceEvents = []; let traceDone = false;
handlers.push((d) => { if (d.method === 'Tracing.dataCollected') traceEvents.push(...d.params.value); if (d.method === 'Tracing.tracingComplete') traceDone = true; });
handlers.push((d) => { if (d.method === 'Page.loadEventFired') loaded = true; });
await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
await send('Emulation.setScriptExecutionDisabled', { value: true });
await send('Fetch.enable', { patterns: [{ urlPattern: '*' }] });
await send('Page.enable');
await send('Page.navigate', { url: PAGE_URL });
for (let i = 0; i < 600 && !loaded; i++) await new Promise((r) => setTimeout(r, 50));
if (!loaded) fail('the page did not load');
const evaluate = async (expression) => {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true });
  if (r.result?.exceptionDetails || r.error) fail('evaluate: ' + JSON.stringify(r.result?.exceptionDetails || r.error).slice(0, 400));
  return r.result.result.value;
};

// In the page: the elements and text nodes in tree order, and the edit
// operations. Byte offsets of the scripts become UTF-16 offsets here.
await evaluate(`(() => {
  const list = []; const w = document.createTreeWalker(document, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) list.push(n);
  window.__list = list; window.__byId = new Map(); window.__created = new Map();
  const enc = new TextEncoder();
  window.__offset = (data, bytes) => { let b = 0; for (let i = 0; i <= data.length; i++) { if (b === bytes) return i; if (i === data.length) break; const c = data.codePointAt(i); b += enc.encode(String.fromCodePoint(c)).length; if (c > 0xffff) i++; } throw new Error('byte offset ' + bytes + ' inside a character'); };
  window.__time = (f) => { const t0 = performance.now(); f(); document.documentElement.offsetHeight; return Math.round((performance.now() - t0) * 1000); };
  document.documentElement.offsetHeight;
  return list.length;
})()`);
const check = await evaluate(`JSON.stringify(window.__list.map((n) => n.nodeType === 3 ? ['T', n.data] : ['E', n.localName]))`);
const page = JSON.parse(check);
if (page.length !== listing.length) fail(`tree order holds ${page.length} nodes, the listing ${listing.length}`);
for (let k = 0; k < listing.length; k++) {
  const [kind, value] = page[k]; const l = listing[k];
  if (kind !== l.kind || (kind === 'T' && value !== l.data) || (kind === 'E' && value !== l.name)) fail(`node ${l.id} at position ${k} differs: ${JSON.stringify(page[k]).slice(0, 80)}`);
}
const position = new Map(listing.map((l, k) => [l.id, k]));
const node = (id) => { if (position.has(id)) return `window.__list[${position.get(id)}]`; return `window.__created.get(${id})`; };

const tracing = process.env.TRACE === '1';
if (tracing) await send('Tracing.start', { categories: 'devtools.timeline', transferMode: 'ReportEvents' });
if (!(await evaluate('self.crossOriginIsolated'))) fail('the page is not cross-origin isolated, so performance.now is coarse');
const linked = await evaluate(`JSON.stringify([...document.querySelectorAll('link[rel~=stylesheet]')].map((l) => { let rules = -1; try { rules = l.sheet ? l.sheet.cssRules.length : -1; } catch { rules = -2; } return [l.href, rules > 0]; }))`);
const served = JSON.parse(linked).filter(([href]) => sheets.some((s) => href.endsWith(s.suffix)));
if (served.length < sheets.length || served.some(([, loaded]) => !loaded)) fail('a served stylesheet did not load: ' + JSON.stringify(served).slice(0, 300));
const times = [];
let edits = 0; let next = nodeCount;
for (const line of script) {
  const kind = line[0]; const f = line.split(' ');
  if (kind === 'P') continue;
  if (kind === 'S') { await evaluate(`(() => { const s = document.createElement('style'); s.textContent = ${JSON.stringify(line.slice(2))}; document.head.appendChild(s); document.documentElement.offsetHeight; })()`); continue; }
  edits++;
  let op;
  if (kind === 'T') { const text = unescape(f.slice(3).join(' ')); op = `{ const n = ${node(+f[1])}; n.insertData(window.__offset(n.data, ${+f[2]}), ${JSON.stringify(text)}); }`; }
  else if (kind === 'D') op = `{ const n = ${node(+f[1])}; const a = window.__offset(n.data, ${+f[2]}); const b = window.__offset(n.data, ${+f[2] + +f[3]}); n.deleteData(a, b - a); }`;
  else if (kind === 'C') op = `${node(+f[1])}.classList.add(${JSON.stringify(f[2])})`;
  else if (kind === 'K') op = `${node(+f[1])}.classList.remove(${JSON.stringify(f[2])})`;
  else if (kind === 'B') {
    const text = unescape(f.slice(3).join(' ')); const before = f[2] === '-' ? 'null' : node(+f[2]);
    op = `{ const p = document.createElement('p'); p.textContent = ${JSON.stringify(text)}; window.__created.set(${next}, p); window.__created.set(${next + 1}, p.firstChild); ${node(+f[1])}.insertBefore(p, ${before}); }`;
    next += 2;
  } else if (kind === 'X') op = `${node(+f[1])}.remove()`;
  else fail('unknown edit line: ' + line);
  const us = await evaluate(`(() => { console.timeStamp('e1-begin-${edits}'); const us = window.__time(() => ${op}); console.timeStamp('e1-end-${edits}'); return us; })()`);
  times.push(us);
}
if (tracing) {
await send('Tracing.end');
for (let i = 0; i < 400 && !traceDone; i++) await new Promise((r) => setTimeout(r, 50));
if (!traceDone) fail('the trace did not complete');
}
const marks = new Map(); const spans = [];
for (const e of traceEvents) {
  const message = e.name === 'TimeStamp' && e.args?.data?.message;
  if (message && message.startsWith('e1-')) marks.set(message, { ts: e.ts, tid: e.tid });
  else if ((e.name === 'UpdateLayoutTree' || e.name === 'Layout') && e.ph === 'X') spans.push(e);
}
const traced = [];
for (let k = 1; k <= edits; k++) {
  const a = marks.get('e1-begin-' + k); const b = marks.get('e1-end-' + k);
  if (!tracing) { traced.push(times[k - 1]); console.log(`edit ${k} us ${times[k - 1]}`); continue; }
  if (!a || !b) fail('missing trace markers for edit ' + k);
  let style = 0; let layout = 0;
  for (const e of spans) if (e.tid === a.tid && e.ts >= a.ts && e.ts + e.dur <= b.ts) { if (e.name === 'Layout') layout += e.dur; else style += e.dur; }
  traced.push(style + layout);
  console.log(`edit ${k} us ${times[k - 1]} style_us ${Math.round(style)} layout_us ${Math.round(layout)}`);
}
const sorted = times.slice().sort((a, b) => a - b);
const tsorted = traced.slice().sort((a, b) => a - b);
console.log(`summary edits ${times.length} median_us ${sorted[Math.floor(sorted.length / 2)]} max_us ${sorted[sorted.length - 1]} traced_median_us ${Math.round(tsorted[Math.floor(tsorted.length / 2)])} traced_max_us ${Math.round(tsorted[tsorted.length - 1])}`);
ws.close(); proc.kill();
