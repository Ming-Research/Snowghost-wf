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
	oracle-style-dump oracle-style

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
# them with Chromium's from oracle-style-dump (research/investigations/style).
# It stays out of `check` for the same reasons.
oracle-style: compiler
	@sh $(ROOT)/research/investigations/style/run.sh check

.PHONY: FORCE
FORCE:
