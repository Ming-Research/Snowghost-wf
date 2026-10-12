// Snapshots live web pages into static files the Chromium oracles load, and
// records Chromium's layout dump of each (research/investigations/testset).
//
//   node tests/testset/snapshot.mjs snapshot PAGES.txt OUTDIR [--only a,b] [--shadow flatten|declarative]
//   node tests/testset/snapshot.mjs compare OLD/manifest.tsv NEW/manifest.tsv
//
// snapshot loads each page of PAGES.txt (tests/testset/pages.txt) in headless
// Chromium with scripts running, 1280x720, device scale factor 1, en-US,
// time zone UTC, no geolocation, light colors and reduced motion; waits for
// the load, a network-idle period (best effort) and a fixed settle time,
// scrolls down to trigger lazy content and back, and serializes what the
// scripts left as one static HTML file that needs nothing else:
//
//   OUTDIR/NAME/page.html            the snapshot
//   OUTDIR/NAME/layout.chromium.tsv  `layout_oracle.mjs dump page.html` of it
//   OUTDIR/NAME/layout.chromium.2.tsv  a second dump of the same file, kept so a
//                                    difference between the two can be diffed
//   OUTDIR/NAME/dump.log, dump.2.log  the oracle's standard error of each dump
//   OUTDIR/NAME/live.png             the live page's first screen, for people
//   OUTDIR/NAME/failure.png          the first screen of a page that failed
//   OUTDIR/manifest.tsv              one row per page, see MANIFEST_COLUMNS
//
// What a snapshot is. It loads in tests/layout/layout_oracle.mjs and
// tests/css/style_oracle.mjs exactly as they load a page (scripts disabled,
// the page served at http://snowghost.test/page/index.html, every other
// request refused), so nothing in it may need the network or a script:
//
// - All CSS is inlined into <style> elements, in document order; the dump
//   command gets no URL-SUFFIX=SHEET.css mappings. Each <style> holds the
//   sheet's CSSOM rules (so rules inserted by script are kept), with @import
//   rules replaced by the imported sheets' rules wrapped in the @layer,
//   @supports and @media of the import. A <link rel=stylesheet> becomes a
//   <style> with the link's media attribute. Constructed (adopted) sheets
//   become <style> elements at the end of <body> (a shadow root's before its
//   content). A sheet the page cannot read (cross-origin without CORS) is
//   taken from the network response Chromium received for it.
// - Scripts, noscript elements, comments, <base>, <link>, meta
//   http-equiv/charset, event-handler attributes and iframe/object/embed
//   sources are removed; <meta charset=utf-8> is added. An iframe stays as
//   an empty box.
// - Every URL (CSS url(), src, href, poster, action, style attributes) is
//   made absolute against the page, except fragment-only references such as
//   url(#clip). A data: URL is replaced by an unreachable absolute URL: the
//   oracles refuse all requests but do not intercept data:, so a data: font
//   or image would load in Chromium and make the dump depend on something
//   the rest of the page does not get. srcset is dropped (src is set from
//   currentSrc when the image had none), so no image or font loads.
// - Form state is written back to attributes; hidden input values are
//   cleared (CSRF tokens would change on every fetch).
// - Shadow DOM, --shadow flatten (the default): each open shadow root is
//   replaced by its content in the host, a <slot> holding the nodes assigned
//   to it. The oracles list elements with querySelectorAll('*'), which does
//   not enter shadow roots, so a page that keeps shadow DOM would have
//   boxes no oracle line names; flattening makes every box visible to them.
//   Shadow-scoped CSS becomes global (`:host` then matches nothing), so
//   styling of such a page can differ from the live page. --shadow
//   declarative keeps the roots as <template shadowrootmode> (Element.getHTML
//   with every open root serializable) and the page as Chromium renders it,
//   but the oracles then omit those elements. Closed shadow roots cannot be
//   read in either mode. Hosts counted are in the manifest.
//
// A page that shows a bot wall or error is recorded as failed, not worked
// around: a main document status of 400 or more, a navigation failure, a
// document with fewer than 100 elements, or a challenge phrase in a short
// page. No user agent, header or timing is changed to avoid detection.
//
// The manifest is TSV with a header: name, url, fetched_at, status (ok or
// failed), html_sha256, html_bytes, dump_sha256, failure_reason, then
// final_url, http_status, elements (of the snapshot), shadow_hosts,
// dump_repeat (same or DIFFERENT: the oracle dumped the snapshot a second
// time in the same run, which separates oracle noise from page change; when it
// differs the notes give the number of differing lines and the first one) and
// notes.
//
// compare reads two manifests (the second run is made a day later for the
// stability check) and prints, per page of either, a TSV row: status, whether
// the snapshot (html) and the dump are byte-identical, a verdict (stable; oracle
// noise, the same html with a different dump; page changed, a different html),
// the dump_repeat of each side and details (byte and element counts of a
// changed html; how many dump lines differ and where the first is, when both
// dumps are beside their manifests). A page in one manifest only is reported
// as such and is neither an error nor counted in the exit status; a page that
// failed in both is reported with both reasons. Exit status of compare: 0 when
// every page that is ok in both has the same html and dump and no page changed
// status, 1 otherwise, 2 on a usage error.
//
// CHROMIUM and PLAYWRIGHT override the browser binary and the playwright
// module's path, the same variables and defaults as the oracles, so the
// snapshot and the dump use one browser.

