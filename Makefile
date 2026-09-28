# Snowghost's canonical checks. `make check` is the gate a revision passes
# before it merges into main; CI runs the same targets.

PY ?= python3

# Every path is relative to this Makefile, so each target works from any
# working directory.
ROOT := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
WHITEFOOT := $(ROOT)/whitefoot

# The live design trees: every root node file directly under design/ except
# the log, so a tree is linted in the same change that adds it. With none,
# the lint still checks amendments and the log.
DESIGN_TREES := $(filter-out log,$(basename $(notdir $(wildcard $(ROOT)/design/*.md))))

# The revision a design-tree change is reviewed against. CI selects it per
# event with .github/design-review-base.sh.
DESIGN_REVIEW_BASE ?= origin/main

.PHONY: check compiler renderer design-lint design-ready review-scope \
	oracle-data oracle-line-break oracle-css oracle-png oracle-png-speed \
	oracle-normalization

check: compiler renderer design-lint

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

design-lint:
	@$(PY) -B -m unittest discover -s $(ROOT)/design/skill -p 'test_lint.py'
	@$(PY) -B $(ROOT)/design/skill/lint.py --root $(ROOT)/design --trees $(DESIGN_TREES) --base "$(DESIGN_REVIEW_BASE)"

design-ready:
	@$(PY) -B $(ROOT)/design/skill/lint.py --root $(ROOT)/design --trees $(DESIGN_TREES) --base "$(DESIGN_REVIEW_BASE)" --require-no-amendments

review-scope:
	@cd $(ROOT) && sh docs/skills/completion-review/scripts/review-scope.sh

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

oracle-png: $(BUILD)/png_oracle
	@cd $(ROOT) && $< check build/oracle/pngsuite/cases.txt build/oracle/pngsuite

# Decodes the speed set three times with each decoder, single-threaded.
SPEED_SET = $(sort $(wildcard $(ORACLE)/png-speed/*.png))
oracle-png-speed: $(BUILD)/png_oracle $(BUILD)/png-reference
	@cd $(ROOT) && echo libpng: && time -p $(BUILD)/png-reference time 3 $(SPEED_SET:$(ROOT)/%=%)
	@cd $(ROOT) && echo whitefoot: && time -p $(BUILD)/png_oracle time 3 $(SPEED_SET:$(ROOT)/%=%)

.PHONY: FORCE
FORCE:
