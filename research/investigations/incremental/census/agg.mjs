import { readFileSync } from 'node:fs';
const pages = process.argv.slice(2);
const q = (a, p) => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
const fmt = (a) => `${q(a, .5)}/${q(a, .9)}/${a.length ? Math.max(...a) : 0}`;
const sum = (a) => a.reduce((x, y) => x + y, 0);
const isNoop = (r) => r.anyChanged === 0 && r.t.size + r.t.moved + r.t.shift + r.t.gone + r.t.appeared === 0;
let TOT = 1;
const pct = (n) => Math.round(1e4 * n / TOT) / 100;
const rows = {
  'style': (r) => r.styleChanged,
  'el size': (r) => r.e.size,
  'el shift': (r) => r.e.shift,
  'el gone/new': (r) => r.e.gone + r.e.appeared,
  'el moved': (r) => r.moved.abs,
  'mv roots(ctx)': (r) => r.moved.ctxRel,
  'mv roots(sib)': (r) => r.moved.sibRel,
  'blk moved': (r) => r.moved.absBlock,
  'blk roots(par)': (r) => r.moved.parentRelBlock,
  'blk roots(sib)': (r) => r.moved.sibRelBlock,
  'txt size': (r) => r.t.size,
  'txt shift': (r) => r.t.shift,
  'txt moved': (r) => r.t.moved,
  'txt roots(ctx)': (r) => r.tmoved.ctxRel,
  'own': (r) => r.own,
  'any el': (r) => r.anyChanged,
  'abs-dirty%': (r) => pct(r.anyChanged + r.t.size + r.t.shift + r.t.moved),
  'rel-dirty%': (r) => pct(r.styleChanged + r.e.size + r.e.shift + r.e.gone + r.e.appeared + r.moved.ctxRel + r.t.size + r.t.shift + r.tmoved.ctxRel),
};
for (const f of pages) {
  const d = JSON.parse(readFileSync(f));
  console.log(`\n### ${f}: ${d.info.N} elements, ${d.info.boxes} boxes, ${d.info.rendTexts} rendered text nodes; edits ${d.results.length}`);
  TOT = d.info.boxes + d.info.rendTexts;
  const kinds = [...new Set(d.results.map((r) => r.kind))];
  for (const [label, filt] of [['ALL edits', () => true], ['NON-NOOP edits', (r) => !isNoop(r)]]) {
    console.log(`\n${label}: kind | n | ` + Object.keys(rows).join(' | ') + '   (median/p90/max)');
    for (const k of kinds) {
      const rs = d.results.filter((r) => r.kind === k && filt(r));
      if (!rs.length) { console.log(`${k} | 0`); continue; }
      console.log(`${k} | ${rs.length} | ` + Object.values(rows).map((fn) => fmt(rs.map(fn))).join(' | '));
    }
  }
  console.log('\nno-op share and explained fractions per kind (sum over non-noop edits):');
  for (const k of kinds) {
    const all = d.results.filter((r) => r.kind === k); const rs = all.filter((r) => !isNoop(r));
    const mv = sum(rs.map((r) => r.moved.abs)), ctx = sum(rs.map((r) => r.moved.ctxRel)), sib = sum(rs.map((r) => r.moved.sibRel));
    const bm = sum(rs.map((r) => r.moved.absBlock)), bp = sum(rs.map((r) => r.moved.parentRelBlock)), bs = sum(rs.map((r) => r.moved.sibRelBlock));
    const tm = sum(rs.map((r) => r.tmoved.abs)), tc = sum(rs.map((r) => r.tmoved.ctxRel));
    const own = sum(rs.map((r) => r.own)), anyc = sum(rs.map((r) => r.anyChanged + r.t.size + r.t.shift + r.t.moved));
    const pc = (a, b) => b ? Math.round(100 * a / b) + '%' : '-';
    console.log(`${k}: noop ${all.length - rs.length}/${all.length}; moved ${mv} -> ctx-roots ${ctx} (${pc(ctx, mv)} unexplained), sib-roots ${sib} (${pc(sib, mv)}); block-moved ${bm} -> par-roots ${bp}, sib-roots ${bs}; text-moved ${tm} -> ctx-roots ${tc}; own ${own} vs changed(el+txt) ${anyc}`);
  }
  console.log('\ncauses (sum over edits of each kind): wCause | hCause | tCause');
  for (const k of kinds) {
    const rs = d.results.filter((r) => r.kind === k);
    const agg = (key) => { const o = {}; for (const r of rs) for (const [a, b] of Object.entries(r[key])) o[a] = (o[a] || 0) + b; return JSON.stringify(o); };
    console.log(`${k}: W ${agg('wCause')} H ${agg('hCause')} T ${agg('tCause')}`);
  }
  console.log('\nresidual "other" display pairs (sum over all edits): wOther / hOther / tOther');
  const oth = (key) => { const o = {}; for (const r of d.results) for (const [a, b] of r[key]) o[a] = (o[a] || 0) + b; return JSON.stringify(Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 8)); };
  console.log('W', oth('wOther')); console.log('H', oth('hOther')); console.log('T', oth('tOther'));
  console.log('\ntop 8 edits by (changed el + text size/shift/moved):');
  const tot = (r) => r.anyChanged + r.t.size + r.t.shift + r.t.moved;
  for (const r of d.results.slice().sort((a, b) => tot(b) - tot(a)).slice(0, 8)) {
    console.log(`${tot(r)} [${r.kind}] ${r.descr} | style ${r.styleChanged} size ${r.e.size} shift ${r.e.shift} gone/new ${r.e.gone + r.e.appeared} moved ${r.moved.abs} (ctxRoots ${r.moved.ctxRel}, sibRoots ${r.moved.sibRel}) txtsize ${r.t.size + r.t.shift} txtmoved ${r.t.moved} | W ${JSON.stringify(r.wCause)} H ${JSON.stringify(r.hCause)} T ${JSON.stringify(r.tCause)} wOther ${JSON.stringify(r.wOther)} hOther ${JSON.stringify(r.hOther)} tOther ${JSON.stringify(r.tOther)}`);
  }
  const chk = d.results.filter((r) => r.verify);
  const bad = chk.filter((r) => r.verify.badBoxes || r.verify.badTexts || r.verify.badStyles);
  console.log(`verify: ${chk.length} reverts checked, ${bad.length} not restored`);
}
