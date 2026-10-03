import { readFileSync } from 'node:fs';
const q = (a, p) => { if (!a.length) return 0; const s = a.slice().sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
const fmt = (a) => `${q(a, .5)}/${q(a, .9)}/${a.length ? Math.max(...a) : 0}`;
for (const f of process.argv.slice(2)) {
  const d = JSON.parse(readFileSync(f));
  console.log(`\n### ${f}`);
  console.log('kind | n | P(height of start-chain changes) | h-run length (changed edits) med/p90/max | reaches root (doc height changes) | push roots (sum following siblings over height-changed levels) med/p90/max | w-run med/p90/max | P(width changes)');
  for (const k of [...new Set(d.map((r) => r.kind))]) {
    const rs = d.filter((r) => r.kind === k);
    let hCh = 0, reach = 0, wCh = 0; const hr = [], push = [], wr = [], pushAll = []; const stop = {};
    for (const r of rs) {
      const st = r.steps;
      let anyH = false, run = 0, i = 0;
      // skip leading nobox (display:none target)
      while (i < st.length && st[i].s === 'nobox') i++;
      while (i < st.length && !st[i].dh && !st[i].s) i++;
      const first = i;
      for (; i < st.length && st[i].dh; i++) run++;
      // pushes: all levels with dh != 0
      let p = 0, anyChange = false;
      st.forEach((s, j) => { if (s.dh) { p += s.f; anyChange = true; } });
      if (anyChange) { hCh++; hr.push(run); push.push(p); }
      pushAll.push(p);
      if (st.length && st[st.length - 1].dh) reach++;
      if (anyChange && i < st.length) { const s = st[i]; const key = `${s.d}${s.p ? ' ' + s.p : ''}`; stop[key] = (stop[key] || 0) + 1; }
      let w = 0, j = st.findIndex((x) => x.dw); if (j < 0) j = st.length; for (; j < st.length && st[j].dw; j++) w++;
      if (st.some((s) => s.dw)) { wCh++; wr.push(w); }
    }
    console.log(`${k} | ${rs.length} | ${(100 * hCh / rs.length).toFixed(0)}% | ${fmt(hr)} | ${(100 * reach / rs.length).toFixed(0)}% | ${fmt(push)} | ${fmt(wr)} | ${(100 * wCh / rs.length).toFixed(0)}%`);
    console.log('   stop at (display pos/overflow/height) of first ancestor whose height is unchanged:', JSON.stringify(Object.entries(stop).sort((a, b) => b[1] - a[1]).slice(0, 6)));
  }
}
