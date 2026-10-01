# Snowghost's canonical checks. `make check` is the gate a revision passes
# before it merges into main; CI runs the same targets.

PY ?= python3
NODE ?= node

# Every path is relative to this Makefile, so each target works from any
# working directory.
ROOT := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
WHITEFOOT := $(ROOT)/whitefoot

# The live design trees: every root node file directly under design/ except
# the log, so a tree is linted in the same change that adds it.
DESIGN_TREES := $(filter-out log,$(basename $(notdir $(wildcard $(ROOT)/design/*.md))))

# The revision a design-tree change is reviewed against. CI selects it per
# event with .github/design-review-base.sh.
DESIGN_REVIEW_BASE ?= origin/main

.PHONY: check compiler renderer design-lint design-ready \
	static-atoms dom-selftest \
	oracle-data oracle-line-break oracle-css oracle-css-rules oracle-css-color oracle-css-selectors oracle-html-tokenizer oracle-html-tree \
	oracle-png oracle-png-speed \
	oracle-normalization oracle-idna oracle-url oracle-font-face oracle-font-shape oracle-text-properties \
	oracle-style-dump oracle-style oracle-layout-dump oracle-fonts oracle-text

check: compiler renderer dom-selftest design-lint

# Builds the pinned compiler with Whitefoot's own build target, which
# leaves it at whitefoot/compiler/target/gate/whitefootc.
compiler:
	@test -f $(WHITEFOOT)/compiler/Cargo.toml || { \
		echo "the whitefoot submodule is not checked out: git submodule update --init" >&2; \
		exit 1; }
	@$(MAKE) --no-print-directory -C $(WHITEFOOT)/compiler build

WHITEFOOTC := $(WHITEFOOT)/compiler/target/gate/whitefootc
BUILD := $(ROOT)/build
ORACLE := $(BUILD)/oracle

# Checks every renderer module against its interface; a module whose
# functions are declared but not yet written passes as pending. Each module
# is checked alone because --check-modules also composes every entry, and an
# entry cannot compose while a module it calls is pending.
RENDERER_MODULES = $(shell sed -n 's/^\(pkg[a-z_:]*\):.*/\1/p' $(ROOT)/renderer/modules.wfg)
renderer: compiler
	@cd $(ROOT)/renderer && for module in $(RENDERER_MODULES); do \
		$(WHITEFOOTC) --graph modules.wfg --check-module $$module || exit 1; done

# Regenerates pkg::base::static_atoms from its name list with the
# static_atoms tool; the record is replaced only when the tool succeeds.
static-atoms: $(BUILD)/static_atoms
	@cd $(ROOT)/renderer && $< < tools/static_atoms/names.txt > $(BUILD)/static_atoms.wfm
	@mv $(BUILD)/static_atoms.wfm $(ROOT)/renderer/base/static_atoms/module.wfm

# Builds the document arena and atom self-test and runs it; it exits with 0
# only when every check passes.
dom-selftest: $(BUILD)/dom_selftest
	@$<

$(BUILD)/static_atoms $(BUILD)/dom_selftest: compiler FORCE
	@mkdir -p $(BUILD)
	@cd $(ROOT)/renderer && $(WHITEFOOTC) --graph modules.wfg --entry $(notdir $@) -o $@

design-lint:
	@$(PY) -B -m unittest discover -s $(ROOT)/design/skill -p 'test_lint.py'
	@$(PY) -B $(ROOT)/design/skill/lint.py --root $(ROOT)/design --trees $(DESIGN_TREES) --base "$(DESIGN_REVIEW_BASE)"

design-ready:
	@$(PY) -B $(ROOT)/design/skill/lint.py --root $(ROOT)/design --trees $(DESIGN_TREES) --base "$(DESIGN_REVIEW_BASE)" --require-approval

# The agent writer trial's oracles (research/investigations/agent-writer-trial).
# They need network access, libpng and a C compiler, and stay out of `check`.
$(BUILD)/png-reference: $(ROOT)/tests/png/reference.c
	@mkdir -p $(BUILD)
	@$(CC) -O2 -Wall -Wextra -o $@ $< $$(pkg-config --cflags --libs libpng)

oracle-data: $(BUILD)/png-reference
	@sh $(ROOT)/tests/oracle-data.sh $(ORACLE) $(BUILD)/png-reference

$(BUILD)/%_oracle: compiler FORCE
	@cd $(ROOT)/renderer && $(WHITEFOOTC) --graph modules.wfg --entry $*_oracle -o $@

oracle-line-break: $(BUILD)/line_break_oracle
	@cd $(ROOT) && $< build/oracle/ucd/LineBreakTest.txt

oracle-normalization: $(BUILD)/normalization_oracle
	@cd $(ROOT) && $< build/oracle/ucd/NormalizationTest.txt

oracle-css: $(BUILD)/css_syntax_oracle
	@cd $(ROOT) && $(PY) -B tests/css/oracle.py build/oracle/css/component_value_list.json $<

oracle-html-tokenizer: $(BUILD)/html_tokenizer_oracle
	@cd $(ROOT) && $(PY) -B tests/html/oracle.py build/oracle/html5lib $<

oracle-html-tree: $(BUILD)/html_tree_oracle
	@cd $(ROOT) && $(PY) -B tests/html/tree_oracle.py build/oracle/wpt-parsing $< tests/html/tree-local.dat

oracle-css-rules: $(BUILD)/css_rules_oracle
	@cd $(ROOT) && $(PY) -B tests/css/rules_oracle.py build/oracle/css $<

oracle-css-color: $(BUILD)/css_color_oracle
	@cd $(ROOT) && $(PY) -B tests/css/color_oracle.py build/oracle/css $<

oracle-css-selectors: $(BUILD)/css_selectors_oracle
	@cd $(ROOT) && $(PY) -B tests/css/selectors_oracle.py build/oracle/wpt-nodes build/oracle/css $<

oracle-font-face: $(BUILD)/font_face_oracle
	@cd $(ROOT) && $(PY) -B tests/font/face_oracle.py build/oracle/fonts build/oracle/py $<

oracle-font-shape: $(BUILD)/font_shape_oracle
	@cd $(ROOT) && $(PY) -B tests/font/shape_oracle.py build/oracle/fonts build/oracle/udhr build/oracle/py $<

oracle-text-properties: $(BUILD)/text_properties_oracle
	@cd $(ROOT) && $(PY) -B tests/text/properties_oracle.py build/oracle/ucd $<

oracle-png: $(BUILD)/png_oracle
	@cd $(ROOT) && $< check build/oracle/pngsuite/cases.txt build/oracle/pngsuite

oracle-idna: $(BUILD)/idna_oracle
	@cd $(ROOT) && $(PY) -B tests/text/idna_oracle.py build/oracle/idna/IdnaTestV2.txt $<

oracle-url: $(BUILD)/url_oracle
	@cd $(ROOT) && $(PY) -B tests/url/oracle.py build/oracle/wpt-url $<

# Decodes the speed set three times with each decoder, single-threaded.
SPEED_SET = $(sort $(wildcard $(ORACLE)/png-speed/*.png))
oracle-png-speed: $(BUILD)/png_oracle $(BUILD)/png-reference
	@cd $(ROOT) && echo libpng: && time -p $(BUILD)/png-reference time 3 $(SPEED_SET:$(ROOT)/%=%)
	@cd $(ROOT) && echo whitefoot: && time -p $(BUILD)/png_oracle time 3 $(SPEED_SET:$(ROOT)/%=%)

# Dumps Chromium's computed values of the style stage's longhands for the
# three real pages of the concurrency investigation and for
# tests/css/style-cases.html, the oracle of the style
# stage (research/investigations/style). It needs Chromium and Playwright
# (tests/css/style_oracle.mjs names their paths) and the pages fetched by
# research/investigations/concurrency/run.sh fetch; it stays out of `check`.
STYLE_PAGES := $(BUILD)/research/concurrency
STYLE_ORACLE := $(ORACLE)/style
oracle-style-dump:
	@mkdir -p $(STYLE_ORACLE)
	@cd $(ROOT) && $(NODE) tests/css/style_oracle.mjs dump $(STYLE_PAGES)/ecma262.html \
		assets/css/ecmarkup.css=$(STYLE_PAGES)/ecma262-ecmarkup.css \
		assets/css/print.css=$(STYLE_PAGES)/ecma262-print.css \
		> $(STYLE_ORACLE)/ecma262.chromium.tsv.part
	@mv $(STYLE_ORACLE)/ecma262.chromium.tsv.part $(STYLE_ORACLE)/ecma262.chromium.tsv
	@cd $(ROOT) && $(NODE) tests/css/style_oracle.mjs dump $(STYLE_PAGES)/html5.html \
		> $(STYLE_ORACLE)/html5.chromium.tsv.part
	@mv $(STYLE_ORACLE)/html5.chromium.tsv.part $(STYLE_ORACLE)/html5.chromium.tsv
	@cd $(ROOT) && $(NODE) tests/css/style_oracle.mjs dump $(STYLE_PAGES)/apollo11.html \
		'wikibase.client.init&only=styles&skin=vector-2022=$(STYLE_PAGES)/apollo11-modules.css' \
		'modules=site.styles&only=styles&skin=vector-2022=$(STYLE_PAGES)/apollo11-site.css' \
		> $(STYLE_ORACLE)/apollo11.chromium.tsv.part
	@mv $(STYLE_ORACLE)/apollo11.chromium.tsv.part $(STYLE_ORACLE)/apollo11.chromium.tsv
	@cd $(ROOT) && $(NODE) tests/css/style_oracle.mjs dump tests/css/style-cases.html \
		> $(STYLE_ORACLE)/cases.chromium.tsv.part
	@mv $(STYLE_ORACLE)/cases.chromium.tsv.part $(STYLE_ORACLE)/cases.chromium.tsv

# Builds the style_oracle driver sequentially and with --par, dumps the three
# real pages with both, requires the two dumps to be identical and compares
# them with Chromium's from oracle-style-dump (research/investigations/style);
# it fails while a page misses the 99 percent criterion. It stays out of
# `check` for the same reasons.
oracle-style: compiler
	@sh $(ROOT)/research/investigations/style/run.sh check

# Dumps Chromium's boxes and text fragments for the three real pages of the
# concurrency investigation, the oracle of the layout stage
# (research/investigations/layout), with tests/layout/layout_oracle.mjs. It
# needs what oracle-style-dump needs and stays out of `check`.
LAYOUT_ORACLE := $(ORACLE)/layout
oracle-layout-dump:
	@mkdir -p $(LAYOUT_ORACLE)
	@cd $(ROOT) && $(NODE) tests/layout/layout_oracle.mjs dump $(STYLE_PAGES)/ecma262.html \
		assets/css/ecmarkup.css=$(STYLE_PAGES)/ecma262-ecmarkup.css \
		assets/css/print.css=$(STYLE_PAGES)/ecma262-print.css \
		> $(LAYOUT_ORACLE)/ecma262.chromium.tsv.part
	@mv $(LAYOUT_ORACLE)/ecma262.chromium.tsv.part $(LAYOUT_ORACLE)/ecma262.chromium.tsv
	@cd $(ROOT) && $(NODE) tests/layout/layout_oracle.mjs dump $(STYLE_PAGES)/html5.html \
		> $(LAYOUT_ORACLE)/html5.chromium.tsv.part
	@mv $(LAYOUT_ORACLE)/html5.chromium.tsv.part $(LAYOUT_ORACLE)/html5.chromium.tsv
	@cd $(ROOT) && $(NODE) tests/layout/layout_oracle.mjs dump $(STYLE_PAGES)/apollo11.html \
		'wikibase.client.init&only=styles&skin=vector-2022=$(STYLE_PAGES)/apollo11-modules.css' \
		'modules=site.styles&only=styles&skin=vector-2022=$(STYLE_PAGES)/apollo11-site.css' \
		> $(LAYOUT_ORACLE)/apollo11.chromium.tsv.part
	@mv $(LAYOUT_ORACLE)/apollo11.chromium.tsv.part $(LAYOUT_ORACLE)/apollo11.chromium.tsv

# Copies the installed faces the reference draws with on the oracle's host
# into build/fonts, where pkg::oracle::fonts::load_fonts reads them in the
# fallback order its interface documents; they are copied, not linked,
# because std::fs opens no symbolic link.
FONT_DIR := $(BUILD)/fonts
SYSTEM_FONTS := /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
	/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc \
	/usr/share/fonts/opentype/tlwg/Loma.otf \
	/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf \
	/usr/share/fonts/truetype/freefont/FreeSans.ttf \
	/usr/share/fonts/truetype/freefont/FreeSerif.ttf \
	/usr/share/fonts/truetype/freefont/FreeMono.ttf \
	/usr/share/fonts/truetype/libreoffice/opens___.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf \
	/usr/share/fonts/opentype/unifont/unifont.otf \
	/usr/share/fonts/opentype/unifont/unifont_jp.otf \
	/usr/share/fonts/opentype/unifont/unifont_sample.otf \
	/usr/share/fonts/opentype/unifont/unifont_csur.otf \
	/usr/share/fonts/opentype/unifont/unifont_upper.otf \
	/usr/share/fonts/opentype/unifont/unifont_upper_sample.otf \
	/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf \
	/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf \
	/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf \
	/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf \
	/usr/share/fonts/truetype/liberation/LiberationMono-Italic.ttf \
	/usr/share/fonts/truetype/liberation/LiberationMono-BoldItalic.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSansMono-BoldOblique.ttf \
	/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf \
	/usr/share/fonts/truetype/freefont/FreeSansBold.ttf \
	/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf \
	/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf \
	/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf \
	/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf \
	/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf \
	/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf \
	/usr/share/fonts/truetype/freefont/FreeMonoOblique.ttf \
	/usr/share/fonts/truetype/freefont/FreeMonoBoldOblique.ttf \
	/usr/share/fonts/opentype/tlwg/Loma-Bold.otf \
	/usr/share/fonts/opentype/tlwg/Loma-Oblique.otf \
	/usr/share/fonts/opentype/tlwg/Loma-BoldOblique.otf \
	/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf
oracle-fonts:
	@mkdir -p $(FONT_DIR)
	@cp $(SYSTEM_FONTS) $(FONT_DIR)/

# The oracle of the layout stage's text preparation
# (research/investigations/layout, "Text preparation results"): draws 1,000
# text cases from each of the three real pages, adds the extents and break
# cases, measures them all in Chromium with tests/layout/text_oracle.mjs,
# runs the text_oracle driver on the same cases and compares the two. It
# needs what oracle-style-dump needs and the installed fonts, and stays out
# of `check`; it fails while fewer than 99 percent of the widths match.
TEXT_ORACLE := $(ORACLE)/text
oracle-text: oracle-fonts $(BUILD)/text_oracle
	@mkdir -p $(TEXT_ORACLE)
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs cases e 1000 $(STYLE_PAGES)/ecma262.html \
		assets/css/ecmarkup.css=$(STYLE_PAGES)/ecma262-ecmarkup.css \
		assets/css/print.css=$(STYLE_PAGES)/ecma262-print.css > $(TEXT_ORACLE)/ecma262.cases
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs cases h 1000 $(STYLE_PAGES)/html5.html > $(TEXT_ORACLE)/html5.cases
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs cases a 1000 $(STYLE_PAGES)/apollo11.html \
		'wikibase.client.init&only=styles&skin=vector-2022=$(STYLE_PAGES)/apollo11-modules.css' \
		'modules=site.styles&only=styles&skin=vector-2022=$(STYLE_PAGES)/apollo11-site.css' > $(TEXT_ORACLE)/apollo11.cases
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs extents > $(TEXT_ORACLE)/extents.cases
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs breaks > $(TEXT_ORACLE)/breaks.cases
	@cd $(TEXT_ORACLE) && cat ecma262.cases html5.cases apollo11.cases extents.cases breaks.cases > cases.tsv
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs measure $(TEXT_ORACLE)/cases.tsv > $(TEXT_ORACLE)/chromium.tsv
	@cd $(ROOT) && $(BUILD)/text_oracle build/fonts build/oracle/text/cases.tsv > $(TEXT_ORACLE)/snowghost.tsv
	@cd $(ROOT) && $(NODE) tests/layout/text_oracle.mjs compare $(TEXT_ORACLE)/cases.tsv $(TEXT_ORACLE)/chromium.tsv $(TEXT_ORACLE)/snowghost.tsv

.PHONY: FORCE
FORCE:
