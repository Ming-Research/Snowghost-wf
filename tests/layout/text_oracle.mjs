// The Chromium oracle of the layout stage's text preparation, pkg::layout::text
// (research/investigations/layout/DESIGN.md, "Text preparation results").
//
//   node tests/layout/text_oracle.mjs cases PREFIX COUNT PAGE.html [URL-SUFFIX=SHEET.css ...] > cases.tsv
//   node tests/layout/text_oracle.mjs extents > extents.tsv
//   node tests/layout/text_oracle.mjs breaks > breaks.tsv
//   node tests/layout/text_oracle.mjs measure cases.tsv > chromium.tsv
//   node tests/layout/text_oracle.mjs compare cases.tsv chromium.tsv snowghost.tsv
//   node tests/layout/text_oracle.mjs fallback > fallback.txt
//   node tests/layout/text_oracle.mjs ascii > ascii.txt
//
// cases loads PAGE.html as tests/layout/layout_oracle.mjs does (scripts
// disabled, a 1280x720 viewport, device scale factor 1, media type screen,
// the mapped sheets served and every other request refused) and writes one
// text case for each of COUNT rendered text nodes taken at even steps of
// document order, each with the computed style of its parent element.
// extents writes the extents cases of the faces the oracle checks, breaks
// a fixed set of text cases for break opportunities (URLs, slashes,
// hyphens, punctuation, scripts, special spaces) under each word-break and
// overflow-wrap. measure
// lays every case out in a page of its own font size (Chromium shares a
// font's platform data between sizes that are close, so one page per size
// keeps one case's size from changing another's) and writes Chromium's
// result; compare judges a Snowghost driver's output, the text_oracle
// entry's, against it. fallback writes the platform face Chromium draws
// single characters with, each in a block of its own, under a few
// font-family lists and styles: the evidence for the fallback order of
// pkg::oracle::fonts. ascii writes, for each printable ASCII scalar, whether
// Chromium breaks a line between it and each printable ASCII scalar, the
// table pkg::layout::text's ascii_breaks encodes.
//
// Case file. UTF-8, LF line ends, no header, two kinds of line:
//
//   T<TAB>ID<TAB>FAMILY<TAB>SIZE<TAB>WEIGHT<TAB>STYLE<TAB>LETTER<TAB>WORD<TAB>WRAP<TAB>WORDBREAK<TAB>OVERFLOWWRAP<TAB>TEXT
//   X<TAB>ID<TAB>FAMILY<TAB>SIZE<TAB>WEIGHT<TAB>STYLE
//
// ID is a token without tabs or spaces; FAMILY the computed font-family as
// Chromium serializes it; SIZE, LETTER (letter-spacing, 0 for normal) and
// WORD (word-spacing) decimal px values; WEIGHT a decimal weight; STYLE 0
// for normal, 1 italic and 2 oblique; WRAP 1 when white-space wraps lines
// and 0 when it does not; WORDBREAK 0 normal, 1 break-all, 2 keep-all, 3
// break-word; OVERFLOWWRAP 0 normal, 1 break-word, 2 anywhere; TEXT the
// scalar values of one line of text after white-space processing and
// text-transform, in lowercase hexadecimal separated by single spaces.
//
// Result file, as measure writes it and the driver writes it:
//
//   T<TAB>ID<TAB>WIDTH<TAB>FACES<TAB>BREAKS<TAB>EMERGENCY
//   X<TAB>ID<TAB>CONTENT<TAB>LINE<TAB>BASELINE
//
// WIDTH is the text's width on one line in 1/64 px, rounded up (Chromium's
// getBoundingClientRect width of a span with white-space: pre, times 64);
// FACES the faces that draw it, comma-separated, each NAME:COUNT with the
// face's PostScript name and its glyph count (Chromium's
// CSS.getPlatformFontsForNode; the driver counts scalars and writes face
// indices, with b appended for synthetic bold, that compare maps through its
// F lines); BREAKS the indices i of TEXT
// before which a line may break, comma-separated, as Chromium breaks the
// text in a zero-width box with the case's white-space and word-break (normal
// for break-word, which is normal with overflow-wrap anywhere) and
// overflow-wrap normal; EMERGENCY the further indices it breaks before with
// the case's word-break and overflow-wrap. CONTENT is ascent plus descent in px (a span's
// height), LINE the height of a one-line block with line-height normal and
// BASELINE the distance from that block's top to its baseline. The driver
// also writes one F<TAB>N<TAB>NAME line per face it loaded, in order, NAME
// the face's PostScript name, through which compare maps its face indices.
//
// compare prints the share of text cases whose width is exactly Chromium's
// and whose faces are Chromium's, the extents cases that match, and each
// mismatch class with its count and examples. Exit status 0 when at least
// 99.0% of the text cases match exactly and every extents case matches, 1
// otherwise, 2 on a usage or input error.
//
// CHROMIUM and PLAYWRIGHT override the browser binary and the playwright
// module's path.

