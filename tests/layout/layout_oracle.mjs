// The Chromium oracle of the layout stage's boxes
// (research/investigations/layout/DESIGN.md, "Oracle" and "Criteria").
//
//   node tests/layout/layout_oracle.mjs dump PAGE.html [URL-SUFFIX=SHEET.css ...] > chromium.tsv
//   node tests/layout/layout_oracle.mjs compare chromium.tsv snowghost.tsv
//
// dump loads PAGE.html exactly as tests/css/style_oracle.mjs does: scripts
// disabled, a 1280x720 viewport, device scale factor 1, media type screen,
// prefers-color-scheme light, the page served at
// http://snowghost.test/page/index.html, the mapped sheets served and every
// other request refused. Playwright runs headless Chromium with hidden
// scrollbars, so no scrollbar takes space.
//
// File format, the contract a Snowghost driver writes to. UTF-8, LF line
// ends, no header, three kinds of line:
//
//   E<TAB>INDEX<TAB>LOCALNAME<TAB>PARENT<TAB>LEVEL<TAB>RECTS
//   T<TAB>ORDINAL<TAB>PARENT<TAB>RECTS
//   H<TAB>HEIGHT
//
// - One E line per element in document order, as the style oracle lists
//   them (document.querySelectorAll('*')), INDEX counting from 0 and
//   LOCALNAME escaped as there; PARENT is the INDEX of its parent element,
//   or -1 when its parent is no element. LEVEL is n when the element has no box
//   (getClientRects() is empty: display none or contents, or inside a
//   subtree without boxes), i when its computed display is inline-level
//   (inline, inline-block, inline-flex, inline-grid, inline-table, ruby,
//   ruby-text) and b otherwise. RECTS is the element's getClientRects(), in
//   order, each as X,Y,WIDTH,HEIGHT, separated by single spaces; empty for
//   level n.
// - One T line per text node with at least one rendered fragment, in
//   document order: ORDINAL counts every text node of a tree-order walk of
//   the document that does not enter template contents, from 0, whether or
//   not it is rendered; PARENT is the INDEX of its parent element; RECTS are
//   the getClientRects() of a Range selecting its contents, one per line
//   fragment.
// - One H line: the document element's scrollHeight.
// - Numbers are written as JavaScript writes them (Chromium's are
//   multiples of 1/64, which it writes exactly); a Snowghost driver writes
//   the shortest decimal that reads back as its value.
//
// compare reads two such files, requires the same E lines' INDEX and
// LOCALNAME and PARENT in the same order, and judges by Chromium's LEVEL:
//
// - A block-level element (b) matches when Snowghost gives it level b and
//   its width, its height and its position relative to its parent's box are
//   each within 1 px of Chromium's. A box is the union of its RECTS; its
//   parent's box is that of its nearest ancestor element with a box, or the
//   origin for the root.
// - An inline-level element (i) matches when Snowghost gives it level i and
//   the same number of RECTS, each as wide as Chromium's within 1 px.
// - An element without a box (n) matches when Snowghost gives it none.
// - A text node matches when both files list it with the same number of
//   RECTS, each as wide within 1 px; a node one file lists and the other
//   does not is a mismatch.
//
// It prints, for each of the three judged measures (block-level boxes,
// inline-level boxes, text nodes), the matched count, the total, the
// percentage (truncated to two decimals) and the share that matches
// exactly (every compared number within 1/64 px); the elements without a
// box; the reported measures that are not judged (every box's absolute
// position within 1 px, and the scroll heights); and for each judged
// measure below 100% its eight most frequent mismatch classes with their
// counts and one example. Exit status: 0 when the three judged measures
// each match at least 99.0%; 1 when one does not; 2 on a usage or input
// error; 3 when the files' structure differs.
//
// CHROMIUM and PLAYWRIGHT override the browser binary and the playwright
// module's path.

import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { basename } from 'node:path';

const CHROMIUM = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PLAYWRIGHT = process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright';
const PAGE_URL = 'http://snowghost.test/page/index.html';
const BATCH = 5000;
const PASS_PERCENT = 99.0;
const PIXEL = 1;
const EXACT = 1 / 64 + 1e-4;

function usage(message) {
  if (message) process.stderr.write(`layout_oracle: ${message}\n`);
  process.stderr.write(
    'usage: layout_oracle.mjs dump PAGE.html [URL-SUFFIX=SHEET.css ...]\n' +
    '       layout_oracle.mjs compare chromium.tsv snowghost.tsv\n');
  process.exit(2);
}

function writeOut(text) {
  return new Promise((resolve, reject) => {
    process.stdout.write(text, (error) => (error ? reject(error) : resolve()));
  });
}

