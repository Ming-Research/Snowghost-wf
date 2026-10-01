// The measurements behind the layout investigation's proposed scope
// (DESIGN.md in this directory), run in Chromium under the style oracle's
// setup: scripts disabled, a 1280x720 viewport, device scale factor 1,
// media type screen, every request but the page and its mapped sheets
// refused (tests/css/style_oracle.mjs).
//
//   node scope_probe.mjs MODE PAGE.html [URL-SUFFIX=SHEET.css ...]
//
// MODE is one of
//   widths      the widths of five fixed spans (PAGE is ignored), to see how
//               Chromium rounds text advances;
//   shares      each rendered text node's characters, classified by the
//               nearest layout feature above it, and how many element boxes
//               have a fractional edge;
//   containers  every flex or grid container holding 2,000 characters or
//               more, with its tracks and its items' boxes;
//   fonts       the replaced elements and form controls, and the platform
//               fonts of about 1,500 sampled text nodes, by glyph count;
//   generated   the ::before and ::after boxes with content, and the list
//               markers;
//   families    the platform font Chromium draws a paragraph with for each of
//               a fixed list of font-family names (PAGE is ignored).
//
// It is removed when the layout oracle (DESIGN.md, Oracle) reports these
// figures itself. CHROMIUM and PLAYWRIGHT override the browser binary and
// the playwright module's path, as in the style oracle.

import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';

const CHROMIUM = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PLAYWRIGHT = process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright';
const PAGE_URL = 'http://snowghost.test/page/index.html';
const WIDTHS_PAGE = `<!doctype html><body style="margin:0">
<span id=a style="font:16px serif">iiiiiiiiii</span><br><span id=b style="font:16px serif">i</span><br>
<span id=c style="font:16px sans-serif">The quick brown fox jumps over the lazy dog</span><br>
<span id=d style="font:13px monospace">The quick brown fox</span><br><span id=e style="font:16px serif">AVAWAVAW</span></body>`;

const FAMILIES = ['Arial', 'Helvetica', 'Times New Roman', 'Times', 'Courier New', 'Courier', 'Georgia', 'Verdana', 'Segoe UI',
  'IBM Plex Serif', 'Linux Libertine', 'Arial Plus', 'Droid Sans Fallback', 'DejaVu Serif', 'serif', 'sans-serif', 'monospace',
  'system-ui', 'cursive', 'fantasy'];
const GENERIC = new Set(['serif', 'sans-serif', 'monospace', 'system-ui', 'cursive', 'fantasy']);
const FAMILIES_PAGE = '<!doctype html><body>' + FAMILIES.map((family, i) =>
  `<p id=f${i} style="font-family:${GENERIC.has(family) ? family : `'${family}'`}">Hello</p>`).join('') + '</body>';

const [mode, pagePath, ...mappings] = process.argv.slice(2);
const pageless = mode === 'widths' || mode === 'families';
if (!['widths', 'shares', 'containers', 'fonts', 'generated', 'families'].includes(mode) || (!pageless && !pagePath)) {
  process.stderr.write('usage: scope_probe.mjs widths|shares|containers|fonts|generated|families PAGE.html [URL-SUFFIX=SHEET.css ...]\n');
  process.exit(2);
}
const sheets = mappings.map((mapping) => {
  const at = mapping.lastIndexOf('=');
  return { suffix: mapping.slice(0, at), body: readFileSync(mapping.slice(at + 1)) };
}).sort((a, b) => b.suffix.length - a.suffix.length);
const body = mode === 'widths' ? Buffer.from(WIDTHS_PAGE) : mode === 'families' ? Buffer.from(FAMILIES_PAGE) : readFileSync(pagePath);

const require = createRequire(import.meta.url);
const { chromium } = require(PLAYWRIGHT);
const browser = await chromium.launch({ executablePath: CHROMIUM, headless: true });
const context = await browser.newContext({
  javaScriptEnabled: false, viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, colorScheme: 'light', locale: 'en-US',
});
const page = await context.newPage();
page.setDefaultTimeout(600000);
await page.emulateMedia({ media: 'screen', colorScheme: 'light' });
await page.route('**/*', (route) => {
  const url = route.request().url();
  if (url === PAGE_URL) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body });
  const sheet = sheets.find((candidate) => url.endsWith(candidate.suffix));
  if (sheet) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: sheet.body });
  return route.abort();
});
await page.goto(PAGE_URL, { waitUntil: 'load' });