import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';

const CHROMIUM = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PLAYWRIGHT = process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright';
const PAGE_URL = 'http://snowghost.test/page/index.html';
const PASS_PERCENT = 99.0;
const MAX_SCALARS = 120;

function usage(message) {
  if (message) process.stderr.write(`text_oracle: ${message}\n`);
  process.stderr.write(
    'usage: text_oracle.mjs cases PREFIX COUNT PAGE.html [URL-SUFFIX=SHEET.css ...]\n' +
    '       text_oracle.mjs extents\n' +
    '       text_oracle.mjs breaks\n' +
    '       text_oracle.mjs measure cases.tsv\n' +
    '       text_oracle.mjs compare cases.tsv chromium.tsv snowghost.tsv\n' +
    '       text_oracle.mjs fallback\n' +
    '       text_oracle.mjs ascii\n');
  process.exit(2);
}

function writeOut(text) {
  return new Promise((resolve, reject) => {
    process.stdout.write(text, (error) => (error ? reject(error) : resolve()));
  });
}

async function launch() {
  const require = createRequire(import.meta.url);
  const { chromium } = require(PLAYWRIGHT);
  return chromium.launch({ executablePath: CHROMIUM, headless: true });
}

async function blankPage(browser) {
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, colorScheme: 'light', locale: 'en-US',
  });
  const page = await context.newPage();
  page.setDefaultTimeout(600000);
  await page.emulateMedia({ media: 'screen', colorScheme: 'light' });
  await page.route('**/*', (route) => (route.request().url() === PAGE_URL
    ? route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: '<!doctype html><html lang=en><body style="margin:0"></body></html>' })
    : route.abort()));
  await page.goto(PAGE_URL, { waitUntil: 'load' });
  return { context, page };
}

// ---- cases ----

