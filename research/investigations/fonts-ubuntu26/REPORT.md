# Ubuntu 26.04 font refusal diagnosis

Only `/usr/share/fonts/opentype/unifont/unifont_upper_sample.otf` from
`fonts-unifont` `1:16.0.04-1build1` causes `FontsError::Refused(face: 16)`,
not `FontsError::Unreadable`. Its `cmap` data is
malformed, and both fontTools and Chromium reject it independently.
This evidence identifies an invalid packaged font, rather than a missing
Snowghost feature for a valid font.

The unchanged sequential layout driver at Snowghost revision
`65fd29a0139400ca069634bbbfa2ceda9284d65e`, built with pinned release
`wf-78223721f77d`, refuses the Ubuntu 26.04 font set and accepts the Ubuntu
24.04 control. Both sets contain all 47 `SYSTEM_FONTS` files.

The question is which package files trigger the refusal and which OpenType
feature distinguishes them from the accepted control. The comparison uses
the exact font-package list in `time-14900k.yml`, downloaded after
`apt-get update` inside the official `ubuntu:26.04` and `ubuntu:24.04`
Docker images and extracted with `dpkg -x` into fresh host-mounted trees.
The `ubuntu:26.04` tag exists; no substitute tag was needed.

All compilation and probes ran on GitHub-hosted `ubuntu-24.04`. There was
no local build, test, check or measurement and no self-hosted job. The
driver uses `make compiler`, `make toolchain`, the release's checked LLVM
toolchain, and the timing workflow's sequential `--cache --fragments
function --graph modules.wfg --entry layout_oracle` compilation path.
The committed renderer, timing workflow, pin and submodules were unchanged.
After the unchanged-driver probes, CI temporarily expanded the layout
driver's failure message to print the existing `FontsError` variant and
zero-based face index, exposing those fields in the module interface only
for that diagnostic build, without changing font acceptance or exit status.
The artifact retains that diagnostic patch.

The page was the existing `html5` input, downloaded from WebKit revision
`e9f2cf896959ec35ce49b0458b2b1bcfbd301e86` and checked against the pinned
SHA-256 `f0466f5a8c8099935a9394607abcd4bbbb3b41384a14b3f906eea80a521fe06e`.
Both roots used `make -s oracle-fonts FONT_ROOT=<extracted-root>` followed
by `sh research/investigations/incremental-layout/run.sh prepare html5`.
Isolation restored the 24.04 set before swapping each changed file into
`build/fonts`, and used one small page through the unchanged driver.

## Package versions

| Package | Ubuntu 24.04 | Ubuntu 26.04 |
|---|---|---|
| fonts-dejavu-core | 2.37-8 | 2.37-8build1 |
| fonts-dejavu-mono | 2.37-8 | 2.37-8build1 |
| fonts-dejavu-extra | 2.37-8 | 2.37-8build1 |
| fonts-liberation | 1:2.1.5-3 | 1:2.1.5-3build1 |
| fonts-freefont-ttf | 20211204+svn4273-2 | 20211204+svn4273-4build1 |
| fonts-wqy-zenhei | 0.9.45-8 | 0.9.45-8build1 |
| fonts-ipafont-gothic | 00303-21ubuntu1 | 00303-23ubuntu1 |
| fonts-tlwg-loma-otf | 1:0.7.3-1 | 1:0.7.3-1build1 |
| fonts-unifont | 1:15.1.01-1build1 | 1:16.0.04-1build1 |
| fonts-noto-color-emoji | 2.047-0ubuntu0.24.04.1 | 2.051-1build1 |
| fonts-opensymbol | 4:102.12+LibO24.2.7-0ubuntu0.24.04.7 | 4:102.12+LibO26.2.6.3-0ubuntu0.26.04.2 |

## File isolation

Of the 47 configured files, 43 differ by SHA-256 between the two roots;
the other four are identical. Each changed file was swapped individually
into the accepted 24.04 set. Only face 16,
`/usr/share/fonts/opentype/unifont/unifont_upper_sample.otf`, caused the
unchanged driver to fail; the other 42 swaps passed.

| Version | Size in bytes | SHA-256 | Symlink | `file` type |
|---|---:|---|---|---|
| 24.04 | 5915464 | `68dfc1d34d533c8dada07a8dd84294635afdc4790904fa956ea735ca1d20c127` | false | OpenType font data |
| 26.04 | 5999116 | `6f0365a3628e3807b874beb0b86a3f10bdc13f4435be8be214a4f62271a35482` | false | OpenType font data |

## Format-level refusal

The 26.04 file's `cmap` has two Windows encoding records. The BMP record
`(3,1)` points to format 4 at byte 20, declares length 24 and one segment.
Interpreted according to that declaration, it has:

| Field | 26.04 value | 24.04 control |
|---|---|---|
| segment count | 1 | 2 |
| reserved padding | `0xFFFF` | `0` |
| first segment end | `0xFFFE` | `0x0020` |
| first segment start | `0` | `0x0020` |
| first segment delta (raw unsigned word) | `0xFFFF` | `0xFFE1` |
| first segment range offset | `1` | `0` |

The full-repertoire record `(3,10)` declares offset 44, but format 12's
`000c` marker is at byte 46. Byte 44 instead begins `0000 000c`, which
looks like format 0 with a length of 12. The bytes are consistent with an
extra end-code word shifting the later fields and subtable by two bytes.

These are malformed existing formats, not a new format or version.
The [OpenType cmap specification](https://learn.microsoft.com/en-us/typography/opentype/spec/cmap)
requires format 4's reserved padding to be zero, its final start and end
codes to be `0xFFFF`, and each encoding offset to point to its subtable.
Format 0 consists of three 16-bit header fields and 256 glyph bytes, so
12 bytes cannot be its declared length. The 24.04 control has valid format
4 at offset 20, length 32, and format 12 at offset 52, length 2740.

Snowghost's refusal can be traced from these bytes in the unchanged
sources. `compile_character_map` in `renderer/font/cmap.wf` prefers
`(3,10)`, but skips its apparent format 0 because it selects formats 4 or
12. It then selects `(3,1)` format 4. `compile_segments` reads the odd
`idRangeOffset=1` and returns `FontError::Invalid` from its `misplaced`
branch. This is a static trace from the recorded bytes and source;
the face oracle independently reports `refused Invalid`.
`font_set_add` wraps a `load_face` error as `TextError::Invalid`, and
`load_fonts` wraps that as `FontsError::Refused(face)`.

fontTools 4.66.1 fully decompiles the 24.04 control, but rejects the
26.04 file with `Format 0 cmap subtable not 262 bytes`. Chromium
141.0.7390.37 renders 19 glyphs from the 24.04 custom font and rejects
the 26.04 custom font through OpenType Sanitizer with
`Non zero cmap subtable segment padding (65535)`. CDP reports zero custom
glyphs for the latter; any visible text uses fallback fonts. Thus the
26.04 file fails both the specification's concrete requirements and the
requested independent oracles.

## Evidence

[Hosted run 38051009222](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38051009222)
establishes the unchanged-driver reproduction. Exact output lines:

```text
RESULT prepare-26.04 exit=2
STDERR prepare-26.04 layout_oracle: failed: fonts
RESULT prepare-24.04 exit=0
```

Its [artifact](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38051009222/artifacts/11669925187)
records the package downloads and image digests, all 94 per-file records
(size, SHA-256, `file` type and symlink flag), and the prepare stdout/stderr.
The first run stopped after reproduction because the temporary diagnostic
patch expected a semicolon absent from the actual source; the next revision
corrected that text match. Its isolation and browser checks did not run.

[Hosted run 38053630296](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38053630296),
at harness revision `f15fff1b415e69e7c327d8b22640b9a445961202`, records
the raw `cmap` and both independent controls. Exact stdout lines (the
hosting service's step/timestamp prefix is omitted):

```text
OFFENDERS [{"index": 16, "path": "/usr/share/fonts/opentype/unifont/unifont_upper_sample.otf"}]
FACE_ORACLE 26.04 unifont_upper_sample.otf refused Invalid
RAW_CMAP 26.04 unifont_upper_sample.otf size=7838 version=0 records=2 first64=0000000200030001000000140003000a0000002c0004001800000002000200000000fffeffff0000ffff00010000000c000000001e7000000000000002880001
CMAP_RECORD 26.04 unifont_upper_sample.otf record=0 platform=3 encoding=1 offset=20 format=4 length=24 header=0004001800000002000200000000fffe
CMAP_RECORD 26.04 unifont_upper_sample.otf record=1 platform=3 encoding=10 offset=44 format=0 length=12 header=0000000c000000001e70000000000000
FONTTOOLS 26.04 unifont_upper_sample.otf rejected=AssertionError: Format 0 cmap subtable not 262 bytes
CHROMIUM 24.04 face=16 file=unifont_upper_sample.otf status=loaded customGlyphs=19 fonts=[{"familyName":"Unifont Sample","postScriptName":"UnifontSample","isCustomFont":true,"glyphCount":19}]
BROWSER_CONSOLE OTS parsing error: cmap: Non zero cmap subtable segment padding (65535)
CHROMIUM 26.04 face=16 file=unifont_upper_sample.otf status=error customGlyphs=0 fonts=[{"familyName":"WenQuanYi Zen Hei","postScriptName":"WenQuanYiZenHei","isCustomFont":false,"glyphCount":1},{"familyName":"Unifont Upper","postScriptName":"UnifontUpper","isCustomFont":false,"glyphCount":18}]
```

Its [artifact](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38053630296/artifacts/11670683173)
contains all package versions, image digests and 94 file records, both raw
`cmap` binaries, the control's XML, per-probe outputs, browser screenshots
and the diagnostic patch. This run stopped when that diagnostic tried to
read private face fields; the independent font results above completed.

[Hosted run 38054400837](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38054400837)
passed the complete diagnosis at harness revision
`bd01c59d5cfe2127fa9ea881687eee1c0c45f53d`. It repeats reproduction,
all swaps and independent oracles, prints the decoded format-4 fields,
and completes the failure-message diagnostic. Exact stdout lines:

```text
RESULT prepare-26.04 exit=2
STDERR prepare-26.04 layout_oracle: failed: fonts
RESULT prepare-24.04 exit=0
CMAP_FORMAT4 26.04 unifont_upper_sample.otf segCount=1 reservedPad=65535 segments=[{"endCode": 65534, "startCode": 0, "idDelta": 65535, "idRangeOffset": 1}]
RESULT diagnostic-26.04 exit=2
STDERR diagnostic-26.04 layout_oracle: failed: fonts Refused face=16
RESULT diagnostic-control exit=0
RESULT diagnostic-swap-16 exit=2
STDERR diagnostic-swap-16 layout_oracle: failed: fonts Refused face=16
```

The [complete artifact](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38054400837/artifacts/11669979301)
contains all 94 size/hash/type/symlink records in `inventory.txt`, package
versions and Docker digests, per-probe stdout/stderr, raw cmap binaries,
the control's XML, screenshots and `diagnostic.patch`. Every inventoried
file is present and regular, and the offender is well below 256 MiB.

The project gate also passed at this revision:
[38054400801](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38054400801).
Its exact output includes:

```text
dom_selftest: passed
Ran 21 tests in 0.897s
OK
nodes: 7 (base 7, +0)  depth: 1 (base 1, +0)  decisions: 53 (base 53, +0)  rejected: 24 (base 24, +0)
design lint: ok
```

## Review

A separate read-only review examined the complete diagnostic change from
base `65fd29a0139400ca069634bbbfa2ceda9284d65e` through tested harness
`bd01c59d5cfe2127fa9ea881687eee1c0c45f53d`, this report and the cleanup.
Its scope included the affected font loading interfaces, parser path,
relevant design nodes and ancestors, independent specification, workflow,
probe logic and actual hosted results. It checked applicable engineering
and design correspondence rules; no design decisions were changed.
The reviewer ran no builds, tests or timing and reran no green suite.
There were no findings within that scope. The remaining limit is the
package-generation history excluded below.

## Scope and intermediate runs

The comparison is limited to the package versions above, the 47 configured
faces, the pinned compiler and this driver. It does not validate every font
installed by those packages, or diagnose when or where the offending font
was generated. No renderer fix, replacement font or parser workaround was
committed.

Intermediate hosted runs retained their observations but were incomplete:

- [38051684784](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38051684784)
  reproduced both roots, then compilation rejected a local type annotation
  in the temporary diagnostic; module constants replaced it.
- [38052314757](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38052314757)
  reproduced both roots, then compilation rejected diagnostic pattern
  binders matching their field names; distinct binders replaced them.
- [38052806780](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38052806780)
  and [38052844032](https://github.com/Ming-Research/Snowghost-wf/actions/runs/38052844032)
  completed unchanged-driver isolation, then stopped on the independent
  fontTools rejection. The latter also recorded Chromium's rejection.
  The final harness records that known negative oracle result and proceeds
  to the failure-message diagnostic and both browser controls.

The temporary workflow and harness are removed after the diagnosis; their
tested revisions remain in this branch's history and the linked runs.