import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const CHROMIUM = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const PLAYWRIGHT = process.env.PLAYWRIGHT || '/opt/node22/lib/node_modules/playwright';
const LAYOUT_ORACLE = resolve(dirname(fileURLToPath(import.meta.url)), '../layout/layout_oracle.mjs');

const NAVIGATION_TIMEOUT = 60000;
const IDLE_TIMEOUT = 20000;
const DEFAULT_SETTLE = 5000;
const DEFAULT_SCROLL = 12;
const SCROLL_PAUSE = 400;
const MIN_ELEMENTS = 100;
const SHORT_TEXT = 1500;
const MANIFEST_COLUMNS = ['name', 'url', 'fetched_at', 'status', 'html_sha256', 'html_bytes', 'dump_sha256',
  'failure_reason', 'final_url', 'http_status', 'elements', 'shadow_hosts', 'dump_repeat', 'notes'];

// Phrases of bot walls, CAPTCHAs and block pages. One counts only on a page with
// little text, since ordinary pages mention captchas in forms and footers.
const CHALLENGE_PHRASES = [
  'just a moment', 'attention required', 'access denied', 'verify you are human', 'verifying you are human',
  'are you a robot', 'not a robot', 'captcha', 'unusual traffic', 'pardon our interruption', 'request blocked',
  'press & hold', 'press and hold', 'security check', 'checking your browser', 'enable javascript and cookies',
  'automated access', 'sorry, you have been blocked', 'enter the characters you see below', 'bot detection',
  'robot or human', 'request unsuccessful', 'incapsula',
];

function usage(message) {
  if (message) process.stderr.write(`snapshot: ${message}\n`);
  process.stderr.write(
    'usage: snapshot.mjs snapshot PAGES.txt OUTDIR [--only a,b] [--shadow flatten|declarative]\n' +
    '       snapshot.mjs compare OLD/manifest.tsv NEW/manifest.tsv\n');
  process.exit(2);
}

const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const oneLine = (text) => String(text).replace(/[\t\r\n]+/g, ' ').trim();

// ---- the page list ----

