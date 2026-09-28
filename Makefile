# Snowghost's canonical checks. `make check` is the gate a revision passes
# before it merges into main; CI runs the same targets.

PY ?= python3
WHITEFOOT := whitefoot

# The live design trees, by root node name. A change that adds a tree's root
# node adds its name here in the same change; with none, the lint still
# checks amendments and the log.
DESIGN_TREES :=

# The revision a design-tree change is reviewed against. CI selects it per
# event with .github/design-review-base.sh.
DESIGN_REVIEW_BASE ?= origin/main

.PHONY: check compiler design-lint design-ready review-scope

check: compiler design-lint

# Builds the pinned compiler with Whitefoot's own build target, which
# leaves it at whitefoot/compiler/target/gate/whitefootc.
compiler:
	@test -f $(WHITEFOOT)/compiler/Cargo.toml || { \
		echo "the whitefoot submodule is not checked out: git submodule update --init" >&2; \
		exit 1; }
	@$(MAKE) --no-print-directory -C $(WHITEFOOT)/compiler build

design-lint:
	@$(PY) -B -m unittest discover -s design/skill -p 'test_lint.py'
	@$(PY) -B design/skill/lint.py --root design --trees $(DESIGN_TREES) --base "$(DESIGN_REVIEW_BASE)"

design-ready:
	@$(PY) -B design/skill/lint.py --root design --trees $(DESIGN_TREES) --base "$(DESIGN_REVIEW_BASE)" --require-no-amendments

review-scope:
	@sh docs/skills/completion-review/scripts/review-scope.sh
