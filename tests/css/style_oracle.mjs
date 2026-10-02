// The Chromium oracle of the style stage's computed values
// (research/investigations/style/DESIGN.md, "Oracle" and "Criteria").
//
//   node tests/css/style_oracle.mjs dump PAGE.html [URL-SUFFIX=SHEET.css ...] > chromium.tsv
//   node tests/css/style_oracle.mjs compare chromium.tsv snowghost.tsv
//
// dump loads PAGE.html in Chromium headless with scripts disabled, a
// 1280x720 viewport, device scale factor 1, media type screen and
// prefers-color-scheme light. The page is served at the fixed URL
// http://snowghost.test/page/index.html. A request whose URL ends with one of
// the given suffixes is answered from the mapped local file as text/css (the
// longest matching suffix wins; a mapping splits at its last =, so a
// suffix may hold =); every other request (fonts, images,
// scripts, unmapped sheets) is refused. Standard error lists each served
// and each refused style sheet or document URL, then the element count, the
// run time and the refused requests counted by resource type.
// Chromium fetches a sheet whose `media` does not hold, such as
// media=print, but does not apply it.
//
// File format, the contract a Snowghost driver writes to. UTF-8, LF line
// ends, one header line, then one line per element, then one line per
// generated pseudo-element:
//
//   index<TAB>name<TAB>display<TAB>position<TAB>...<TAB>word-break
//   INDEX<TAB>LOCALNAME<TAB>VALUE<TAB>...<TAB>VALUE
//
// - Elements are in document order: a preorder walk of the document's
//   elements that does not enter template contents, which is
//   document.querySelectorAll('*'). INDEX counts from 0; LOCALNAME is the
//   element's local name as the DOM gives it (case preserved, so SVG's
//   linearGradient stays as written), without a namespace.
// - The value columns are the 92 longhands of PROPERTIES below, in that
//   order, each the computed value as
//   element.computedStyleMap().get(property).toString() serializes it in
//   Chromium 141 (lengths resolved to px except percentages, colors
//   resolved, currentcolor resolved to the color). get() returns the first
//   item of a property Chromium lists as list-valued, so grid-auto-columns
//   and grid-auto-rows hold their first track only.
// - After the element lines comes one line for each ::before and ::after
//   pseudo-element whose computed content, as
//   getComputedStyle(element, pseudo).content reads it, is not none, in
//   document order of their elements, ::before before ::after. INDEX is the
//   element's index and LOCALNAME is ::before or ::after. Pseudo-elements
//   have no computedStyleMap, so the values are
//   getComputedStyle(element, pseudo).getPropertyValue(property), which
//   serializes as computedStyleMap does except for the properties whose
//   resolved value differs from the computed value (CSSOM, "resolved
//   values"): width, height, top, right, bottom, left, the four margins and
//   the four paddings, which read their used value, min-width and min-height,
//   which Chromium reads as 0px for auto on a box that is no flex or grid
//   item, line-height, which reads its used value in px unless it is normal,
//   and grid-template-columns and
//   grid-template-rows on a grid container, which read the used track sizes.
//   The dump writes those cells empty (RESOLVED and GRID_RESOLVED below); a
//   driver writes its computed value there or nothing.
// - In INDEX, LOCALNAME and every value, a backslash is written \\, a tab
//   \t, a line feed \n and a carriage return \r; no other escape exists.
//
// compare reads two such files and requires the same header, the same
// number of lines and, line by line, the same INDEX and LOCALNAME, with the
// element lines numbered 0, 1, 2 and so on; at the first difference it
// reports it and stops with status 1. It then compares every value after
// unescaping and normalizing both sides, except that a cell of a
// pseudo-element line that is empty in the first file, Chromium's, is not
// compared and counts in neither the matched nor the total count:
//
// - The value is split into tokens: numbers (with an optional unit or %),
//   quoted strings, identifiers, and the punctuation ( ) , /. Whitespace
//   only separates tokens, so runs of whitespace, and whitespace next to
//   punctuation, do not count.
// - Identifiers and units compare ASCII case-insensitively; quoted strings
//   compare exactly (a string's quote character, ' or ", does not count).
// - A number with unit px matches when |a - b| <= 1/64 + 1e-4. Any other
//   number (unitless, %, or another unit, which must be the same) matches
//   when |a - b| <= 1e-4 * max(1, |a|, |b|).
// - rgb() and rgba(), with comma or space syntax, are read as four
//   channels: red, green and blue in 0-255 (a percentage times 2.55) and
//   alpha in 0-1 (a percentage divided by 100; 1 when absent). So
//   rgb(0, 0, 0) equals rgba(0, 0, 0, 1). Channels match within 0.5,
//   alpha within 0.002. Other color functions (lab, lch, oklab, oklch,
//   color, hsl, hwb) and color keywords fall under the token rules above;
//   Chromium resolves hsl and hwb to rgb() or rgba() and keeps lab, lch,
//   oklab, oklch and color() in their own space.
//
// - counter-reset, counter-increment and counter-set: Chromium keeps a
//   computed counter list in a hash map, so it serializes the name and value
//   pairs in an order of its own rather than the specified one; their pairs
//   are sorted on both sides before comparing.
//
// compare prints, per property, the matched count, the total of compared
// cells over element and pseudo-element lines and the percentage
// (truncated to two decimals), and for each property below 100%
// its five most frequent mismatching (chromium value, snowghost value)
// pairs, unescaped but not normalized, with their counts and one example
// element's index and local name.
// Exit status: 0 when every property matches on at least 99.0% of its
// compared cells; 1 when one does not, or the files' structure differs; 2 on a
// usage or input error.
//
// CHROMIUM and PLAYWRIGHT override the browser binary and the playwright
// module's path.

import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { basename } from 'node:path';

const PROPERTIES = [
  'display', 'position', 'float', 'clear', 'overflow-x', 'overflow-y', 'box-sizing', 'visibility', 'z-index',
  'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
  'top', 'right', 'bottom', 'left',
  'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
  'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
  'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width',
  'border-top-style', 'border-right-style', 'border-bottom-style', 'border-left-style',
  'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color',
  'font-family', 'font-size', 'font-weight', 'font-style', 'line-height',
  'color', 'text-align', 'text-indent', 'text-transform', 'white-space', 'letter-spacing', 'word-spacing',
  'vertical-align', 'text-decoration-line', 'list-style-type',
  'background-color',
  'flex-direction', 'flex-wrap', 'justify-content', 'align-items', 'align-content', 'justify-items',
  'row-gap', 'column-gap',
  'grid-template-columns', 'grid-template-rows', 'grid-template-areas', 'grid-auto-flow',
  'grid-auto-columns', 'grid-auto-rows',
  'order', 'flex-grow', 'flex-shrink', 'flex-basis', 'align-self', 'justify-self',
  'grid-row-start', 'grid-row-end', 'grid-column-start', 'grid-column-end',
  'aspect-ratio', 'border-collapse', 'border-spacing', 'table-layout', 'caption-side',
  'content', 'counter-reset', 'counter-increment', 'counter-set', 'quotes',
  'list-style-position', 'overflow-wrap', 'word-break',
];

// The properties whose getComputedStyle value is a resolved value that
// differs from the computed value (CSSOM, "resolved values"): sizes, margins,
// paddings and offsets read the used value in px, line-height the used
// value unless it is normal, and min-width and min-height read auto as 0px
// on a box that is no flex or grid item. A pseudo-element row dumps them empty, as it
// has no computedStyleMap; grid-template-columns and grid-template-rows are
// dumped empty too when the pseudo-element is a grid container.
const RESOLVED = new Set([
  'width', 'height', 'min-width', 'min-height', 'top', 'right', 'bottom', 'left',
  'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
  'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
  'line-height',
]);
const GRID_RESOLVED = new Set(['grid-template-columns', 'grid-template-rows']);

// The counter properties, whose name and value pairs compare in any order.
const COUNTERS = new Set(['counter-reset', 'counter-increment', 'counter-set']);

function sortedPairs(value) {
  const words = value.trim().split(/\s+/);
  if (words.length % 2 !== 0) return value;
  const pairs = [];
  for (let k = 0; k < words.length; k += 2) pairs.push(words[k] + ' ' + words[k + 1]);
  return pairs.sort().join(' ');
}

const CHROMIUM = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PLAYWRIGHT = process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright';
const PAGE_URL = 'http://snowghost.test/page/index.html';
const BATCH = 5000;
const PASS_PERCENT = 99.0;