function readPages(path) {
  const pages = [];
  readFileSync(path, 'utf8').split('\n').forEach((line, n) => {
    const text = line.trim();
    if (text === '' || text.startsWith('#')) return;
    const [name, url, ...rest] = text.split(/\s+/);
    if (!/^[a-z0-9][a-z0-9-]*$/.test(name || '') || !/^https?:\/\//.test(url || '')) usage(`${path}:${n + 1}: expected NAME URL, got ${text}`);
    if (pages.some((page) => page.name === name)) usage(`${path}:${n + 1}: duplicate name ${name}`);
    const options = { scroll: DEFAULT_SCROLL, settle: DEFAULT_SETTLE };
    for (const option of rest) {
      const match = /^(scroll|settle)=(\d+)$/.exec(option);
      if (!match) usage(`${path}:${n + 1}: unknown option ${option}`);
      options[match[1]] = Number(match[2]);
    }
    pages.push({ name, url, ...options });
  });
  return pages;
}

// ---- the serializer, run inside the page ----

// Returns { html, elements, shadowHosts, notes }. The page is changed in
// place, so it runs last, after the probe that detects a block page.
async function serializeInPage({ cssResponses, shadowMode }) {
  const REMOVED = 'http://snowghost.test/removed-data-uri';
  const notes = [];
  const URL_PATTERN = /url\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|([^)\s"'][^)]*?))\s*\)/gi;

  const absolute = (value, base) => {
    const text = value.trim();
    if (text === '' || text.startsWith('#')) return value;
    if (/^data:/i.test(text)) return REMOVED;
    if (/^javascript:/i.test(text)) return '#';
    try {
      return new URL(text, base).href;
    } catch {
      return value;
    }
  };
  const rewriteUrls = (css, base) => css.replace(URL_PATTERN, (match, double, single, bare) => {
    const raw = double ?? single ?? bare;
    const fixed = absolute(raw, base);
    return fixed === raw ? match : `url("${fixed.replace(/["\\\n]/g, encodeURIComponent)}")`;
  });

  // The composed tree: roots to look through, the style nodes, the shadow hosts.
  const styleNodes = [];
  const hosts = [];
  const scan = (root) => {
    for (const element of root.querySelectorAll('style, link[rel~="stylesheet" i]')) styleNodes.push(element);
    for (const element of root.querySelectorAll('*')) {
      if (element.shadowRoot) {
        hosts.push(element);
        scan(element.shadowRoot);
      }
    }
  };
  scan(document);
  const assignments = hosts.map((host) => [...host.shadowRoot.querySelectorAll('slot')].map(
    (slot) => [slot, slot.assignedNodes({ flatten: false })]));

  // CSS text of a sheet, @import rules replaced by the sheets they import.
  const wrapImport = (inner, { layer, supports, media }) => {
    let out = inner;
    if (media && media.trim() !== '' && media.trim() !== 'all') out = `@media ${media} {\n${out}\n}`;
    if (supports) {
      const condition = /^(\(|not\b|selector\()/i.test(supports.trim()) ? supports : `(${supports})`;
      out = `@supports ${condition} {\n${out}\n}`;
    }
    if (layer !== null && layer !== undefined) out = layer === '' ? `@layer {\n${out}\n}` : `@layer ${layer} {\n${out}\n}`;
    return out;
  };
  const rawText = (href, depth) => {
    const text = cssResponses[href];
    if (text === undefined) {
      notes.push(`css-missing:${href}`);
      return `/* snapshot: no text for ${href} */`;
    }
    notes.push('css-from-response');
    return inlineRawImports(rewriteUrls(text, href), href, depth);
  };
  const inlineRawImports = (text, base, depth) => {
    if (depth > 8) return text;
    const pattern = /@import\s+(?:url\(\s*(?:"([^"]+)"|'([^']+)'|([^)\s]+))\s*\)|"([^"]+)"|'([^']+)')\s*([^;]*);/gi;
    return text.replace(pattern, (match, a, b, c, d, e, tail) => {
      const target = absolute(a ?? b ?? c ?? d ?? e, base);
      const layer = /\blayer\(\s*([^)]*?)\s*\)/i.exec(tail);
      const supports = /\bsupports\(((?:[^()]|\([^()]*\))*)\)/i.exec(tail);
      const bareLayer = !layer && /(^|\s)layer(\s|$)/i.test(tail);
      const media = tail.replace(/\blayer\([^)]*\)/i, '').replace(/\bsupports\((?:[^()]|\([^()]*\))*\)/i, '').replace(/(^|\s)layer(\s|$)/i, ' ').trim();
      return wrapImport(rawText(target, depth + 1), { layer: layer ? layer[1] : bareLayer ? '' : null, supports: supports ? supports[1] : null, media });
    });
  };
  const sheetText = (sheet, depth) => {
    let rules;
    try {
      rules = sheet.cssRules;
    } catch {
      return sheet.href ? rawText(sheet.href, depth) : '';
    }
    const base = sheet.href || document.baseURI;
    const parts = [];
    for (const rule of rules) {
      if (rule.type === CSSRule.IMPORT_RULE) {
        let inner;
        if (depth <= 8 && rule.styleSheet) inner = sheetText(rule.styleSheet, depth + 1);
        else inner = rule.href ? rawText(rule.href, depth + 1) : '';
        parts.push(wrapImport(inner, { layer: rule.layerName ?? null, supports: rule.supportsText ?? null, media: rule.media.mediaText }));
      } else {
        parts.push(rewriteUrls(rule.cssText, base));
      }
    }
    return parts.join('\n');
  };

  // Phase 1: read every sheet before anything changes.
  const planned = styleNodes.map((node) => {
    const sheet = node.sheet;
    if (!sheet || sheet.disabled) return { node, text: null };
    return { node, text: sheetText(sheet, 0) };
  });
  const adopted = [document, ...hosts.map((host) => host.shadowRoot)].map((root) => ({
    root,
    texts: (root.adoptedStyleSheets || []).map((sheet) => sheetText(sheet, 0)),
  }));

  // Phase 2: write them back as <style> elements.
  for (const { node, text } of planned) {
    if (text === null) {
      node.remove();
      continue;
    }
    if (node.localName === 'link') {
      const style = document.createElement('style');
      if (node.media) style.setAttribute('media', node.media);
      style.setAttribute('data-source', node.href);
      style.textContent = text;
      node.replaceWith(style);
    } else {
      node.textContent = text;
    }
  }
  for (const { root, texts } of adopted) {
    if (texts.length === 0) continue;
    const style = document.createElement('style');
    style.setAttribute('data-source', 'adopted');
    style.textContent = texts.join('\n');
    if (root === document) (document.body || document.documentElement).append(style);
    else root.prepend(style);
  }

  // Phase 3: shadow roots.
  if (shadowMode === 'flatten') {
    hosts.forEach((host, i) => {
      for (const [slot, nodes] of assignments[i]) if (nodes.length > 0) slot.replaceChildren(...nodes);
      host.replaceChildren(...host.shadowRoot.childNodes);
    });
  }
  const everything = () => {
    const found = [...document.querySelectorAll('*')];
    if (shadowMode !== 'flatten') for (const host of hosts) found.push(...host.shadowRoot.querySelectorAll('*'));
    return found;
  };
  const roots = shadowMode === 'flatten' ? [document] : [document, ...hosts.map((host) => host.shadowRoot)];

  // Phase 4: remove what the oracles must not run, load or follow.
  for (const root of roots) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
    const comments = [];
    for (let node = walker.nextNode(); node; node = walker.nextNode()) comments.push(node);
    for (const comment of comments) comment.remove();
  }
  for (const element of everything()) {
    const name = element.localName;
    if (name === 'script' || name === 'noscript' || name === 'base' || name === 'link' ||
        (name === 'meta' && (element.hasAttribute('http-equiv') || element.hasAttribute('charset')))) {
      element.remove();
    }
  }
  const URL_ATTRIBUTES = ['src', 'href', 'poster', 'data', 'action', 'formaction', 'xlink:href'];
  for (const element of everything()) {
    const name = element.localName;
    if (name === 'img' && !element.getAttribute('src') && element.currentSrc) element.setAttribute('src', element.currentSrc);
    if (name === 'iframe' || name === 'frame') {
      element.removeAttribute('src');
      element.removeAttribute('srcdoc');
      element.replaceChildren();
    }
    if (name === 'object' || name === 'embed') {
      element.removeAttribute('data');
      element.removeAttribute('src');
    }
    const base = element.baseURI;
    for (const attribute of [...element.attributes]) {
      const attributeName = attribute.name;
      if (attributeName.startsWith('on') || attributeName === 'nonce' || attributeName === 'integrity' ||
          attributeName === 'srcset' || attributeName === 'imagesrcset') {
        element.removeAttribute(attributeName);
      } else if (URL_ATTRIBUTES.includes(attributeName) && attribute.value !== '') {
        element.setAttribute(attributeName, absolute(attribute.value, base));
      } else if (attributeName === 'style' && attribute.value.includes('url(')) {
        element.setAttribute('style', rewriteUrls(attribute.value, base));
      }
    }
    // Form state, which lives in properties, written back as attributes.
    if (name === 'input') {
      const type = element.type;
      if (type === 'checkbox' || type === 'radio') element.toggleAttribute('checked', element.checked);
      else if (type === 'hidden') element.setAttribute('value', '');
      else if (!['submit', 'button', 'reset', 'image', 'file', 'password'].includes(type) &&
               element.value !== (element.getAttribute('value') ?? '')) element.setAttribute('value', element.value);
    } else if (name === 'textarea') {
      element.textContent = element.value;
    } else if (name === 'option') {
      element.toggleAttribute('selected', element.selected);
    }
  }

  // Phase 5: serialize.
  const head = document.head || document.documentElement.insertBefore(document.createElement('head'), document.documentElement.firstChild);
  const charset = document.createElement('meta');
  charset.setAttribute('charset', 'utf-8');
  head.prepend(charset);
  const type = document.doctype;
  let doctype = '';
  if (type) {
    doctype = `<!DOCTYPE ${type.name}${type.publicId ? ` PUBLIC "${type.publicId}"` : type.systemId ? ' SYSTEM' : ''}${type.systemId ? ` "${type.systemId}"` : ''}>\n`;
  }
  const body = shadowMode === 'flatten'
    ? document.documentElement.outerHTML
    : document.documentElement.getHTML({ serializableShadowRoots: true, shadowRoots: hosts.map((host) => host.shadowRoot) });
  const html = shadowMode === 'flatten' ? doctype + body + '\n' : `${doctype}<html${[...document.documentElement.attributes].map((a) => ` ${a.name}="${a.value.replace(/"/g, '&quot;')}"`).join('')}>${body}</html>\n`;
  return { html, elements: document.querySelectorAll('*').length, shadowHosts: hosts.length, notes: [...new Set(notes)] };
}

