// Emits the markdown tables used in fanout.md from the three result files.
import { readFileSync } from 'node:fs';
const q = (a, p) => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
const f = (a, d = 0) => { const r = (x) => d ? x.toFixed(d) : String(x); return a.length ? `${r(q(a, .5))} / ${r(q(a, .9))} / ${r(Math.max(...a))}` : '-'; };
const isNoop = (r) => r.anyChanged === 0 && r.t.size + r.t.moved + r.t.shift + r.t.gone + r.t.appeared === 0;
const KINDS = ['text+word', 'text-word', 'text+sentence', 'class+', 'class-', 'color', 'width', 'font-size', 'display-none', 'insert-block', 'remove-block', 'container-color', 'container-font-size', 'container-width'];
for (const [name, file] of [['apollo11', 'apollo11.json'], ['html5', 'html5.json'], ['ecma262', 'ecma262.json']]) {
  const d = JSON.parse(readFileSync(file));
  const TOT = d.info.boxes + d.info.rendTexts;
  console.log(`\n#### ${name}: ${d.info.N} elements, ${d.info.boxes} boxes, ${d.info.rendTexts} rendered text nodes (eps ${(d.info.eps || 1 / 64).toFixed(3)} px)\n`);
  console.log('| edit kind | edits (no-op) | style changed | el size changed | el moved (abs) | move roots, parent-rel | move roots, sibling-end | text nodes resized | text nodes moved | dirty % abs | dirty % rel (parent) | dirty % rel (sibling-end) |');
  console.log('|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const k of KINDS) {
    const rs = d.results.filter((r) => r.kind === k); if (!rs.length) continue;
    const noop = rs.filter(isNoop).length;
    console.log(`| ${k} | ${rs.length} (${noop}) | ${f(rs.map((r) => r.styleChanged))} | ${f(rs.map((r) => r.e.size + r.e.shift + r.e.gone + r.e.appeared))} | ${f(rs.map((r) => r.moved.abs))} | ${f(rs.map((r) => r.moved.ctxRel))} | ${f(rs.map((r) => r.moved.sibRel))} | ${f(rs.map((r) => r.t.size + r.t.shift))} | ${f(rs.map((r) => r.t.moved))} | ${f(rs.map((r) => 100 * (r.anyChanged + r.t.size + r.t.shift + r.t.moved) / TOT), 2)} | ${f(rs.map((r) => 100 * (r.styleChanged + r.e.size + r.e.shift + r.e.gone + r.e.appeared + r.moved.ctxRel + r.t.size + r.t.shift + r.tmoved.ctxRel) / TOT), 2)} | ${f(rs.map((r) => 100 * (r.styleChanged + r.e.size + r.e.shift + r.e.gone + r.e.appeared + r.moved.sibRel + r.t.size + r.t.shift + r.tmoved.ctxRel) / TOT), 2)} |`);
  }
  const chk = d.results.filter((r) => r.verify); const bad = chk.filter((r) => r.verify.badBoxes || r.verify.badTexts || r.verify.badStyles);
  console.log(`\nreverts checked ${chk.length}, not restored ${bad.length}`);
}