function usage(message) {
  if (message) process.stderr.write(`style_oracle: ${message}\n`);
  process.stderr.write(
    'usage: style_oracle.mjs dump PAGE.html [URL-SUFFIX=SHEET.css ...]\n' +
    '       style_oracle.mjs compare chromium.tsv snowghost.tsv\n');
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
    const refused = new Map();
    await page.route('**/*', (route) => {
      const url = route.request().url();
      if (url === PAGE_URL) {
        return route.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: pageBody });
      }
      const sheet = sheets.find((candidate) => url.endsWith(candidate.suffix));
      if (sheet) {
        process.stderr.write(`served ${sheet.suffix}: ${url}\n`);
        return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: sheet.body });
      }
      const type = route.request().resourceType();
      if (type === 'stylesheet' || type === 'document') process.stderr.write(`refused ${type} ${url}\n`);
      refused.set(type, (refused.get(type) || 0) + 1);
      return route.abort();
    });
    await page.goto(PAGE_URL, { waitUntil: 'load' });

    const count = await page.evaluate(() => {
      globalThis.__styleOracleElements = document.querySelectorAll('*');
      return globalThis.__styleOracleElements.length;
    });
    await writeOut(['index', 'name', ...PROPERTIES].join('\t') + '\n');
    for (let start = 0; start < count; start += BATCH) {
      const text = await page.evaluate(({ start, end, properties }) => {
        const escape = (value) => value.replace(/[\\\t\n\r]/g,
          (c) => (c === '\\' ? '\\\\' : c === '\t' ? '\\t' : c === '\n' ? '\\n' : '\\r'));
        const elements = globalThis.__styleOracleElements;
        const lines = [];
        for (let i = start; i < end; i++) {
          const element = elements[i];
          const map = element.computedStyleMap();
          const fields = [String(i), escape(element.localName)];
          for (const property of properties) {
            const value = map.get(property);
            fields.push(escape(value === null ? '' : value.toString()));
          }
          lines.push(fields.join('\t'));
        }
        return lines.join('\n') + '\n';
      }, { start, end: Math.min(start + BATCH, count), properties: PROPERTIES });
      await writeOut(text);
    }
    let pseudos = 0;
    for (let start = 0; start < count; start += BATCH) {
      const { text, rows } = await page.evaluate(({ start, end, properties, resolved, gridResolved }) => {
        const escape = (value) => value.replace(/[\\\t\n\r]/g,
          (c) => (c === '\\' ? '\\\\' : c === '\t' ? '\\t' : c === '\n' ? '\\n' : '\\r'));
        const elements = globalThis.__styleOracleElements;
        const lines = [];
        for (let i = start; i < end; i++) {
          for (const pseudo of ['::before', '::after']) {
            const style = getComputedStyle(elements[i], pseudo);
            if (style.content === 'none') continue;
            const grid = style.display === 'grid' || style.display === 'inline-grid';
            const fields = [String(i), pseudo];
            for (const property of properties) {
              const empty = resolved.includes(property) || (grid && gridResolved.includes(property));
              fields.push(empty ? '' : escape(style.getPropertyValue(property)));
            }
            lines.push(fields.join('\t'));
          }
        }
        return { text: lines.length ? lines.join('\n') + '\n' : '', rows: lines.length };
      }, { start, end: Math.min(start + BATCH, count), properties: PROPERTIES, resolved: [...RESOLVED], gridResolved: [...GRID_RESOLVED] });
      pseudos += rows;
      await writeOut(text);
    }
    const seconds = Number(process.hrtime.bigint() - started) / 1e9;
    const kinds = [...refused].map(([type, n]) => `${n} ${type}`).join(', ');
    process.stderr.write(`${basename(pagePath)}: ${count} elements and ${pseudos} pseudo-elements in ${seconds.toFixed(2)} s` +
      `; refused ${kinds || 'no requests'}\n`);
  } finally {
    await browser.close();
  }
}

// ---- compare ----

function unescape(field) {
  return field.replace(/\\(.)/g, (_, c) => (c === 't' ? '\t' : c === 'n' ? '\n' : c === 'r' ? '\r' : c));
}