// ---- one page ----

function blockReason(status, probe) {
  if (status !== null && status >= 400) return `main document status ${status}`;
  if (probe.elements < MIN_ELEMENTS) return `tiny document: ${probe.elements} elements (title "${oneLine(probe.title).slice(0, 80)}")`;
  if (probe.text.length < SHORT_TEXT) {
    const haystack = `${probe.title}\n${probe.text}`.toLowerCase();
    const phrase = CHALLENGE_PHRASES.find((candidate) => haystack.includes(candidate));
    if (phrase) return `challenge phrase "${phrase}" on a short page (title "${oneLine(probe.title).slice(0, 80)}")`;
  }
  return null;
}

async function scrollThrough(page, steps) {
  let atBottom = 0;
  for (let i = 0; i < steps; i++) {
    const bottom = await page.evaluate(() => {
      window.scrollBy(0, 720);
      return window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 1;
    });
    await sleep(SCROLL_PAUSE);
    atBottom = bottom ? atBottom + 1 : 0;
    if (atBottom >= 2) break;
  }
  await page.evaluate(() => window.scrollTo(0, 0));
}

function runDump(htmlPath, dumpPath, logPath) {
  const out = openSync(dumpPath, 'w');
  let result;
  try {
    result = spawnSync(process.execPath, [LAYOUT_ORACLE, 'dump', htmlPath], { stdio: ['ignore', out, 'pipe'], timeout: 600000 });
  } finally {
    closeSync(out);
  }
  const log = result.stderr ? result.stderr.toString() : '';
  if (logPath) writeFileSync(logPath, log);
  return { ok: result.status === 0, status: result.status, log };
}