async function cases(prefix, count, pagePath, mappings) {
  const sheets = mappings.map((mapping) => {
    const at = mapping.lastIndexOf('=');
    if (at <= 0 || at === mapping.length - 1) usage(`a sheet mapping is URL-SUFFIX=SHEET.css, not ${mapping}`);
    return { suffix: mapping.slice(0, at), body: readFileSync(mapping.slice(at + 1)) };
  }).sort((a, b) => b.suffix.length - a.suffix.length);
  const pageBody = readFileSync(pagePath);
  const browser = await launch();
  try {
    const context = await browser.newContext({
      javaScriptEnabled: false, viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, colorScheme: 'light', locale: 'en-US',
    });
    const page = await context.newPage();
    page.setDefaultTimeout(600000);
    await page.emulateMedia({ media: 'screen', colorScheme: 'light' });
    await page.route('**/*', (route) => {
      const url = route.request().url();
      if (url === PAGE_URL) return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody });
      const sheet = sheets.find((candidate) => url.endsWith(candidate.suffix));
      if (sheet) return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: sheet.body });
      return route.abort();
    });
    await page.goto(PAGE_URL, { waitUntil: 'load' });
    const lines = await page.evaluate(({ prefix, count, maxScalars }) => {
      const STYLE = { normal: 0, italic: 1 };
      const WORD_BREAK = { normal: 0, 'break-all': 1, 'keep-all': 2, 'break-word': 3 };
      const OVERFLOW_WRAP = { normal: 0, 'break-word': 1, anywhere: 2 };
      const found = [];
      const range = document.createRange();
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        const parent = node.parentElement;
        if (!parent) continue;
        range.selectNodeContents(node);
        if (range.getClientRects().length === 0) continue;
        const s = getComputedStyle(parent);
        const collapse = s.whiteSpaceCollapse === 'collapse' || s.whiteSpaceCollapse === 'preserve-breaks';
        let text = node.data;
        if (collapse) {
          text = text.replace(/[ \t\n\r\f]+/g, ' ').trim();
        } else {
          text = text.split('\n').find((line) => line.trim() !== '') || '';
          if (/[\t\r\f]/.test(text)) continue;
        }
        if (s.textTransform === 'uppercase') text = text.toUpperCase();
        else if (s.textTransform === 'lowercase') text = text.toLowerCase();
        else if (s.textTransform !== 'none') continue;
        let scalars = Array.from(text).slice(0, maxScalars);
        while (scalars.length && collapse && scalars[scalars.length - 1] === ' ') scalars.pop();
        if (scalars.length === 0) continue;
        const style = STYLE[s.fontStyle] ?? 2;
        const letter = s.letterSpacing === 'normal' ? 0 : parseFloat(s.letterSpacing);
        const word = parseFloat(s.wordSpacing) || 0;
        const wrap = s.textWrapMode === 'nowrap' ? 0 : 1;
        found.push([s.fontFamily, parseFloat(s.fontSize), parseFloat(s.fontWeight), style, letter, word, wrap,
          WORD_BREAK[s.wordBreak] ?? 0, OVERFLOW_WRAP[s.overflowWrap] ?? 0,
          scalars.map((c) => c.codePointAt(0).toString(16)).join(' ')]);
      }
      const out = [];
      const step = Math.max(1, found.length / count);
      for (let k = 0, n = 0; Math.floor(k) < found.length && n < count; k += step, n++) {
        out.push(`T\t${prefix}${n}\t${found[Math.floor(k)].join('\t')}`);
      }
      return out;
    }, { prefix, count, maxScalars: MAX_SCALARS });
    await writeOut(lines.join('\n') + '\n');
    process.stderr.write(`${pagePath}: ${lines.length} cases\n`);
  } finally {
    await browser.close();
  }
}

// ---- extents ----

const EXTENT_FAMILIES = ['Liberation Serif', 'Liberation Sans', 'Liberation Mono', 'DejaVu Sans Mono', 'DejaVu Sans', 'DejaVu Serif',
  'FreeSerif', 'FreeSans', 'FreeMono', 'IPAGothic', 'Unifont', 'Loma'];
const EXTENT_SIZES = [8, 10, 11, 12, 13, 13.3333, 14, 15, 16, 17, 18, 20, 21.3333, 24, 26, 32, 37, 48];

function extents() {
  const lines = [];
  let n = 0;
  for (const family of EXTENT_FAMILIES) {
    for (const size of EXTENT_SIZES) {
      for (const [weight, style] of [[400, 0], [700, 0], [400, 1]]) {
        lines.push(`X\tx${n++}\t"${family}"\t${size}\t${weight}\t${style}`);
      }
    }
  }
  return writeOut(lines.join('\n') + '\n');
}

// ---- breaks ----

const BREAK_TEXTS = ['http://www.example.com/foo/bar?x=1&y=2', 'and/or', 'e-mail and well-known', '1,000,000.50', 'ISO/IEC 16262',
  'foo_bar.baz(qux)', 'a\u2014b a\u2013b', 'x = (y + 1) * 2;', 'CJK \u6f22\u5b57\u304b\u306a\u6df7\u3058\u308a\u6587', '\u00c9COLE-\u00e9cole',
  "don't \u201cquoted\u201d", 'price: $10.00 or 50%', '#hash a/b/c', '[1, 2, 3] { key: value }', '1-2-3 -1 a -1',
  'foo-bar-baz Ab12', 'C++ and C#', 'na\u00efve caf\u00e9', '\u0395\u03bb\u03bb\u03b7\u03bd\u03b9\u03ba\u03ac \u03ba\u03b5\u03af\u03bc\u03b5\u03bd\u03bf',
  '\u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u0442\u0435\u043a\u0441\u0442', 'non\u00a0breaking space', 'soft\u00adhyphen', 'zero\u200bwidth',
  'word\u2060joiner', 'emoji \ud83d\ude00 text', 'a.b,c;d:e!f?g', 'x\u2192y \u2200x \u2208 A', 'O(n\u00b2) \u2264 k', '\u00a7 1.2.3 \u00b6',
  'self.foo=bar||baz', 'Array.prototype.map()', '"quoted"(paren)', 'end.', 'U+2028 and \u2026 ellipsis'];
