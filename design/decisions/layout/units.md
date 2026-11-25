# Units

The fixed-point unit layout measures in, and how a computed length becomes one.

### decision layout-lengths-are-fixed-point
Layout lengths are `LayoutUnit`, an `i32` counting 1/64 of a CSS pixel, and the geometry types are built on it.
- rejected: an agent proposed `f32` or `f64` lengths; the owner rejected it, because fixed point adds and compares exactly, keeps a layout free of floating-point rounding and evaluation order, and still spans about 33 million pixels, as Blink's layout unit does.

### decision lengths-become-layout-units-when-read
A computed length stays `f32` CSS pixels and becomes a `LayoutUnit` once, when layout reads it, with each conversion the reference's for its use.
- replaced: Rounding lengths at computed-value time was on main; the owner changed it, because percentages and `calc()` already wait for layout, so layout reads every length anyway, and the reference reports computed lengths unrounded.
- replaced: Truncating every length, line heights included, was on main; the owner changed it, because the reference rounds a length line height to the nearest unit, and truncating put apollo11's infobox 1 px short after 60 rows (data: `research/investigations/layout/runs/line-height-rounding.txt`).
- rejected: an agent proposed rounding each glyph's advance; the owner rejected it, because it drifts by up to 1/128 px a glyph and moves line breaks (data: `research/investigations/layout/runs/scope-probe.txt`).