async function snapshotPage(browser, entry, outDir, shadowMode) {
  const dir = join(outDir, entry.name);
  mkdirSync(dir, { recursive: true });
  const row = Object.fromEntries(MANIFEST_COLUMNS.map((column) => [column, '']));
  Object.assign(row, { name: entry.name, url: entry.url, fetched_at: new Date().toISOString(), status: 'failed' });
  const notes = [];
  const context = await browser.newContext({
    javaScriptEnabled: true,
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
    reducedMotion: 'reduce',
    locale: 'en-US',
    timezoneId: 'UTC',
    permissions: [],
  });
  const page = await context.newPage();
  const cssResponses = {};
  const reading = [];
  page.on('response', (response) => {
    if (response.request().resourceType() !== 'stylesheet') return;
    reading.push(response.text().then((text) => {
      const urls = [response.url()];
      for (let request = response.request(); request; request = request.redirectedFrom()) urls.push(request.url());
      for (const url of urls) cssResponses[url] = text;
    }, () => {}));
  });
  try {
    let response;
    try {
      response = await page.goto(entry.url, { waitUntil: 'load', timeout: NAVIGATION_TIMEOUT });
    } catch (error) {
      row.failure_reason = `navigation failed: ${oneLine(error.message).slice(0, 200)}`;
      return row;
    }
    row.http_status = response ? String(response.status()) : '';
    if (response && response.status() !== 200) notes.push(`status ${response.status()}`);
    await page.waitForLoadState('networkidle', { timeout: IDLE_TIMEOUT }).catch(() => notes.push('networkidle-timeout'));
    await sleep(entry.settle);
    if (entry.scroll > 0) {
      await scrollThrough(page, entry.scroll);
      await sleep(entry.settle / 2);
      await page.waitForLoadState('networkidle', { timeout: IDLE_TIMEOUT }).catch(() => notes.push('networkidle-timeout-after-scroll'));
    }
    row.final_url = page.url();
    const probe = await page.evaluate(() => ({
      title: document.title,
      elements: document.querySelectorAll('*').length,
      text: document.body ? document.body.innerText.slice(0, 20000) : '',
    }));
    row.elements = String(probe.elements);
    const reason = blockReason(response ? response.status() : null, probe);
    if (reason) {
      row.failure_reason = reason;
      await page.screenshot({ path: join(dir, 'failure.png') }).catch(() => {});
      return row;
    }
    await page.screenshot({ path: join(dir, 'live.png') }).catch(() => {});
    await Promise.allSettled(reading);
    let captured;
    try {
      captured = await page.evaluate(serializeInPage, { cssResponses, shadowMode });
    } catch (error) {
      row.failure_reason = `serialization failed: ${oneLine(error.message).slice(0, 200)}`;
      return row;
    }
    const bytes = Buffer.from(captured.html, 'utf8');
    const htmlPath = join(dir, 'page.html');
    writeFileSync(htmlPath, bytes);
    Object.assign(row, { html_sha256: sha256(bytes), html_bytes: String(bytes.length), elements: String(captured.elements), shadow_hosts: String(captured.shadowHosts) });
    notes.push(...captured.notes.map((note) => (note.length > 120 ? `${note.slice(0, 120)}...` : note)));
  } finally {
    await context.close();
    row.notes = oneLine(notes.join('; '));
  }

  // The oracle's dump, twice, both kept: the second separates the oracle's own
  // noise from a change of the page, and a difference can be diffed.
  const dumpPath = join(dir, 'layout.chromium.tsv');
  const first = runDump(join(dir, 'page.html'), dumpPath, join(dir, 'dump.log'));
  if (!first.ok) {
    row.failure_reason = `layout dump failed (exit ${first.status}): ${oneLine(first.log).slice(0, 200)}`;
    return row;
  }
  const againPath = join(dir, 'layout.chromium.2.tsv');
  const second = runDump(join(dir, 'page.html'), againPath, join(dir, 'dump.2.log'));
  const firstHash = sha256(readFileSync(dumpPath));
  row.dump_sha256 = firstHash;
  const same = second.ok && sha256(readFileSync(againPath)) === firstHash;
  row.dump_repeat = same ? 'same' : 'DIFFERENT';
  if (!same) {
    const found = second.ok ? differingLines(dumpPath, againPath) : null;
    row.notes = oneLine(`${row.notes}; dump-repeat: ${found ? `${found.differing} of ${found.lines} lines differ, first at line ${found.first.line}: ${found.first.a} | ${found.first.b}` : `second dump failed (exit ${second.status})`}`);
  }
  row.status = 'ok';
  return row;
}