let out;
if (mode === 'widths') {
  out = await page.evaluate(() => Object.fromEntries([...'abcde'].map((id) => [id, document.getElementById(id).getBoundingClientRect().width])));
} else if (mode === 'shares') {
  out = await page.evaluate(() => {
    const kinds = {};
    let total = 0;
    let fragments = 0;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = node.data.replace(/\s+/g, ' ').trim();
      if (!text) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      const rects = range.getClientRects();
      if (rects.length === 0) continue;
      fragments += rects.length;
      let kind = 'block/inline';
      for (let e = node.parentElement; e; e = e.parentElement) {
        const s = getComputedStyle(e);
        if (s.position === 'absolute' || s.position === 'fixed') { kind = 'abs/fixed'; break; }
        if (s.float !== 'none') { kind = 'float'; break; }
        if (/table/.test(s.display)) { kind = 'table'; break; }
        const parent = e.parentElement && getComputedStyle(e.parentElement).display;
        if (parent && /flex/.test(parent)) { kind = 'flex item'; break; }
        if (parent && /grid/.test(parent)) { kind = 'grid item'; break; }
        if (s.display === 'inline-block') { kind = 'inline-block'; break; }
      }
      kinds[kind] = (kinds[kind] || 0) + text.length;
      total += text.length;
    }
    let boxes = 0;
    let fractional = 0;
    for (const e of document.querySelectorAll('*')) {
      const r = e.getBoundingClientRect();
      if (!r.width && !r.height) continue;
      boxes++;
      if (r.x % 1 || r.y % 1 || r.width % 1 || r.height % 1) fractional++;
    }
    const share = {};
    for (const kind in kinds) share[kind] = (100 * kinds[kind] / total).toFixed(1) + '%';
    return { chars: total, textFragments: fragments, share, boxes, fractionalBoxes: fractional, documentHeight: document.documentElement.scrollHeight };
  });
} else if (mode === 'containers') {
  out = await page.evaluate(() => {
    const flat = (e) => (e.textContent || '').replace(/\s+/g, ' ').length;
    const name = (e) => e.localName + (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.split(' ')[0] : '');
    const found = [];
    for (const e of document.querySelectorAll('*')) {
      const s = getComputedStyle(e);
      if (!/flex|grid/.test(s.display) || flat(e) < 2000) continue;
      const r = e.getBoundingClientRect();
      const items = [...e.children].filter((c) => getComputedStyle(c).display !== 'none').map((c) => {
        const b = c.getBoundingClientRect();
        const cs = getComputedStyle(c);
        return `${name(c)} ${Math.round(b.x)},${Math.round(b.y)} ${Math.round(b.width)}x${Math.round(b.height)} chars=${flat(c)} flex=${cs.flex} position=${cs.position}`;
      });
      found.push({ container: name(e), display: s.display, direction: s.flexDirection, wrap: s.flexWrap, columns: s.gridTemplateColumns,
        rows: s.gridTemplateRows, areas: s.gridTemplateAreas, size: `${Math.round(r.width)}x${Math.round(r.height)}`, chars: flat(e), items });
    }
    return found;
  });
} else if (mode === 'fonts') {
  const replaced = await page.evaluate(() => {
    const tally = {};
    for (const e of document.querySelectorAll('img,svg,input,button,select,textarea,video,iframe')) {
      const r = e.getBoundingClientRect();
      const key = e.localName + (e.hasAttribute('width') ? ' with width attribute' : '') + (r.width || r.height ? ' boxed' : ' empty');
      tally[key] = (tally[key] || 0) + 1;
    }
    return tally;
  });
  const cdp = await context.newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { root } = await cdp.send('DOM.getDocument', { depth: -1, pierce: false });
  const texts = [];
  (function walk(node) {
    if (node.nodeType === 3 && node.nodeValue.trim()) texts.push(node.nodeId);
    for (const child of node.children || []) walk(child);
  })(root);
  const step = Math.max(1, Math.floor(texts.length / 1500));
  const fonts = {};
  let sampled = 0;
  for (let k = 0; k < texts.length; k += step) {
    sampled++;
    const result = await cdp.send('CSS.getPlatformFontsForNode', { nodeId: texts[k] });
    for (const font of result.fonts) fonts[font.familyName] = (fonts[font.familyName] || 0) + font.glyphCount;
  }
  out = { replaced, sampledTextNodes: sampled, glyphsByFont: fonts };
} else if (mode === 'families') {
  const cdp = await context.newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { root } = await cdp.send('DOM.getDocument', { depth: -1 });
  out = {};
  for (let i = 0; i < FAMILIES.length; i++) {
    const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: '#f' + i });
    const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId });
    out[FAMILIES[i]] = fonts.map((font) => font.familyName).join(', ');
  }
} else {
  out = await page.evaluate(() => {
    const tally = { before: 0, after: 0, contentChars: 0, markersInside: 0, markersOutside: 0, common: {} };
    for (const e of document.querySelectorAll('*')) {
      for (const pseudo of ['::before', '::after']) {
        const content = getComputedStyle(e, pseudo).content;
        if (!content || content === 'none' || content === 'normal') continue;
        tally[pseudo.slice(2)]++;
        tally.contentChars += content.length;
        const key = e.localName + pseudo + ' ' + content.slice(0, 24);
        tally.common[key] = (tally.common[key] || 0) + 1;
      }
      const s = getComputedStyle(e);
      if (s.display === 'list-item' && s.listStyleType !== 'none') {
        if (s.listStylePosition === 'inside') tally.markersInside++;
        else tally.markersOutside++;
      }
    }
    tally.common = Object.entries(tally.common).sort((a, b) => b[1] - a[1]).slice(0, 8);
    return tally;
  });
}
process.stdout.write(JSON.stringify(out, null, 1) + '\n');
await browser.close();