const BREAK_SETTINGS = [[0, 0], [1, 0], [2, 0], [3, 0], [0, 1], [0, 2]];

function breaks() {
  const lines = [];
  let n = 0;
  for (const text of BREAK_TEXTS) {
    for (const [wordBreak, overflowWrap] of BREAK_SETTINGS) {
      const hex = Array.from(text).map((c) => c.codePointAt(0).toString(16)).join(' ');
      lines.push(`T\tb${n++}\tserif\t16\t400\t0\t0\t0\t1\t${wordBreak}\t${overflowWrap}\t${hex}`);
    }
  }
  return writeOut(lines.join('\n') + '\n');
}

// ---- ascii ----

async function ascii() {
  const browser = await launch();
  try {
    const { page } = await blankPage(browser);
    const rows = await page.evaluate(() => {
      const out = [];
      const range = document.createRange();
      for (let a = 0x21; a <= 0x7e; a++) {
        let row = '';
        for (let b = 0x21; b <= 0x7e; b++) {
          const box = document.createElement('div');
          box.style.cssText = 'width:0;font:16px serif;white-space:pre-wrap';
          box.textContent = 'x' + String.fromCharCode(a) + String.fromCharCode(b) + 'x';
          document.body.appendChild(box);
          const node = box.firstChild;
          range.setStart(node, 1);
          range.setEnd(node, 2);
          const first = range.getBoundingClientRect().top;
          range.setStart(node, 2);
          range.setEnd(node, 3);
          row += range.getBoundingClientRect().top > first + 0.5 ? '1' : '0';
          box.remove();
        }
        out.push(`${String.fromCharCode(a)} ${row}`);
      }
      return out;
    });
    await writeOut(rows.join('\n') + '\n');
  } finally {
    await browser.close();
  }
}

// ---- measure ----

function parseCases(path) {
  const textCases = [];
  const extentCases = [];
  const lines = readFileSync(path, 'utf8').split('\n');
  lines.forEach((line, at) => {
    if (line === '') return;
    const f = line.split('\t');
    if (f[0] === 'T' && f.length === 12) {
      textCases.push({ id: f[1], family: f[2], size: f[3], weight: f[4], style: Number(f[5]), letter: f[6], word: f[7],
        wrap: f[8] === '1', wordBreak: Number(f[9]), overflowWrap: Number(f[10]),
        text: f[11] === '' ? '' : String.fromCodePoint(...f[11].split(' ').map((h) => parseInt(h, 16))) });
    } else if (f[0] === 'X' && f.length === 6) {
      extentCases.push({ id: f[1], family: f[2], size: f[3], weight: f[4], style: Number(f[5]) });
    } else {
      usage(`${path}:${at + 1}: malformed case`);
    }
  });
  return { textCases, extentCases };
}