async function snapshot(listPath, outDir, only, shadowMode) {
  let pages = readPages(listPath);
  if (only) {
    for (const name of only) if (!pages.some((page) => page.name === name)) usage(`--only names ${name}, which ${listPath} does not list`);
    pages = pages.filter((page) => only.includes(page.name));
  }
  mkdirSync(outDir, { recursive: true });
  const require = createRequire(import.meta.url);
  const { chromium } = require(PLAYWRIGHT);
  const browser = await chromium.launch({ executablePath: CHROMIUM, headless: true });
  const rows = [];
  try {
    for (const entry of pages) {
      const started = Date.now();
      let row;
      try {
        row = await snapshotPage(browser, entry, outDir, shadowMode);
      } catch (error) {
        row = Object.fromEntries(MANIFEST_COLUMNS.map((column) => [column, '']));
        Object.assign(row, { name: entry.name, url: entry.url, fetched_at: new Date().toISOString(), status: 'failed', failure_reason: `unexpected: ${oneLine(error.stack || error.message).slice(0, 300)}` });
      }
      rows.push(row);
      process.stderr.write(`${row.name}: ${row.status}${row.failure_reason ? ` (${row.failure_reason})` : ''}, ${row.elements || 0} elements, ${((Date.now() - started) / 1000).toFixed(1)} s\n`);
      writeManifest(outDir, rows);
    }
  } finally {
    await browser.close();
  }
  const failed = rows.filter((row) => row.status !== 'ok');
  process.stderr.write(`${rows.length - failed.length} of ${rows.length} pages ok; failed: ${failed.map((row) => row.name).join(', ') || 'none'}\n`);
}