// ---- dump ----

async function dump(pagePath, mappings) {
  const started = process.hrtime.bigint();
  const sheets = mappings.map((mapping) => {
    const at = mapping.lastIndexOf('=');
    if (at <= 0 || at === mapping.length - 1) usage(`a sheet mapping is URL-SUFFIX=SHEET.css, not ${mapping}`);
    return { suffix: mapping.slice(0, at), body: readFileSync(mapping.slice(at + 1)) };
  }).sort((a, b) => b.suffix.length - a.suffix.length);
  const pageBody = readFileSync(pagePath);

  const require = createRequire(import.meta.url);
  const { chromium } = require(PLAYWRIGHT);
  const browser = await chromium.launch({ executablePath: CHROMIUM, headless: true });
  try {
    const context = await browser.newContext({
      javaScriptEnabled: false,
      viewport: { width: 1280, height: 720 },
      deviceScaleFactor: 1,
      colorScheme: 'light',
      locale: 'en-US',
    });
    const page = await context.newPage();
    page.setDefaultTimeout(600000);
    await page.emulateMedia({ media: 'screen', colorScheme: 'light' });
    await page.route('**/*', (route) => {
      const url = route.request().url();
      if (url === PAGE_URL) {
        return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody });
      }
      const sheet = sheets.find((candidate) => url.endsWith(candidate.suffix));
      if (sheet) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: sheet.body });
      return route.abort();
    });
    await page.goto(PAGE_URL, { waitUntil: 'load' });

    const counts = await page.evaluate(() => {
      globalThis.__layoutOracleElements = document.querySelectorAll('*');
      const texts = [];
      const walker = document.createTreeWalker(document, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) texts.push(node);
      globalThis.__layoutOracleTexts = texts;
      const index = new Map();
      globalThis.__layoutOracleElements.forEach((element, i) => index.set(element, i));
      globalThis.__layoutOracleIndex = index;
      return { elements: globalThis.__layoutOracleElements.length, texts: texts.length };
    });
    for (let start = 0; start < counts.elements; start += BATCH) {
      const text = await page.evaluate(({ start, end }) => {
        const escape = (value) => value.replace(/[\\\t\n\r]/g,
          (c) => (c === '\\' ? '\\\\' : c === '\t' ? '\\t' : c === '\n' ? '\\n' : '\\r'));
        const INLINE = new Set(['inline', 'inline-block', 'inline-flex', 'inline-grid', 'inline-table', 'ruby', 'ruby-text']);
        const rects = (list) => [...list].map((r) => `${r.x},${r.y},${r.width},${r.height}`).join(' ');
        const elements = globalThis.__layoutOracleElements;
        const lines = [];
        for (let i = start; i < end; i++) {
          const element = elements[i];
          const list = element.getClientRects();
          const level = list.length === 0 ? 'n' : INLINE.has(getComputedStyle(element).display) ? 'i' : 'b';
          const parent = element.parentElement === null ? -1 : globalThis.__layoutOracleIndex.get(element.parentElement);
          lines.push(`E\t${i}\t${escape(element.localName)}\t${parent}\t${level}\t${level === 'n' ? '' : rects(list)}`);
        }
        return lines.join('\n') + '\n';
      }, { start, end: Math.min(start + BATCH, counts.elements) });
      await writeOut(text);
    }
    for (let start = 0; start < counts.texts; start += BATCH) {
      const text = await page.evaluate(({ start, end }) => {
        const rects = (list) => [...list].map((r) => `${r.x},${r.y},${r.width},${r.height}`).join(' ');
        const texts = globalThis.__layoutOracleTexts;
        const index = globalThis.__layoutOracleIndex;
        const lines = [];
        const range = document.createRange();
        for (let k = start; k < end; k++) {
          const node = texts[k];
          range.selectNodeContents(node);
          const list = range.getClientRects();
          if (list.length === 0) continue;
          const parent = node.parentElement === null ? -1 : index.get(node.parentElement);
          lines.push(`T\t${k}\t${parent}\t${rects(list)}`);
        }
        return lines.length === 0 ? '' : lines.join('\n') + '\n';
      }, { start, end: Math.min(start + BATCH, counts.texts) });
      await writeOut(text);
    }
    const height = await page.evaluate(() => document.documentElement.scrollHeight);
    await writeOut(`H\t${height}\n`);
    const seconds = Number(process.hrtime.bigint() - started) / 1e9;
    process.stderr.write(`${basename(pagePath)}: ${counts.elements} elements, ${counts.texts} text nodes in ${seconds.toFixed(2)} s\n`);
  } finally {
    await browser.close();
  }
}