async function measure(path) {
  const { textCases, extentCases } = parseCases(path);
  const bySize = new Map();
  for (const c of [...textCases, ...extentCases]) {
    if (!bySize.has(c.size)) bySize.set(c.size, { text: [], extent: [] });
    (c.text === undefined ? bySize.get(c.size).extent : bySize.get(c.size).text).push(c);
  }
  const browser = await launch();
  try {
    for (const [size, group] of bySize) {
      const { context, page } = await blankPage(browser);
      const results = await page.evaluate(({ texts, extentsList }) => {
        const STYLES = ['normal', 'italic', 'oblique'];
        const WORD_BREAK = ['normal', 'break-all', 'keep-all', 'break-word'];
        const OVERFLOW_WRAP = ['normal', 'break-word', 'anywhere'];
        const font = (element, c) => {
          element.style.fontFamily = c.family;
          element.style.fontSize = `${c.size}px`;
          element.style.fontWeight = c.weight;
          element.style.fontStyle = STYLES[c.style];
          element.style.lineHeight = 'normal';
        };
        const body = document.body;
        const lineStarts = (box) => {
          const node = box.firstChild;
          const starts = [];
          if (!node) return starts;
          const range = document.createRange();
          let offset = 0;
          let index = 0;
          let top = null;
          for (const ch of box.textContent) {
            range.setStart(node, offset);
            range.setEnd(node, offset + ch.length);
            const rects = range.getClientRects();
            const rect = rects.length === 0 ? null : rects[rects.length - 1];
            if (rect !== null && (rect.width !== 0 || rect.height !== 0)) {
              if (top !== null && rect.top > top + 0.5) starts.push(index);
              if (top === null || rect.top > top + 0.5) top = rect.top;
            }
            offset += ch.length;
            index++;
          }
          return starts;
        };
        const breakBox = (c, overflowWrap, wordBreak) => {
          const box = document.createElement('div');
          font(box, c);
          box.style.width = '0px';
          box.style.whiteSpace = c.wrap ? 'pre-wrap' : 'pre';
          box.style.wordBreak = WORD_BREAK[wordBreak];
          box.style.overflowWrap = OVERFLOW_WRAP[overflowWrap];
          box.style.letterSpacing = `${c.letter}px`;
          box.style.wordSpacing = `${c.word}px`;
          box.textContent = c.text;
          body.appendChild(box);
          return box;
        };
        const textResults = texts.map((c) => {
          const line = document.createElement('div');
          line.style.whiteSpace = 'pre';
          const span = document.createElement('span');
          span.className = 'measured';
          font(span, c);
          span.style.letterSpacing = `${c.letter}px`;
          span.style.wordSpacing = `${c.word}px`;
          span.textContent = c.text;
          line.appendChild(span);
          body.appendChild(line);
          const normal = breakBox(c, 0, c.wordBreak === 3 ? 0 : c.wordBreak);
          const own = c.overflowWrap === 0 && c.wordBreak !== 3 ? null : breakBox(c, c.overflowWrap, c.wordBreak);
          return { span, normal, own };
        }).map(({ span, normal, own }) => {
          const width = span.getBoundingClientRect().width * 64;
          const breaks = lineStarts(normal);
          const allowed = new Set(breaks);
          const emergency = own ? lineStarts(own).filter((i) => !allowed.has(i)) : [];
          return [width, breaks.join(','), emergency.join(',')];
        });
        const extentResults = extentsList.map((c) => {
          const block = document.createElement('div');
          font(block, c);
          block.style.whiteSpace = 'pre';
          const span = document.createElement('span');
          span.textContent = ' ';
          const marker = document.createElement('span');
          marker.style.display = 'inline-block';
          marker.style.width = '0px';
          marker.style.height = '0px';
          block.appendChild(span);
          block.appendChild(marker);
          body.appendChild(block);
          return { block, span, marker };
        }).map(({ block, span, marker }) => {
          const top = block.getBoundingClientRect().top;
          return [span.getClientRects()[0].height, block.getBoundingClientRect().height, marker.getBoundingClientRect().bottom - top];
        });
        return { textResults, extentResults };
      }, { texts: group.text, extentsList: group.extent });
      const cdp = await context.newCDPSession(page);
      await cdp.send('DOM.enable');
      await cdp.send('CSS.enable');
      const { root } = await cdp.send('DOM.getDocument', { depth: 0 });
      const { nodeIds } = await cdp.send('DOM.querySelectorAll', { nodeId: root.nodeId, selector: 'span.measured' });
      const out = [];
      for (let k = 0; k < group.text.length; k++) {
        const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId: nodeIds[k] });
        const faces = fonts.map((f) => `${f.postScriptName || f.familyName}:${f.glyphCount}`).join(',');
        const [width, breaks, emergency] = results.textResults[k];
        out.push(`T\t${group.text[k].id}\t${width}\t${faces}\t${breaks}\t${emergency}`);
      }
      group.extent.forEach((c, k) => out.push(`X\t${c.id}\t${results.extentResults[k].join('\t')}`));
      await writeOut(out.length ? out.join('\n') + '\n' : '');
      await context.close();
      process.stderr.write(`size ${size}: ${group.text.length} text and ${group.extent.length} extents cases\n`);
    }
  } finally {
    await browser.close();
  }
}