function writeManifest(outDir, rows) {
  const lines = [MANIFEST_COLUMNS.join('\t'), ...rows.map((row) => MANIFEST_COLUMNS.map((column) => oneLine(row[column])).join('\t'))];
  writeFileSync(join(outDir, 'manifest.tsv'), lines.join('\n') + '\n');
}

// ---- compare ----

function readManifest(path) {
  let text;
  try {
    text = readFileSync(path, 'utf8');
  } catch (error) {
    usage(`cannot read ${path}: ${error.message}`);
  }
  const lines = text.split('\n').filter((line) => line !== '');
  const header = lines.shift().split('\t');
  for (const column of MANIFEST_COLUMNS.slice(0, 8)) if (!header.includes(column)) usage(`${path}: no ${column} column`);
  const rows = new Map();
  for (const line of lines) {
    const fields = line.split('\t');
    rows.set(fields[0], Object.fromEntries(header.map((column, i) => [column, fields[i] ?? ''])));
  }
  return { rows, dir: dirname(resolve(path)) };
}

// How many lines of two dump files differ (a length difference counts its extra
// lines), of how many lines each, and the first differing line, cut short.
function differingLines(a, b) {
  if (!existsSync(a) || !existsSync(b)) return null;
  const left = readFileSync(a, 'utf8').split('\n');
  const right = readFileSync(b, 'utf8').split('\n');
  let differing = Math.abs(left.length - right.length);
  let first = null;
  for (let i = 0; i < Math.max(left.length, right.length); i++) {
    if (i < Math.min(left.length, right.length) && left[i] === right[i]) continue;
    if (i < Math.min(left.length, right.length)) differing++;
    first = first || { line: i + 1, a: (left[i] ?? '(none)').slice(0, 120), b: (right[i] ?? '(none)').slice(0, 120) };
  }
  return { differing, lines: `${left.length - 1}/${right.length - 1}`, first };
}