// ---- compare ----

function unescape(field) {
  return field.replace(/\\(.)/g, (_, c) => (c === 't' ? '\t' : c === 'n' ? '\n' : c === 'r' ? '\r' : c));
}

function parseRects(field, where) {
  if (field === '') return [];
  return field.split(' ').map((rect) => {
    const parts = rect.split(',').map(Number);
    if (parts.length !== 4 || parts.some((n) => !Number.isFinite(n))) usage(`${where}: malformed rect ${rect}`);
    return { x: parts[0], y: parts[1], w: parts[2], h: parts[3] };
  });
}

function union(rects) {
  let left = Infinity;
  let top = Infinity;
  let right = -Infinity;
  let bottom = -Infinity;
  for (const r of rects) {
    left = Math.min(left, r.x);
    top = Math.min(top, r.y);
    right = Math.max(right, r.x + r.w);
    bottom = Math.max(bottom, r.y + r.h);
  }
  return { x: left, y: top, w: right - left, h: bottom - top };
}

function read(path) {
  let text;
  try {
    text = readFileSync(path, 'utf8');
  } catch (error) {
    usage(`cannot read ${path}: ${error.message}`);
  }
  const elements = [];
  const texts = new Map();
  let height = null;
  const lines = text.split('\n');
  if (lines[lines.length - 1] === '') lines.pop();
  lines.forEach((line, n) => {
    const where = `${path}:${n + 1}`;
    const fields = line.split('\t');
    if (fields[0] === 'E' && fields.length === 6) {
      if (Number(fields[1]) !== elements.length) usage(`${where}: element ${fields[1]} out of order`);
      const parent = Number(fields[3]);
      if (!Number.isInteger(parent) || parent < -1 || parent >= elements.length) usage(`${where}: parent ${fields[3]}`);
      if (!['b', 'i', 'n'].includes(fields[4])) usage(`${where}: level ${fields[4]}`);
      elements.push({ name: unescape(fields[2]), parent, level: fields[4], rects: parseRects(fields[5], where) });
    } else if (fields[0] === 'T' && fields.length === 4) {
      texts.set(Number(fields[1]), { parent: Number(fields[2]), rects: parseRects(fields[3], where) });
    } else if (fields[0] === 'H' && fields.length === 2) {
      height = Number(fields[1]);
    } else {
      usage(`${where}: unknown line`);
    }
  });
  return { elements, texts, height };
}

function differs(a, b, limit) {
  return Math.abs(a - b) > limit;
}

class Tally {
  constructor() {
    this.total = 0;
    this.matched = 0;
    this.exact = 0;
    this.classes = new Map();
  }

  add(ok, exact, label, example) {
    this.total++;
    if (ok) this.matched++;
    if (exact) this.exact++;
    if (!ok) {
      const entry = this.classes.get(label) || { count: 0, example };
      entry.count++;
      this.classes.set(label, entry);
    }
  }

  percent(n) {
    return this.total === 0 ? 100 : Math.floor((10000 * n) / this.total) / 100;
  }

  print(title) {
    const share = this.percent(this.matched);
    process.stdout.write(`${title}: ${this.matched}/${this.total} ${share.toFixed(2)}% within 1px, ` +
      `${this.percent(this.exact).toFixed(2)}% exact\n`);
    const top = [...this.classes].sort((a, b) => b[1].count - a[1].count).slice(0, 8);
    for (const [label, entry] of top) process.stdout.write(`  ${entry.count}  ${label}  e.g. ${entry.example}\n`);
    return share >= PASS_PERCENT;
  }
}

