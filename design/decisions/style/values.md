# Values

The values the style stage starts from and computes: the user-agent sheet, font-relative units, the groups a computed style is stored in, and percentages.

### decision user-agent-sheet-follows-chromium
The user-agent sheet holds the HTML Standard's rules where Chromium agrees and Chromium's own where they differ, such as `table { border-color: gray }` and no `counter-reset: list-item` on lists.
- replaced: The HTML Standard's sheet, with Chromium's differences recorded and not copied, was on main; the owner changed it, because readers judge a renderer against Chromium, and the Standard's rules alone left table borders, `sub` and `sup` line heights and form controls unlike it.

### decision ex-and-ch-from-the-default-font
`ex` and `ch` come from the x-height and the zero digit's advance of the default font of the element's first generic family, serif when the list has none.
- rejected: an agent proposed half an em, the fallback CSS allows; the owner rejected it, because the reference resolves them from those metrics, and half an em put 7.4 percent of ecma262's elements off in their right margin (data: `research/investigations/style/DESIGN.md`).

### decision computed-style-is-interned-groups
A computed style is a struct of twelve group identifiers, one per group of values that change together, each group interned in its own table and the tables interned in parallel.
- replaced: One sequential interning pass over all groups was on main; the owner changed it, because the groups' tables are independent, so each can be interned as its own task.
- rejected: an agent proposed adding the layout-only properties to the box group; the owner rejected it, because values that most elements leave initial would make box groups differ and lose sharing.

### decision percentages-wait-for-layout
A computed length that depends on a percentage, alone or in `calc()`, stays a percentage and an offset until layout resolves it against its basis.
- rejected: an agent proposed resolving percentages against an assumed containing block; the owner rejected it, because the containing block's size is layout's result, so style would depend on layout, against CSS's definition of computed values.