function compare(oldPath, newPath) {
  const before = readManifest(oldPath);
  const after = readManifest(newPath);
  const names = [...before.rows.keys(), ...[...after.rows.keys()].filter((name) => !before.rows.has(name))];
  const count = { stable: 0, noise: 0, page: 0, status: 0, onlyOld: 0, onlyNew: 0, failedBoth: 0 };
  const line = (...fields) => process.stdout.write(fields.join('\t') + '\n');
  // verdict: stable (html and dump identical); oracle noise (html identical, dump
  // different: the dump of one input changed); page changed (html different).
  line('page', 'status', 'html', 'dump', 'verdict', 'dump_repeat old/new', 'detail');
  for (const name of names) {
    const a = before.rows.get(name);
    const b = after.rows.get(name);
    if (!a || !b) {
      count[a ? 'onlyOld' : 'onlyNew']++;
      line(name, a ? 'only in old' : 'only in new', '', '', '', '', (a || b).url);
      continue;
    }
    const repeat = `${a.dump_repeat || '-'}/${b.dump_repeat || '-'}`;
    if (a.status !== 'ok' || b.status !== 'ok') {
      if (a.status === b.status) count.failedBoth++;
      else count.status++;
      line(name, a.status === b.status ? `${a.status} in both` : `${a.status} -> ${b.status}`, '', '', '', repeat, `${a.failure_reason || ''} | ${b.failure_reason || ''}`);
      continue;
    }
    const sameHtml = a.html_sha256 === b.html_sha256;
    const sameDump = a.dump_sha256 === b.dump_sha256;
    const verdict = sameHtml && sameDump ? 'stable' : sameHtml ? 'oracle noise' : 'page changed';
    count[verdict === 'stable' ? 'stable' : verdict === 'oracle noise' ? 'noise' : 'page']++;
    const details = [];
    if (!sameHtml) details.push(`html bytes ${a.html_bytes}/${b.html_bytes}, elements ${a.elements}/${b.elements}`);
    if (!sameDump) {
      const found = differingLines(join(before.dir, name, 'layout.chromium.tsv'), join(after.dir, name, 'layout.chromium.tsv'));
      details.push(found ? `${found.differing} dump lines differ (of ${found.lines}), first at line ${found.first.line}` : 'dump files not beside the manifests');
    }
    line(name, 'ok', sameHtml ? 'identical' : 'different', sameDump ? 'identical' : 'DIFFERENT', verdict, repeat, details.join('; '));
  }
  process.stdout.write(`${count.stable} pages stable, ${count.noise} with the same html and a different dump (oracle noise), ${count.page} with changed html, ` +
    `${count.status} that changed status, ${count.failedBoth} failed in both, ${count.onlyOld} only in the old manifest, ${count.onlyNew} only in the new\n`);
  process.exit(count.noise === 0 && count.page === 0 && count.status === 0 ? 0 : 1);
}

// ---- main ----

const [command, ...rest] = process.argv.slice(2);
if (command === 'snapshot' && rest.length >= 2) {
  let only = null;
  let shadowMode = 'flatten';
  for (let i = 2; i < rest.length; i += 2) {
    if (rest[i] === '--only' && rest[i + 1]) only = rest[i + 1].split(',').filter((name) => name !== '');
    else if (rest[i] === '--shadow' && ['flatten', 'declarative'].includes(rest[i + 1])) shadowMode = rest[i + 1];
    else usage(`unknown argument ${rest[i]}`);
  }
  await snapshot(rest[0], rest[1], only, shadowMode);
} else if (command === 'compare' && rest.length === 2) {
  compare(rest[0], rest[1]);
} else {
  usage();
}
