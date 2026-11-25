# Formatting

How layout lays out tables and multi-column containers, and the room it gives scrollbars.

### decision tables-follow-css-tables-3
Tables follow the automatic and fixed table layout of CSS Tables 3's editor's draft, and the reference browser's behavior where the draft leaves a step undefined.
- rejected: an agent proposed CSS 2.2's informative automatic layout; the owner rejected it, because it leaves column widths to the implementation, while the draft is the one the reference's tables follow.

### decision multi-column-split-after-one-column
A multi-column container is laid out as one column of its used width, then split into the fewest balanced columns between units no break may cross, and a column map moves each column's content.
- rejected: an agent proposed leaving multi-column layout out of scope; the owner rejected it, because 20.7 percent of html5's block boxes and 14 percent of apollo11's lie in multi-column containers, so layout could not match the reference on those pages.

### decision scrollbars-take-no-space
Scrollbars take no space beside a scroll container or the viewport.
- rejected: an agent proposed reserving 15 px beside every scroll container, as desktop Chromium does by default; the owner rejected it, because the reference renders with hidden scrollbars, and overlay scrollbars behave so.