const TOKEN = /\s+|([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)(%|[a-zA-Z]+)?|"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|([()\/,])|((?:[^\s()\/,"'\\]|\\.)+)/y;

// Splits a value into tokens: { n, unit } numbers, { s } quoted strings,
// { p } punctuation, { i } identifiers (lower-cased), { rgba } colors.
function tokenize(value) {
  const tokens = [];
  let at = 0;
  while (at < value.length) {
    TOKEN.lastIndex = at;
    const match = TOKEN.exec(value);
    if (match === null) break;
    at = TOKEN.lastIndex;
    if (match[1] !== undefined) tokens.push({ n: Number(match[1]), unit: (match[2] || '').toLowerCase() });
    else if (match[3] !== undefined) tokens.push({ s: match[3] });
    else if (match[4] !== undefined) tokens.push({ s: match[4] });
    else if (match[5] !== undefined) tokens.push({ p: match[5] });
    else if (match[6] !== undefined) tokens.push({ i: match[6].toLowerCase() });
  }
  if (at < value.length) tokens.push({ i: value.slice(at).toLowerCase() });
  return foldColors(tokens);
}

// Replaces rgb(...) and rgba(...) by one { rgba: [r, g, b, a] } token.
function foldColors(tokens) {
  const out = [];
  for (let k = 0; k < tokens.length; k++) {
    const t = tokens[k];
    if ((t.i === 'rgb' || t.i === 'rgba') && tokens[k + 1] && tokens[k + 1].p === '(') {
      const close = tokens.findIndex((u, j) => j > k + 1 && u.p === ')');
      const args = close < 0 ? null : tokens.slice(k + 2, close).filter((u) => u.p !== ',' && u.p !== '/');
      if (args && (args.length === 3 || args.length === 4) &&
          args.every((u) => u.n !== undefined && (u.unit === '' || u.unit === '%'))) {
        const channels = args.slice(0, 3).map((u) => (u.unit === '%' ? u.n * 2.55 : u.n));
        const alpha = args.length === 4 ? (args[3].unit === '%' ? args[3].n / 100 : args[3].n) : 1;
        out.push({ rgba: [...channels, alpha] });
        k = close;
        continue;
      }
    }
    out.push(t);
  }
  return out;
}

function tokenEqual(a, b) {
  if (a.n !== undefined) {
    if (b.n === undefined || a.unit !== b.unit) return false;
    const d = Math.abs(a.n - b.n);
    if (a.unit === 'px') return d <= 1 / 64 + 1e-4;
    return d <= 1e-4 * Math.max(1, Math.abs(a.n), Math.abs(b.n));
  }
  if (a.rgba) {
    if (!b.rgba) return false;
    for (let c = 0; c < 3; c++) if (Math.abs(a.rgba[c] - b.rgba[c]) > 0.5) return false;
    return Math.abs(a.rgba[3] - b.rgba[3]) <= 0.002;
  }
  if (a.s !== undefined) return a.s === b.s;
  if (a.p !== undefined) return a.p === b.p;
  return a.i === b.i;
}

// Pages repeat few distinct values, so each distinct pair is normalized once.
const verdicts = new Map();

function valuesEqual(a, b) {
  if (a === b) return true;
  const key = a + '\0' + b;
  let verdict = verdicts.get(key);
  if (verdict === undefined) {
    const ta = tokenize(a);
    const tb = tokenize(b);
    verdict = ta.length === tb.length && ta.every((t, k) => tokenEqual(t, tb[k]));
    verdicts.set(key, verdict);
  }
  return verdict;
}

function readTable(path) {
  let text;
  try {
    text = readFileSync(path, 'utf8');
  } catch (error) {
    usage(`cannot read ${path}: ${error.message}`);
  }
  const lines = text.split('\n');
  if (lines.length && lines[lines.length - 1] === '') lines.pop();
  return lines;
}

function compare(chromiumPath, snowghostPath) {
  const left = readTable(chromiumPath);
  const right = readTable(snowghostPath);
  const header = ['index', 'name', ...PROPERTIES].join('\t');
  for (const [path, lines] of [[chromiumPath, left], [snowghostPath, right]]) {
    if (lines[0] !== header) {
      const want = header.split('\t');
      const have = (lines[0] || '').split('\t');
      const column = want.findIndex((name, k) => have[k] !== name);
      const at = column < 0 ? want.length : column;
      console.log(`${path}: the header differs from the contract's at column ${at + 1}: ` +
        `expected ${JSON.stringify(want[at] ?? '')}, found ${JSON.stringify(have[at] ?? '')}`);
      return 1;
    }
  }
  if (left.length !== right.length) {
    console.log(`line count differs: ${chromiumPath} has ${left.length - 1}, ${snowghostPath} has ${right.length - 1}`);
  }
  const rowsL = [];
  const rowsR = [];
  const shared = Math.min(left.length, right.length);
  let elements = 0;
  for (let line = 1; line < shared; line++) {
    const l = left[line].split('\t');
    const r = right[line].split('\t');
    for (const [path, row] of [[chromiumPath, l], [snowghostPath, r]]) {
      if (row.length !== PROPERTIES.length + 2) {
        console.log(`${path}:${line + 1}: ${row.length} fields, expected ${PROPERTIES.length + 2}`);
        return 1;
      }
    }
    const pseudo = l[1].startsWith('::');
    const expected = pseudo ? l[0] : String(elements);
    if (l[0] !== r[0] || l[1] !== r[1] || l[0] !== expected || (pseudo && elements === 0)) {
      console.log(`first divergence at line ${line + 1}: ${chromiumPath} has ${l[0]} <${unescape(l[1])}>, ` +
        `${snowghostPath} has ${r[0]} <${unescape(r[1])}>` + (pseudo ? '' : ` (expected element ${elements})`));
      return 1;
    }
    if (!pseudo) {
      if (rowsL.length > elements) {
        console.log(`line ${line + 1}: element ${l[0]} follows a pseudo-element line`);
        return 1;
      }
      elements++;
    }
    rowsL.push(l);
    rowsR.push(r);
  }
  if (left.length !== right.length) {
    const longer = left.length > right.length ? [chromiumPath, left] : [snowghostPath, right];
    const extra = longer[1][shared].split('\t');
    console.log(`first divergence at line ${shared + 1}: only ${longer[0]} has ${extra[0]} <${unescape(extra[1] || '')}>`);
    return 1;
  }

  const lines = rowsL.length;
  let failed = 0;
  const width = Math.max(...PROPERTIES.map((p) => p.length));
  for (let p = 0; p < PROPERTIES.length; p++) {
    const column = p + 2;
    let matched = 0;
    let total = 0;
    const pairs = new Map();
    const counters = COUNTERS.has(PROPERTIES[p]);
    for (let row = 0; row < lines; row++) {
      if (row >= elements && rowsL[row][column] === '') continue;
      total++;
      const a = unescape(rowsL[row][column]);
      const b = unescape(rowsR[row][column]);
      const equal = counters ? valuesEqual(sortedPairs(a), sortedPairs(b)) : valuesEqual(a, b);
      if (equal) {
        matched++;
        continue;
      }
      const key = JSON.stringify([a, b]);
      const entry = pairs.get(key);
      if (entry) entry.count++;
      else pairs.set(key, { a, b, count: 1, index: rowsL[row][0], name: unescape(rowsL[row][1]) });
    }
    const percent = total === 0 ? 100 : (100 * matched) / total;
    if (percent < PASS_PERCENT) failed++;
    // Truncated, so a percentage just below the threshold never prints as 99.00.
    const shown = (Math.floor(percent * 100) / 100).toFixed(2);
    console.log(`${PROPERTIES[p].padEnd(width)}  ${String(matched).padStart(7)}/${total}  ${shown.padStart(6)}%` +
      (percent < PASS_PERCENT ? '  below 99.0%' : ''));
    if (matched < total) {
      const top = [...pairs.values()].sort((x, y) => y.count - x.count).slice(0, 5);
      for (const pair of top) {
        console.log(`    ${String(pair.count).padStart(7)}  chromium ${JSON.stringify(pair.a)}  snowghost ${JSON.stringify(pair.b)}` +
          `  e.g. element ${pair.index} <${pair.name}>`);
      }
    }
  }
  const counted = `${elements} elements and ${lines - elements} pseudo-elements`;
  console.log(failed === 0
    ? `every property matches on at least ${PASS_PERCENT.toFixed(1)}% of its cells on ${counted}`
    : `${failed} of ${PROPERTIES.length} properties below ${PASS_PERCENT.toFixed(1)}% on ${counted}`);
  return failed === 0 ? 0 : 1;
}

// ---- main ----

const [command, ...args] = process.argv.slice(2);
if (command === 'dump') {
  if (args.length < 1) usage();
  await dump(args[0], args.slice(1));
} else if (command === 'compare') {
  if (args.length !== 2) usage();
  process.exitCode = compare(args[0], args[1]);
} else {
  usage(command ? `unknown subcommand ${command}` : undefined);
}