function compare(chromiumPath, snowghostPath) {
  const chromium = read(chromiumPath);
  const snowghost = read(snowghostPath);
  if (chromium.elements.length !== snowghost.elements.length) {
    process.stdout.write(`element count differs: chromium ${chromium.elements.length}, snowghost ${snowghost.elements.length}\n`);
    process.exit(3);
  }
  for (let i = 0; i < chromium.elements.length; i++) {
    const c = chromium.elements[i];
    const s = snowghost.elements[i];
    if (c.name !== s.name || c.parent !== s.parent) {
      process.stdout.write(`element ${i}: chromium ${c.name} in ${c.parent}, snowghost ${s.name} in ${s.parent}\n`);
      process.exit(3);
    }
  }

  const boxOf = (file, i) => (file.elements[i].level === 'n' ? null : union(file.elements[i].rects));
  const holder = (file, i) => {
    for (let p = file.elements[i].parent; p >= 0; p = file.elements[p].parent) if (file.elements[p].level !== 'n') return boxOf(file, p);
    return { x: 0, y: 0, w: 0, h: 0 };
  };

  const blocks = new Tally();
  const inlines = new Tally();
  const absent = new Tally();
  const absolute = new Tally();
  for (let i = 0; i < chromium.elements.length; i++) {
    const c = chromium.elements[i];
    const s = snowghost.elements[i];
    const example = `${i} ${c.name}`;
    if (c.level === 'n') {
      absent.add(s.level === 'n', s.level === 'n', `${c.name}: chromium none, snowghost ${s.level}`, example);
      continue;
    }
    if (s.level === 'n') {
      (c.level === 'b' ? blocks : inlines).add(false, false, `${c.name}: snowghost has no box`, example);
      absolute.add(false, false, `${c.name}: no box`, example);
      continue;
    }
    const cb = boxOf(chromium, i);
    const sb = boxOf(snowghost, i);
    const absoluteOk = !differs(cb.x, sb.x, PIXEL) && !differs(cb.y, sb.y, PIXEL);
    absolute.add(absoluteOk, !differs(cb.x, sb.x, EXACT) && !differs(cb.y, sb.y, EXACT), `${c.name}`, example);
    if (c.level === 'b') {
      if (s.level !== 'b') {
        blocks.add(false, false, `${c.name}: snowghost inline-level`, example);
        continue;
      }
      const cp = holder(chromium, i);
      const sp = holder(snowghost, i);
      const measures = [
        ['width', cb.w, sb.w],
        ['height', cb.h, sb.h],
        ['x', cb.x - cp.x, sb.x - sp.x],
        ['y', cb.y - cp.y, sb.y - sp.y],
      ];
      const off = measures.filter(([, a, b]) => differs(a, b, PIXEL));
      const exact = measures.every(([, a, b]) => !differs(a, b, EXACT));
      const label = off.length === 0 ? '' : `${c.name} ${off.map(([m]) => m).join('+')}`;
      blocks.add(off.length === 0, exact, label, `${example} ${off.map(([m, a, b]) => `${m} ${a}/${b}`).join(' ')}`);
    } else {
      if (s.level !== 'i') {
        inlines.add(false, false, `${c.name}: snowghost block-level`, example);
        continue;
      }
      const sameCount = c.rects.length === s.rects.length;
      const widthsOk = sameCount && c.rects.every((r, k) => !differs(r.w, s.rects[k].w, PIXEL));
      const exact = sameCount && c.rects.every((r, k) => !differs(r.w, s.rects[k].w, EXACT));
      const label = !sameCount ? `${c.name} fragments` : `${c.name} width`;
      inlines.add(widthsOk, exact, label, `${example} ${c.rects.length}/${s.rects.length} fragments`);
    }
  }

  const texts = new Tally();
  const ordinals = new Set([...chromium.texts.keys(), ...snowghost.texts.keys()]);
  for (const ordinal of [...ordinals].sort((a, b) => a - b)) {
    const c = chromium.texts.get(ordinal);
    const s = snowghost.texts.get(ordinal);
    const parent = (c || s).parent;
    const name = parent >= 0 && parent < chromium.elements.length ? chromium.elements[parent].name : '?';
    const example = `text ${ordinal} in ${parent} ${name}`;
    if (!c || !s) {
      texts.add(false, false, `in ${name}: ${c ? 'snowghost' : 'chromium'} renders none`, example);
      continue;
    }
    const sameCount = c.rects.length === s.rects.length;
    const ok = sameCount && c.rects.every((r, k) => !differs(r.w, s.rects[k].w, PIXEL));
    const exact = sameCount && c.rects.every((r, k) => !differs(r.w, s.rects[k].w, EXACT));
    texts.add(ok, exact, sameCount ? `in ${name}: width` : `in ${name}: fragments`, `${example} ${c.rects.length}/${s.rects.length} fragments`);
  }

  const judged = [blocks.print('block-level boxes'), inlines.print('inline-level boxes'), texts.print('text nodes')];
  absent.print('elements without a box (reported)');
  absolute.print('absolute positions (reported)');
  process.stdout.write(`scroll height (reported): chromium ${chromium.height}, snowghost ${snowghost.height}\n`);
  process.exit(judged.every(Boolean) ? 0 : 1);
}

const [command, ...rest] = process.argv.slice(2);
if (command === 'dump' && rest.length >= 1) {
  await dump(rest[0], rest.slice(1));
} else if (command === 'compare' && rest.length === 2) {
  compare(rest[0], rest[1]);
} else {
  usage();
}
