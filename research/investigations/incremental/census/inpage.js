// In-page census machinery. Defines globalThis.__fan.
(function () {
  let EPS = 1 / 64 + 1e-4;
  let MT = 1e-3; // merge tolerance for abutting rects (grows with float32 resolution at the page height)
  const PROPS = ['display', 'float', 'position', 'color', 'fontSize', 'fontWeight', 'fontFamily', 'lineHeight', 'textAlign',
    'visibility', 'backgroundColor', 'whiteSpace', 'letterSpacing', 'marginTop', 'paddingTop', 'paddingLeft', 'borderTopWidth',
    'minWidth', 'maxWidth', 'flexGrow', 'flexBasis', 'overflowX', 'verticalAlign', 'textIndent', 'transform', 'counterIncrement'];
  const SPEC = ['width', 'height']; // via computedStyleMap: computed (not used) value
  const INLINE = new Set(['inline', 'inline-block', 'inline-flex', 'inline-grid', 'inline-table', 'ruby', 'ruby-text']);
  const els = Array.from(document.querySelectorAll('*'));
  const N = els.length;
  const idx = new Map();
  els.forEach((e, i) => idx.set(e, i));
  const parent = new Int32Array(N);
  for (let i = 0; i < N; i++) parent[i] = els[i].parentElement ? idx.get(els[i].parentElement) : -1;
  const texts = [];
  {
    const w = document.createTreeWalker(document, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) texts.push(n);
  }
  const T = texts.length;
  const tparent = new Int32Array(T);
  for (let i = 0; i < T; i++) tparent[i] = texts[i].parentElement ? idx.get(texts[i].parentElement) : -1;
  const subtree = new Int32Array(N).fill(1);
  for (let i = N - 1; i > 0; i--) if (parent[i] >= 0) subtree[parent[i]] += subtree[i];
  // previous element sibling index
  const prevSib = new Int32Array(N).fill(-1);
  for (let i = 0; i < N; i++) { const p = els[i].previousElementSibling; prevSib[i] = p ? idx.get(p) : -1; }

  const styleIntern = new Map();
  const styleStr = [];
  function internStyle(s) {
    let id = styleIntern.get(s);
    if (id === undefined) { id = styleStr.length; styleStr.push(s); styleIntern.set(s, id); }
    return id;
  }

  class Buf {
    constructor() { this.a = new Float64Array(1 << 16); this.n = 0; this.base = 0; }
    push(x, y, w, h) {
      // Merge a rect that continues the previous one on the same line (Chromium reports the same inline box as one rect
      // or as abutting pieces depending on whether it was laid out initially or incrementally).
      const a = this.a, n = this.n;
      if (this.n > this.base && Math.abs(a[n - 3] - y) <= MT && Math.abs(a[n - 1] - h) <= MT && Math.abs(a[n - 4] + a[n - 2] - x) <= MT) { a[n - 2] += w; return; }
      if (n + 4 > a.length) { const b = new Float64Array(a.length * 2); b.set(a); this.a = b; }
      const b2 = this.a; b2[n] = x; b2[n + 1] = y; b2[n + 2] = w; b2[n + 3] = h; this.n = n + 4;
    }
    mark() { this.base = this.n; }
  }

  function snapshot(withStyle) {
    const S = {};
    const eb = new Buf(); const eo = new Int32Array(N + 1);
    for (let i = 0; i < N; i++) {
      eo[i] = eb.n / 4; eb.mark();
      const l = els[i].isConnected ? els[i].getClientRects() : [];
      for (let k = 0; k < l.length; k++) { const r = l[k]; eb.push(r.x, r.y, r.width, r.height); }
    }
    eo[N] = eb.n / 4;
    S.eb = eb.a; S.eo = eo;
    const tb = new Buf(); const to = new Int32Array(T + 1);
    const range = document.createRange();
    for (let i = 0; i < T; i++) {
      to[i] = tb.n / 4; tb.mark();
      if (texts[i].isConnected) {
        range.selectNodeContents(texts[i]);
        const l = range.getClientRects();
        for (let k = 0; k < l.length; k++) { const r = l[k]; tb.push(r.x, r.y, r.width, r.height); }
      }
    }
    to[T] = tb.n / 4;
    S.tb = tb.a; S.to = to;
    if (withStyle) {
      const sid = new Int32Array(N).fill(-1);
      const disp = new Array(N);
      for (let i = 0; i < N; i++) {
        if (!els[i].isConnected) continue;
        const cs = getComputedStyle(els[i]);
        let s = '';
        for (let k = 0; k < PROPS.length; k++) s += cs[PROPS[k]] + '|';
        const m = els[i].computedStyleMap();
        for (let k = 0; k < SPEC.length; k++) s += m.get(SPEC[k]).toString() + '|';
        sid[i] = internStyle(s);
        disp[i] = cs.display;
      }
      S.sid = sid; S.disp = disp;
    }
    // union boxes per element
    const bx = new Float64Array(N), by = new Float64Array(N), bw = new Float64Array(N), bh = new Float64Array(N);
    const has = new Uint8Array(N);
    for (let i = 0; i < N; i++) {
      const a = eo[i], b = eo[i + 1];
      if (a === b) continue;
      has[i] = 1;
      let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      for (let k = a; k < b; k++) {
        const x = eb.a[4 * k], y = eb.a[4 * k + 1], w = eb.a[4 * k + 2], h = eb.a[4 * k + 3];
        if (x < x0) x0 = x; if (y < y0) y0 = y; if (x + w > x1) x1 = x + w; if (y + h > y1) y1 = y + h;
      }
      bx[i] = x0; by[i] = y0; bw[i] = x1 - x0; bh[i] = y1 - y0;
    }
    S.bx = bx; S.by = by; S.bw = bw; S.bh = bh; S.has = has;
    return S;
  }

  // classes: 0 nobox, 1 same, 2 moved (same sizes, common translation), 3 size (any fragment size / count),
  // 4 shift (same sizes, fragments shifted differently), 5 gone, 6 appeared
  function classify(Bo, Bb, Ao, Ab, n) {
    const cls = new Uint8Array(n), wch = new Uint8Array(n), hch = new Uint8Array(n);
    const ddx = new Float64Array(n), ddy = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const b0 = Bo[i], b1 = Bo[i + 1], a0 = Ao[i], a1 = Ao[i + 1];
      const nb = b1 - b0, na = a1 - a0;
      if (nb === 0 && na === 0) continue;
      if (na === 0) { cls[i] = 5; continue; }
      if (nb === 0) { cls[i] = 6; continue; }
      if (nb !== na) { cls[i] = 3; wch[i] = 1; hch[i] = 1; continue; }
      let sizeDiff = false, wd = false, hd = false;
      let dx = Ab[4 * a0] - Bb[4 * b0], dy = Ab[4 * a0 + 1] - Bb[4 * b0 + 1], common = true;
      for (let k = 0; k < nb; k++) {
        const bi = 4 * (b0 + k), ai = 4 * (a0 + k);
        if (Math.abs(Ab[ai + 2] - Bb[bi + 2]) > EPS) { sizeDiff = true; wd = true; }
        if (Math.abs(Ab[ai + 3] - Bb[bi + 3]) > EPS) { sizeDiff = true; hd = true; }
        if (Math.abs(Ab[ai] - Bb[bi] - dx) > EPS || Math.abs(Ab[ai + 1] - Bb[bi + 1] - dy) > EPS) common = false;
      }
      if (sizeDiff) { cls[i] = 3; wch[i] = wd ? 1 : 0; hch[i] = hd ? 1 : 0; continue; }
      if (!common) { cls[i] = 4; continue; }
      ddx[i] = dx; ddy[i] = dy;
      cls[i] = (Math.abs(dx) <= EPS && Math.abs(dy) <= EPS) ? 1 : 2;
    }
    return { cls, wch, hch, ddx, ddy };
  }

  function median(a) { return a.length ? a.slice().sort((x, y) => x - y)[a.length >> 1] : 0; }

  let base = null, baseline = null;
  const level = new Uint8Array(N); // 0 n,1 inline,2 block
  const pbox = new Int32Array(N).fill(-1); // nearest ancestor with box (baseline)
  const bblock = new Int32Array(N).fill(-1); // nearest ancestor-or-self with block level
  const tblock = new Int32Array(T).fill(-1);
  const ctx = new Int32Array(N).fill(-1); // nearest block-level proper ancestor (formatting-context container)
  function init() {
    // Rebuild the layout tree once so the baseline is a state reachable by re-layout (Chromium's first layout can
    // fragment some inline boxes differently from a rebuilt one).
    document.documentElement.style.display = 'none'; document.documentElement.offsetHeight;
    document.documentElement.style.removeProperty('display'); if (!document.documentElement.getAttribute('style')) document.documentElement.removeAttribute('style');
    document.documentElement.offsetHeight;
    MT = Math.max(1e-3, 3 * Math.pow(2, Math.floor(Math.log2(Math.max(document.documentElement.scrollHeight, 1))) - 23));
    base = snapshot(true);
    { // Chromium reports rect coordinates as float32; at large y a size is only known to a few ulps.
      let maxY = 0; for (let i = 0; i < N; i++) if (base.has[i] && base.by[i] + base.bh[i] > maxY) maxY = base.by[i] + base.bh[i];
      const ulp = Math.pow(2, Math.floor(Math.log2(Math.max(maxY, 1))) - 23);
      EPS = Math.max(1 / 64 + 1e-4, 3 * ulp); }
    for (let i = 0; i < N; i++) level[i] = !base.has[i] ? 0 : INLINE.has(base.disp[i]) ? 1 : 2;
    for (let i = 0; i < N; i++) {
      const p = parent[i];
      pbox[i] = p < 0 ? -1 : (base.has[p] ? p : pbox[p]);
      bblock[i] = level[i] === 2 ? i : (p < 0 ? -1 : bblock[p]);
    }
    for (let t = 0; t < T; t++) { const p = tparent[t]; tblock[t] = p < 0 ? -1 : bblock[p]; }
    for (let i = 0; i < N; i++) ctx[i] = parent[i] < 0 ? -1 : bblock[parent[i]];
    let boxes = 0, rendTexts = 0;
    for (let i = 0; i < N; i++) boxes += base.has[i];
    for (let t = 0; t < T; t++) rendTexts += base.to[t + 1] > base.to[t] ? 1 : 0;
    return { N, T, boxes, rendTexts, styles: styleStr.length, eps: EPS };
  }

  // ---- edits ----
  const CANDS = {};
  let classPool = null;
  function buildCands() {
    CANDS.text = []; CANDS.text3 = []; CANDS.blk = []; CANDS.blkSmall = []; CANDS.cont = []; CANDS.cls = []; CANDS.any = [];
    for (let t = 0; t < T; t++) {
      if (base.to[t + 1] === base.to[t]) continue;
      const s = texts[t].data.trim();
      if (s.length < 4) continue;
      CANDS.text.push(t);
      if (s.split(/\s+/).length >= 3) CANDS.text3.push(t);
    }
    for (let i = 1; i < N; i++) {
      const e = els[i];
      if (!base.has[i] || e.localName === 'html' || e.localName === 'body') continue;
      CANDS.any.push(i);
      if (level[i] === 2) {
        CANDS.blk.push(i);
        if (subtree[i] <= 25 && e.parentElement && e.parentElement.localName !== 'html') CANDS.blkSmall.push(i);
        if (subtree[i] >= 60) CANDS.cont.push(i);
      }
      if (e.classList.length > 0) CANDS.cls.push(i);
    }
    // classes mentioned in stylesheet selectors
    const set = new Set();
    const walk = (rules) => { for (const r of rules) { if (r.selectorText) { for (const m of r.selectorText.matchAll(/\.([A-Za-z_][\w-]*)/g)) set.add(m[1]); } if (r.cssRules) walk(r.cssRules); } };
    for (const ss of document.styleSheets) { try { walk(ss.cssRules); } catch (e) {} }
    classPool = Array.from(set);
    return { text: CANDS.text.length, text3: CANDS.text3.length, blk: CANDS.blk.length, blkSmall: CANDS.blkSmall.length, cont: CANDS.cont.length, cls: CANDS.cls.length, any: CANDS.any.length, classPool: classPool.length };
  }
  function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const WORDS = 'lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'.split(' ');
  const pick = (r, a) => a[Math.floor(r() * a.length)];
  const desc = (i) => { const e = els[i]; return e.localName + (e.classList.length ? '.' + Array.from(e.classList).slice(0, 2).join('.') : '') + (e.id ? '#' + e.id.slice(0, 20) : ''); };

  // returns {apply, revert, target (elem idx or -1), ttarget (text idx or -1), parentTouched (elem idx or -1), descr}
  function makeEdit(kind, seed) {
    const r = rng(seed);
    const styleEdit = (list, prop, valueFn) => {
      const i = pick(r, list); const e = els[i]; const old = e.getAttribute('style');
      return { target: i, ttarget: -1, touched: -1, descr: kind + ' ' + desc(i), apply() { e.style[prop] = valueFn(i); }, revert() { if (old === null) e.removeAttribute('style'); else e.setAttribute('style', old); } };
    };
    switch (kind) {
      case 'text+word': case 'text-word': case 'text+sentence': {
        const t = pick(r, kind === 'text-word' ? CANDS.text3 : CANDS.text); const n = texts[t]; const old = n.data;
        const wb = []; const re = /\s+/g; let m; while ((m = re.exec(old))) wb.push(m.index);
        const at = wb.length ? pick(r, wb) : old.length;
        let neu;
        if (kind === 'text+word') neu = old.slice(0, at) + ' ' + pick(r, WORDS) + old.slice(at);
        else if (kind === 'text+sentence') neu = old.slice(0, at) + ' ' + Array.from({ length: 12 }, () => pick(r, WORDS)).join(' ') + '.' + old.slice(at);
        else { const ws = old.split(/(\s+)/); const wi = ws.map((x, k) => k).filter((k) => k % 2 === 0 && ws[k].length > 0); const k = pick(r, wi); ws.splice(k, 1); neu = ws.join(''); }
        return { target: -1, ttarget: t, touched: -1, descr: kind + ' in ' + desc(tparent[t]), apply() { n.data = neu; }, revert() { n.data = old; } };
      }
      case 'class+': {
        const i = pick(r, CANDS.any); const e = els[i]; const old = e.getAttribute('class'); const c = pick(r, classPool);
        return { target: i, ttarget: -1, touched: -1, descr: kind + ' ' + c + ' on ' + desc(i), apply() { e.classList.add(c); }, revert() { if (old === null) e.removeAttribute('class'); else e.setAttribute('class', old); } };
      }
      case 'class-': {
        const i = pick(r, CANDS.cls); const e = els[i]; const old = e.getAttribute('class'); const c = pick(r, Array.from(e.classList));
        return { target: i, ttarget: -1, touched: -1, descr: kind + ' ' + c + ' from ' + desc(i), apply() { e.classList.remove(c); }, revert() { e.setAttribute('class', old); } };
      }
      case 'color': return styleEdit(CANDS.any, 'color', () => 'rgb(200,0,0)');
      case 'width': return styleEdit(CANDS.blk, 'width', (i) => Math.max(10, Math.round(base.bw[i] * 0.8)) + 'px');
      case 'font-size': return styleEdit(CANDS.any, 'fontSize', () => '120%');
      case 'display-none': return styleEdit(CANDS.any, 'display', () => 'none');
      case 'container-color': return styleEdit(CANDS.cont, 'color', () => 'rgb(200,0,0)');
      case 'container-font-size': return styleEdit(CANDS.cont, 'fontSize', () => '110%');
      case 'container-width': return styleEdit(CANDS.cont, 'width', (i) => Math.max(10, Math.round(base.bw[i] * 0.8)) + 'px');
      case 'insert-block': {
        const i = pick(r, CANDS.blkSmall); const e = els[i];
        return { target: -1, ttarget: -1, touched: parent[i], descr: kind + ' after ' + desc(i), clone: null,
          apply() { this.clone = e.cloneNode(true); e.after(this.clone); }, revert() { this.clone.remove(); } };
      }
      case 'remove-block': {
        const i = pick(r, CANDS.blkSmall); const e = els[i]; const p = e.parentNode; const nx = e.nextSibling;
        return { target: -1, ttarget: -1, touched: parent[i], descr: kind + ' ' + desc(i), apply() { e.remove(); }, revert() { p.insertBefore(e, nx); } };
      }
    }
    throw new Error('kind ' + kind);
  }

  function runEdit(kind, seed, verify) {
    const ed = makeEdit(kind, seed);
    ed.apply();
    const t0 = performance.now();
    const A = snapshot(true);
    const dt = performance.now() - t0;
    const R = diff(A, ed);
    R.kind = kind; R.descr = ed.descr; R.snapMs = dt;
    ed.revert();
    if (verify) {
      const V = snapshot(true);
      const D = classify(base.eo, base.eb, V.eo, V.eb, N);
      let bad = 0; for (let i = 0; i < N; i++) if (D.cls[i] > 1) bad++;
      const T2 = classify(base.to, base.tb, V.to, V.tb, T);
      let badT = 0; for (let i = 0; i < T; i++) if (T2.cls[i] > 1) badT++;
      let badS = 0; for (let i = 0; i < N; i++) if (V.sid[i] !== base.sid[i]) badS++;
      R.verify = { badBoxes: bad, badTexts: badT, badStyles: badS };
      if (bad) { R.verify.ex = []; for (let i = 0; i < N && R.verify.ex.length < 2; i++) if (D.cls[i] > 1) R.verify.ex.push(i + ':' + desc(i) + ' cls' + D.cls[i] + ' ' + base.eb.slice(4 * base.eo[i], 4 * base.eo[i + 1]).join(',') + ' -> ' + V.eb.slice(4 * V.eo[i], 4 * V.eo[i + 1]).join(',')); }
    }
    return R;
  }

  function diff(A, ed) {
    const E = classify(base.eo, base.eb, A.eo, A.eb, N);
    const X = classify(base.to, base.tb, A.to, A.tb, T);
    const R = {};
    const cnt = (c, k) => { let n = 0; for (let i = 0; i < c.length; i++) if (c[i] === k) n++; return n; };
    // element classes
    R.e = { same: cnt(E.cls, 1), moved: cnt(E.cls, 2), size: cnt(E.cls, 3), shift: cnt(E.cls, 4), gone: cnt(E.cls, 5), appeared: cnt(E.cls, 6) };
    R.t = { same: cnt(X.cls, 1), moved: cnt(X.cls, 2), size: cnt(X.cls, 3), shift: cnt(X.cls, 4), gone: cnt(X.cls, 5), appeared: cnt(X.cls, 6) };
    // style
    const styleCh = new Uint8Array(N);
    let sc = 0, scGeom = 0, scPaintOnly = 0;
    for (let i = 0; i < N; i++) {
      if (A.sid[i] === base.sid[i]) continue;
      styleCh[i] = 1; sc++;
      const c = E.cls[i];
      if (c === 1 || (c === 0)) scPaintOnly++; else scGeom++;
    }
    R.styleChanged = sc; R.styleChangedNoGeom = scPaintOnly;
    // style changed by relation to the target: which are descendants of target?
    const tgt = ed.target;
    if (tgt >= 0) {
      let d = 0, nd = 0;
      for (let i = 0; i < N; i++) if (styleCh[i]) { let p = i, inS = false; while (p >= 0) { if (p === tgt) { inS = true; break; } p = parent[p]; } if (inS) d++; else nd++; }
      R.styleInTargetSubtree = d; R.styleOutsideTarget = nd; R.targetSubtree = subtree[tgt];
    }
    // new boxes from inserted nodes
    // relative-position roots
    const relCh = (Sx, Sy, i, p, Bx, By) => 0;
    let movedAbs = 0, m1 = 0, m2 = 0, sameRelCh = 0;
    let m1Block = 0, m2Block = 0, movedBlock = 0, mCtx = 0, mCtxInl = 0, movedInl = 0;
    const roots1 = []; // for debugging sample
    for (let i = 0; i < N; i++) {
      const c = E.cls[i];
      if (c !== 2 && c !== 1) continue;
      const p = pbox[i];
      const pOk = p < 0 || (E.cls[p] !== 0 && E.cls[p] !== 5 && E.cls[p] !== 6);
      // parent-relative offset
      const bpx = p < 0 ? 0 : base.bx[p], bpy = p < 0 ? 0 : base.by[p];
      const apx = p < 0 ? 0 : A.bx[p], apy = p < 0 ? 0 : A.by[p];
      const r1 = !pOk || Math.abs((A.bx[i] - apx) - (base.bx[i] - bpx)) > EPS || Math.abs((A.by[i] - apy) - (base.by[i] - bpy)) > EPS;
      // sibling-end anchored: previous block-level sibling with box in both states
      let ps = prevSib[i]; while (ps >= 0 && !(base.has[ps] && A.has[ps])) ps = prevSib[ps];
      let r2 = r1;
      if (ps >= 0 && level[ps] === 2 && level[i] === 2) {
        r2 = Math.abs((A.bx[i] - A.bx[ps]) - (base.bx[i] - base.bx[ps])) > EPS || Math.abs((A.by[i] - (A.by[ps] + A.bh[ps])) - (base.by[i] - (base.by[ps] + base.bh[ps]))) > EPS;
      }
      if (c === 2) {
        const cb = ctx[i];
        const cOk = cb < 0 || E.cls[cb] === 1 || E.cls[cb] === 2;
        const cbx = cb < 0 ? 0 : base.bx[cb], cby = cb < 0 ? 0 : base.by[cb], acx = cb < 0 ? 0 : A.bx[cb], acy = cb < 0 ? 0 : A.by[cb];
        const rc = !cOk || Math.abs((A.bx[i] - acx) - (base.bx[i] - cbx)) > EPS || Math.abs((A.by[i] - acy) - (base.by[i] - cby)) > EPS;
        if (rc) mCtx++;
        if (level[i] === 1) { movedInl++; if (rc) mCtxInl++; }
      }
      if (c === 2) { movedAbs++; if (r1) m1++; if (r2) m2++; if (level[i] === 2) { movedBlock++; if (r1) m1Block++; if (r2) m2Block++; } }
      else if (r1) sameRelCh++;
    }
    R.moved = { abs: movedAbs, parentRel: m1, sibRel: m2, absBlock: movedBlock, parentRelBlock: m1Block, sibRelBlock: m2Block, sameButRelChanged: sameRelCh, ctxRel: mCtx, inl: movedInl, ctxRelInl: mCtxInl };
    // text moved roots (relative to parent element box)
    let tm = 0, tm1 = 0, tmCtx = 0;
    for (let t = 0; t < T; t++) {
      if (X.cls[t] !== 2) continue; tm++;
      { const b = tblock[t]; if (b < 0 || !(E.cls[b] === 1 || E.cls[b] === 2) || Math.abs(X.ddx[t] - E.ddx[b]) > EPS || Math.abs(X.ddy[t] - E.ddy[b]) > EPS) tmCtx++; }
      const p = tparent[t]; if (p < 0) { tm1++; continue; }
      const pOk = E.cls[p] === 1 || E.cls[p] === 2;
      if (!pOk) { tm1++; continue; }
      const dxr = X.ddx[t] - E.ddx[p], dyr = X.ddy[t] - E.ddy[p];
      if (Math.abs(dxr) > EPS || Math.abs(dyr) > EPS) tm1++;
    }
    R.tmoved = { abs: tm, parentRel: tm1, ctxRel: tmCtx };
    // child-change flags
    const childSize = new Uint8Array(N), childMoved = new Uint8Array(N);
    for (let i = 0; i < N; i++) {
      const p = parent[i]; if (p < 0) continue;
      const c = E.cls[i];
      if (c === 3 || c === 4 || c === 5 || c === 6) childSize[p] = 1; else if (c === 2) childMoved[p] = 1;
    }
    for (let t = 0; t < T; t++) {
      const p = tparent[t]; if (p < 0) continue;
      const c = X.cls[t];
      if (c === 3 || c === 4 || c === 5 || c === 6) childSize[p] = 1; else if (c === 2) childMoved[p] = 1;
    }
    if (ed.touched >= 0) childSize[ed.touched] = 1;
    if (ed.ttarget >= 0 && tparent[ed.ttarget] >= 0) childSize[tparent[ed.ttarget]] = 1;
    // cause attribution for size-changed elements
    const wc = { own: 0, followsParent: 0, childW: 0, parentOther: 0, other: 0 };
    const hc = { own: 0, child: 0, ownW: 0, childPush: 0, other: 0 };
    const other = {}; const otherH = {};
    let sizeBoth = 0, sizeWonly = 0, sizeHonly = 0;
    const depthHist = {};
    for (let i = 0; i < N; i++) {
      if (E.cls[i] !== 3 && E.cls[i] !== 4) continue;
      if (E.cls[i] === 4) continue;
      const own = styleCh[i] || i === ed.target;
      const p = pbox[i];
      const w = E.wch[i], h = E.hch[i];
      if (w && h) sizeBoth++; else if (w) sizeWonly++; else sizeHonly++;
      const key = (p >= 0 ? base.disp[p] : '-') + '>' + base.disp[i] + (base.disp[i] !== 'none' ? '' : '') ;
      const k2 = key + (A.disp[i] && base.disp[i] !== A.disp[i] ? '*' : '');
      if (w) {
        const dwi = A.bw[i] - base.bw[i];
        const dwp = (p >= 0 && E.cls[p] === 3) ? A.bw[p] - base.bw[p] : 0;
        if (own) wc.own++;
        else if (p >= 0 && level[i] === 2 && Math.abs(dwi - dwp) <= EPS && Math.abs(dwp) > EPS) wc.followsParent++;
        else if (childSize[i]) wc.childW++;
        else if (p >= 0 && E.wch[p] && E.cls[p] === 3) wc.parentOther++;
        else { wc.other++; other[key] = (other[key] || 0) + 1; }
      }
      if (h) {
        if (own) hc.own++;
        else if (childSize[i]) hc.child++;
        else if (w) hc.ownW++;
        else if (childMoved[i]) hc.childPush++;
        else { hc.other++; otherH[key] = (otherH[key] || 0) + 1; }
      }
    }
    R.sizeBoth = sizeBoth; R.sizeWonly = sizeWonly; R.sizeHonly = sizeHonly;
    R.wCause = wc; R.hCause = hc;
    const top = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 5);
    R.wOther = top(other); R.hOther = top(otherH);
    // text size-change causes
    const tc = { edited: 0, style: 0, containerW: 0, paragraphMate: 0, other: 0 };
    const eblock = ed.ttarget >= 0 ? tblock[ed.ttarget] : (ed.target >= 0 ? bblock[ed.target] : -1);
    const tother = {};
    for (let t = 0; t < T; t++) {
      if (X.cls[t] !== 3 && X.cls[t] !== 4) continue;
      const p = tparent[t]; const b = tblock[t];
      if (t === ed.ttarget) tc.edited++;
      else if (p >= 0 && styleCh[p]) tc.style++;
      else if (b >= 0 && E.cls[b] === 3 && E.wch[b] && (b !== eblock)) tc.containerW++;
      else if (b >= 0 && b === eblock) tc.paragraphMate++;
      else { tc.other++; const k = (b >= 0 ? base.disp[b] : '-') + '/' + (p >= 0 ? base.disp[p] : '-'); tother[k] = (tother[k] || 0) + 1; }
    }
    R.tCause = tc; R.tOther = top(tother);
    // text own-content-change: size changed texts and edited node
    // inserted-node boxes
    let newBoxes = 0;
    if (ed.clone) { const q = ed.clone; newBoxes = 1 + q.querySelectorAll('*').length; }
    R.newNodes = newBoxes;
    // extent: number of distinct DOM parents among changed boxes, and the span of document order of any changed element
    let lo = N, hi = -1, nch = 0;
    for (let i = 0; i < N; i++) if (E.cls[i] >= 2 && E.cls[i] <= 6 || styleCh[i]) { nch++; if (i < lo) lo = i; if (i > hi) hi = i; }
    R.own = (ed.target >= 0 ? 1 : 0) + (ed.ttarget >= 0 ? 1 : 0) + (R.styleInTargetSubtree || 0) + (ed.touched >= 0 ? 1 : 0) + newBoxes;
    R.anyChanged = nch; R.span = hi >= 0 ? hi - lo + 1 : 0;
    // geometry-changed region extent (document y of changed boxes): min y, max y after
    // depth of the root and LCA of all changed elements
    return R;
  }

  globalThis.__fan = { eps: () => EPS, els, parent, tparent, level, makeEdit, init, buildCands, runEdit, snapshot: () => snapshot(true), tags: () => ({}) };
})();