// ---- compare ----

function parseResults(path) {
  const texts = new Map();
  const extentResults = new Map();
  const faces = [];
  readFileSync(path, 'utf8').split('\n').forEach((line, at) => {
    if (line === '') return;
    const f = line.split('\t');
    if (f[0] === 'T' && f.length === 6) {
      const list = (field) => (field === '' ? [] : field.split(',').map(Number));
      const faceCounts = f[3] === '' ? [] : f[3].split(',').map((item) => {
        const colon = item.lastIndexOf(':');
        return [item.slice(0, colon), Number(item.slice(colon + 1))];
      });
      texts.set(f[1], { width: Number(f[2]), faces: faceCounts, breaks: list(f[4]), emergency: list(f[5]) });
    } else if (f[0] === 'X' && f.length === 5) {
      extentResults.set(f[1], f.slice(2).map(Number));
    } else if (f[0] === 'F' && f.length === 3) {
      faces.push(f[2]);
    } else {
      usage(`${path}:${at + 1}: malformed result`);
    }
  });
  return { texts, extentResults, faces };
}

function compare(casesPath, chromiumPath, snowghostPath) {
  const { textCases, extentCases } = parseCases(casesPath);
  const chromium = parseResults(chromiumPath);
  const snowghost = parseResults(snowghostPath);
  const loaded = snowghost.faces;
  const classes = new Map();
  const note = (name, example) => {
    if (!classes.has(name)) classes.set(name, { count: 0, examples: [] });
    const entry = classes.get(name);
    entry.count++;
    if (entry.examples.length < 3) entry.examples.push(example);
  };
  const faceSet = (list) => list.map(([name]) => name).sort().join(',');
  let widthExact = 0;
  let facesSame = 0;
  let breaksSame = 0;
  for (const c of textCases) {
    const want = chromium.texts.get(c.id);
    const got = snowghost.texts.get(c.id);
    const shown = `${c.id} ${JSON.stringify(c.family)} ${c.size}px ${c.weight} ${JSON.stringify(c.text.slice(0, 40))}`;
    if (!want || !got) { note('missing result', shown); continue; }
    const gotFaces = got.faces.map(([index, n]) => [loaded[Number(index.replace(/b$/, ''))] ?? index, n]);
    const sameFaces = faceSet(gotFaces) === faceSet(want.faces);
    if (sameFaces) facesSame++;
    if (want.width === got.width) widthExact++;
    else note(sameFaces ? 'width, same faces' : 'width, different faces',
      `${shown} chromium ${want.width / 64} (${faceSet(want.faces)}) snowghost ${got.width / 64} (${faceSet(gotFaces)})`);
    const breaks = (r) => `${r.breaks.join(',')}|${r.emergency.join(',')}`;
    if (breaks(want) === breaks(got)) breaksSame++;
    else {
      const extra = got.breaks.filter((i) => !want.breaks.includes(i));
      const missing = want.breaks.filter((i) => !got.breaks.includes(i));
      const around = (i) => JSON.stringify([...c.text].slice(Math.max(0, i - 3), i).join('') + '|' + [...c.text].slice(i, i + 3).join(''));
      const kind = extra.length ? `break Snowghost only ${around(extra[0])}` : missing.length ? `break Chromium only ${around(missing[0])}` : 'emergency breaks';
      note(`breaks: ${extra.length ? 'Snowghost only' : missing.length ? 'Chromium only' : 'emergency'}`, `${shown} ${kind} ws=${c.wrap} wb=${c.wordBreak} ow=${c.overflowWrap}`);
    }
  }
  let extentsSame = 0;
  for (const c of extentCases) {
    const want = chromium.extentResults.get(c.id);
    const got = snowghost.extentResults.get(c.id);
    const shown = `${c.id} ${c.family} ${c.size}px ${c.weight} ${c.style}`;
    if (!want || !got) { note('missing extents', shown); continue; }
    if (want.join() === got.join()) extentsSame++;
    else note('extents', `${shown} chromium ${want.join(' ')} snowghost ${got.join(' ')}`);
  }
  const percent = (n, d) => (d === 0 ? 100 : Math.floor((10000 * n) / d) / 100);
  const n = textCases.length;
  const lines = [
    `text cases: ${n}`,
    `  width exact at 1/64 px: ${widthExact} (${percent(widthExact, n)}%)`,
    `  same faces: ${facesSame} (${percent(facesSame, n)}%)`,
    `  same breaks: ${breaksSame} (${percent(breaksSame, n)}%)`,
    `extents cases: ${extentCases.length}, matching ${extentsSame}`,
  ];
  for (const [name, entry] of [...classes].sort((a, b) => b[1].count - a[1].count)) {
    lines.push(`${name}: ${entry.count}`);
    for (const example of entry.examples) lines.push(`  ${example}`);
  }
  process.stdout.write(lines.join('\n') + '\n');
  const pass = percent(widthExact, n) >= PASS_PERCENT && extentsSame === extentCases.length;
  process.exit(pass ? 0 : 1);
}

// ---- fallback ----

const FALLBACK_CHARACTERS = [...'→∀∈𝔽ℝ漢あกאعक😀✓★⌘⟨↪⇒⊂⊕⌊◇✔❯⚠🔗აաሀதক한⿰∎⊤▶△◆☐✗⬆⯈⎕⏎␣⇧⌥⓪①㈠'];
const FALLBACK_CONTEXTS = [['serif', 400, 'normal'], ['sans-serif', 400, 'normal'], ['monospace', 400, 'normal'],
  ['serif', 700, 'normal'], ['serif', 400, 'italic'], ['sans-serif', 700, 'italic'], ['"Liberation Serif"', 700, 'normal'], ['Georgia, serif', 700, 'normal']];

async function fallback() {
  const browser = await launch();
  try {
    const { context, page } = await blankPage(browser);
    await page.evaluate(({ chars, contexts }) => {
      contexts.forEach(([family, weight, style], k) => chars.forEach((c, i) => {
        const block = document.createElement('div');
        block.id = `c${k}_${i}`;
        block.style.fontFamily = family;
        block.style.fontWeight = weight;
        block.style.fontStyle = style;
        block.textContent = c;
        document.body.appendChild(block);
      }));
    }, { chars: FALLBACK_CHARACTERS, contexts: FALLBACK_CONTEXTS });
    const cdp = await context.newCDPSession(page);
    await cdp.send('DOM.enable');
    await cdp.send('CSS.enable');
    const { root } = await cdp.send('DOM.getDocument', { depth: 0 });
    const lines = [`# character\t${FALLBACK_CONTEXTS.map(([f, w, s]) => `${f} ${w} ${s}`).join('\t')}`];
    for (let i = 0; i < FALLBACK_CHARACTERS.length; i++) {
      const row = [`U+${FALLBACK_CHARACTERS[i].codePointAt(0).toString(16).toUpperCase().padStart(4, '0')}`];
      for (let k = 0; k < FALLBACK_CONTEXTS.length; k++) {
        const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: `#c${k}_${i}` });
        const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId });
        row.push(fonts.map((f) => f.postScriptName || f.familyName).join(','));
      }
      lines.push(row.join('\t'));
    }
    await writeOut(lines.join('\n') + '\n');
  } finally {
    await browser.close();
  }
}

const [mode, ...rest] = process.argv.slice(2);
if (mode === 'cases' && rest.length >= 3 && Number(rest[1]) > 0) await cases(rest[0], Number(rest[1]), rest[2], rest.slice(3));
else if (mode === 'extents' && rest.length === 0) await extents();
else if (mode === 'measure' && rest.length === 1) await measure(rest[0]);
else if (mode === 'compare' && rest.length === 3) compare(...rest);
else if (mode === 'fallback' && rest.length === 0) await fallback();
else if (mode === 'breaks' && rest.length === 0) await breaks();
else if (mode === 'ascii' && rest.length === 0) await ascii();
else usage();
