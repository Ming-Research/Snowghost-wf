# Text

How layout matches fonts, shapes and prepares each paragraph's text, and how it reuses shaped text after an edit.

### decision font-families-through-a-table-of-our-own
A `font-family` list is matched against the installed faces through Snowghost's own table of how the reference browser resolves families on its host, with Liberation Serif when nothing matches.
- rejected: an agent proposed reading fontconfig's configuration; the owner rejected it, because it would tie the renderer to one platform's font service, while the table draws all but 0.1 percent of the pages' glyphs as the reference does (data: `research/investigations/layout/DESIGN.md`).

### decision text-prepared-per-paragraph
Text is prepared in one counted loop over paragraphs, each shaping its own items once with `pkg::font` and finding its break opportunities and intrinsic contributions.
- rejected: an agent proposed a shaping cache shared across paragraphs, as Blink keeps per word; the owner rejected it, because every paragraph would read and write it, which orders paragraphs that do not depend on each other.

### decision shaped-advances-rescale-on-a-size-change
A shaped paragraph keeps each one-glyph cluster's advances in font units, so preparing it again with the same text rescales an unchanged segment instead of shaping it.
- replaced: Shaping every paragraph prepared again was on main; the owner changed it, because shaping does not read the font size, so the output is the same byte for byte, and html5's root font-size edit went from 791 to 583 ms (data: `research/investigations/incremental-style/runs/rootfont.txt`).
