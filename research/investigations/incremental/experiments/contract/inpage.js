(() => {
const COMPOSITOR = new Set(['transform','opacity','translate','rotate','scale','filter','backdropFilter','webkitBackdropFilter']);
const PAINT_RE = /color|shadow|fill|stroke|background|outline|visibility|clipPath|mask|textDecoration|caret|accent|borderImage|boxDecoration|stopColor|floodColor/i;
function allElements() {
  const out = [];
  const walk = (root) => {
    const els = root.querySelectorAll('*');
    for (const e of els) { out.push(e); if (e.shadowRoot) walk(e.shadowRoot); }
  };
  walk(document);
  return out;
}
function rendered(e) { return e.getClientRects().length > 0; }
function census() {
  const els = allElements();
  const R = { elements: els.length, stacking: 0, stackingReasons: {}, transform: 0, opacity: 0, filter: 0, backdrop: 0, blend: 0,
    fixed: 0, sticky: 0, scrollRoots: 0, willChange: 0, willChangeValues: {}, video: 0, canvas: 0, iframe: 0, svg: 0, img: 0, maskOrClip: 0 };
  const bump = (o, k) => { o[k] = (o[k] || 0) + 1; };
  const html = document.documentElement;
  for (const e of els) {
    if (e === html) continue;
    const cs = getComputedStyle(e);
    if (cs.display === 'none') continue;
    if (!rendered(e) && cs.display !== 'contents') continue;
    const tag = e.localName;
    if (tag === 'video') R.video++; else if (tag === 'canvas') R.canvas++; else if (tag === 'iframe') R.iframe++; else if (tag === 'svg') R.svg++; else if (tag === 'img') R.img++;
    if (cs.display === 'contents') continue;
    const pos = cs.position;
    const par = e.parentElement ? getComputedStyle(e.parentElement) : null;
    const reasons = [];
    const tr = cs.transform !== 'none' || cs.translate !== 'none' || cs.rotate !== 'none' || cs.scale !== 'none';
    const op = parseFloat(cs.opacity) < 1;
    const fl = cs.filter !== 'none';
    const bf = (cs.backdropFilter && cs.backdropFilter !== 'none') || (cs.webkitBackdropFilter && cs.webkitBackdropFilter !== 'none');
    const bl = cs.mixBlendMode !== 'normal';
    if (tr) { R.transform++; reasons.push('transform'); }
    if (op) { R.opacity++; reasons.push('opacity'); }
    if (fl) { R.filter++; reasons.push('filter'); }
    if (bf) { R.backdrop++; reasons.push('backdrop-filter'); }
    if (bl) { R.blend++; reasons.push('mix-blend-mode'); }
    if (pos === 'fixed') { R.fixed++; reasons.push('fixed'); }
    if (pos === 'sticky') { R.sticky++; reasons.push('sticky'); }
    if ((pos === 'absolute' || pos === 'relative') && cs.zIndex !== 'auto') reasons.push('z-index');
    else if (cs.zIndex !== 'auto' && par && /flex|grid/.test(par.display)) reasons.push('z-index-flexitem');
    if (cs.perspective !== 'none') reasons.push('perspective');
    if (cs.clipPath !== 'none') { R.maskOrClip++; reasons.push('clip-path'); }
    const mk = cs.maskImage || cs.webkitMaskImage;
    if (mk && mk !== 'none') { R.maskOrClip++; reasons.push('mask'); }
    if (cs.isolation === 'isolate') reasons.push('isolation');
    if (/layout|paint|strict|content/.test(cs.contain)) reasons.push('contain');
    if (cs.containerType && cs.containerType !== 'normal') reasons.push('container-type');
    if (cs.willChange !== 'auto') {
      R.willChange++; bump(R.willChangeValues, cs.willChange);
      if (/opacity|transform|filter|perspective|clip-path|mask|isolation|contain|position|z-index|translate|rotate|scale|backdrop|mix-blend/.test(cs.willChange)) reasons.push('will-change');
    }
    if (cs.viewTransitionName && cs.viewTransitionName !== 'none') reasons.push('view-transition-name');
    if (reasons.length) { R.stacking++; for (const r of new Set(reasons)) bump(R.stackingReasons, r); }
    // nested scroll roots: auto/scroll with scrollable overflow
    if (e !== document.body) {
      const ox = cs.overflowX, oy = cs.overflowY;
      const sy = (oy === 'auto' || oy === 'scroll') && e.scrollHeight > e.clientHeight + 1 && e.clientHeight > 0;
      const sx = (ox === 'auto' || ox === 'scroll') && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0;
      if (sy || sx) R.scrollRoots++;
    }
  }
  // animations
  const A = { running: 0, compositor: 0, paint: 0, layout: 0, cssAnimation: 0, cssTransition: 0, script: 0, infinite: 0, targets: 0, byProperty: {}, byClass: {} };
  const tg = new Set();
  for (const a of document.getAnimations()) {
    if (a.playState !== 'running' || !a.effect) continue;
    let props = new Set();
    try { for (const kf of a.effect.getKeyframes()) for (const k of Object.keys(kf)) if (!['offset','easing','composite','computedOffset'].includes(k)) props.add(k); } catch (e) {}
    if (!props.size) continue;
    A.running++;
    const ps = [...props];
    let cls = 'compositor';
    if (ps.some((p) => !COMPOSITOR.has(p))) cls = ps.every((p) => COMPOSITOR.has(p) || PAINT_RE.test(p)) ? 'paint' : 'layout';
    A[cls]++;
    for (const p of ps) A.byProperty[p] = (A.byProperty[p] || 0) + 1;
    const ctor = a.constructor.name;
    if (ctor === 'CSSAnimation') A.cssAnimation++; else if (ctor === 'CSSTransition') A.cssTransition++; else A.script++;
    try { if (a.effect.getComputedTiming().iterations === Infinity) A.infinite++; } catch (e) {}
    if (a.effect.target) tg.add(a.effect.target);
  }
  A.targets = tg.size;
  const viewport = { w: innerWidth, h: innerHeight, scrollH: document.documentElement.scrollHeight, bodyScrollH: document.body ? document.body.scrollHeight : 0 };
  return { R, A, viewport };
}
// ---- X17 helpers
function prep() {
  const els = allElements();
  const cand = [];
  for (const e of els) {
    const p = getComputedStyle(e).position;
    if ((p === 'fixed' || p === 'sticky') && rendered(e)) cand.push(e);
  }
  for (const e of cand) e.setAttribute('data-wf-f', '');
  const roots = cand.filter((e) => !(e.parentElement && e.parentElement.closest('[data-wf-f]')));
  for (const e of cand) e.removeAttribute('data-wf-f');
  window.__roots = roots;
  roots.forEach((e, i) => e.setAttribute('data-wf-f', String(i)));
  const st = document.createElement('style');
  st.textContent = 'html *{pointer-events:auto !important}';
  document.head.appendChild(st);
  return roots.length;
}
function rootRects() {
  return window.__roots.map((e) => { const r = e.getBoundingClientRect(); return [r.left + scrollX, r.top + scrollY, r.width, r.height, getComputedStyle(e).position]; });
}
const MEDIA = new Set(['img','video','canvas','svg','iframe','picture','object','embed','input','button','select','textarea']);
function alphaOf(c) { if (!c || c === 'transparent') return 0; const m = c.match(/rgba?\(([^)]*)\)/); if (m) { const p = m[1].split(/[ ,\/]+/); return p.length > 3 ? parseFloat(p[3]) : 1; } return 1; }
function frameB(prevDoc) {
  // prevDoc: root doc rects of the previous frame (or null). Returns per-frame info incl. hit-test interleave check.
  const cur = rootRects();
  const moved = cur.map((c, i) => prevDoc ? (Math.abs(c[0] - prevDoc[i][0]) > 0.5 || Math.abs(c[1] - prevDoc[i][1]) > 0.5) : false);
  const W = document.documentElement.clientWidth, H = innerHeight;
  const NX = 16, NY = 9;
  const info = { cur, moved, interleavedPoints: 0, nsPoints: 0, points: NX * NY, stackMax: 0, examples: [] };
  const csCache = new Map(), txtCache = new Map();
  const paintableNoText = (e) => {
    if (csCache.has(e)) return csCache.get(e);
    const cs = getComputedStyle(e);
    let v = false;
    if (cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0) {
      v = MEDIA.has(e.localName) || alphaOf(cs.backgroundColor) > 0 || cs.backgroundImage !== 'none';
    } else v = null; // invisible
    csCache.set(e, v); return v;
  };
  const textHit = (e, x, y) => {
    let rs = txtCache.get(e);
    if (!rs) {
      rs = [];
      for (const n of e.childNodes) if (n.nodeType === 3 && /\S/.test(n.data)) { const r = document.createRange(); r.selectNodeContents(n); for (const q of r.getClientRects()) rs.push(q); }
      txtCache.set(e, rs);
    }
    for (const q of rs) if (x >= q.left && x < q.right && y >= q.top && y < q.bottom) return true;
    return false;
  };
  for (let iy = 0; iy < NY; iy++) for (let ix = 0; ix < NX; ix++) {
    const x = (ix + 0.5) * W / NX, y = (iy + 0.5) * H / NY;
    const st = document.elementsFromPoint(x, y);
    if (st.length > info.stackMax) info.stackMax = st.length;
    let seenS = false, hasN = false, inter = false;
    for (const e of st) {
      const v = paintableNoText(e);
      if (v === null) continue;
      const pa = v || textHit(e, x, y);
      if (!pa) continue;
      const rt = e.closest('[data-wf-f]');
      const isN = rt && moved[Number(rt.getAttribute('data-wf-f'))];
      if (isN) { hasN = true; if (seenS) inter = true; } else seenS = true;
    }
    if (hasN) info.nsPoints++;
    if (inter) { info.interleavedPoints++; if (info.examples.length < 2) info.examples.push([Math.round(x), Math.round(y)]); }
  }
  return info;
}
function descr(i) { const e = window.__roots[i]; return e.localName + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : ''); }
window.__wf = { census, prep, rootRects, frameB, descr, scrollInfo: () => ({ scrollH: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0), H: innerHeight, W: document.documentElement.clientWidth, canScroll: document.scrollingElement.scrollHeight > innerHeight + 1 }) };
})();
