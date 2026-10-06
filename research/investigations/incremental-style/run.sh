#!/bin/sh
# The harness of M1 (DESIGN.md in this directory).
#
#   run.sh scripts PAGE...          writes, under build/m1/scripts/, each
#                                   page's classes and body edit scripts
#                                   (scripts/classes.py) from X5's node
#                                   listing (incremental-layout/run.sh
#                                   prepare)
#   run.sh restyle PAGE KIND...     runs the style oracle's restyle check
#                                   (build/m1/style_seq, or STYLE) on
#                                   PAGE-KIND.edits from build/x5/scripts
#                                   or build/m1/scripts, keeps its lines in
#                                   build/m1/restyle/PAGE-KIND.txt and
#                                   prints the edits, those with an element
#                                   missing from the restyle set, the full
#                                   sets and the sizes of the sets against
#                                   the elements rematched; fails when an
#                                   element is missing
#   run.sh structure PAGE KIND...  keeps stable style slots across B/X edits and
#                                   compares every element with a fresh computation
#                                   by NodeId (structure_restyle); fails on a difference
#   run.sh reach PAGE KIND...      checks B/X restyle completeness (structural_restyle);
#                                   also accepts PAGE structure, KIND case or full, and
#                                   PAGE sides, KIND case, for fixtures
#   run.sh incremental PAGE KIND... runs the style oracle's incremental check
#                                   (restyle on a kept state against a full
#                                   style run after every C and K edit) and
#                                   prints the edits, those whose styles
#                                   differ, those rebuilt and the elements
#                                   visited; fails when any differ
#
# PAGE is ecma262, html5 or apollo11, with the inputs of X5's run.sh;
# apollo11 is the supplementary capture in build/x5/apollo-supplement. The
# style oracle is built by
#   cd renderer && whitefootc --cache ../build/whitefoot-cache --fragments function --graph modules.wfg --entry style_oracle -o ../build/m1/style_seq
# under the host-wide lock. POSIX sh plus python3.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=${PAGES:-build/research/concurrency}
apollo=${PAGES:-build/x5/apollo-supplement}
ua=renderer/style/ua.css
work=build/m1
cases=research/investigations/incremental-style/scripts

page_args() {
	case $1 in
	ecma262) echo "$data/ecma262.html $ua assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
	html5) echo "$data/html5.html $ua" ;;
	structure) echo "$cases/structure-case.html $ua" ;;
	sides) echo "$cases/sides-case.html $ua" ;;
	apollo11) echo "$apollo/apollo11.html $ua wikibase.client.init&only=styles&skin=vector-2022=$apollo/apollo11-modules.css modules=site.styles&only=styles&skin=vector-2022=$apollo/apollo11-site.css" ;;
	*)
		echo "run.sh: unknown page $1" >&2
		exit 2
		;;
	esac
}

sheet_files() {
	case $1 in
	ecma262) echo "$data/ecma262-ecmarkup.css $data/ecma262-print.css" ;;
	html5) echo "" ;;
	apollo11) echo "$apollo/apollo11-modules.css $apollo/apollo11-site.css" ;;
	esac
}

scripts() {
	mkdir -p "$work/scripts"
	for page in "$@"; do
		# shellcheck disable=SC2046
		python3 "$here/scripts/classes.py" "$page" "build/x5/$page.nodes" "$work/scripts" $(sheet_files "$page")
	done
}

restyle() {
	page=$1
	shift
	mkdir -p "$work/restyle"
	status=0
	for kind in "$@"; do
		script=build/x5/scripts/$page-$kind.edits
		[ -f "$script" ] || script=$work/scripts/$page-$kind.edits
		out=$work/restyle/$page-$kind.txt
		# shellcheck disable=SC2046
		"${STYLE:-$work/style_seq}" restyle "$script" $(page_args "$page") >"$out"
		awk -v name="$page-$kind" '
			/^restyle/ {
				edits++
				for (i = 3; i < NF; i++) {
					if ($i == "set") set += $(i + 1)
					if ($i == "rematched") rematched += $(i + 1)
					if ($i == "missing" && $(i + 1) > 0) missing++
				}
				if ($3 == "full") full++
			}
			END { printf "%s: %d edits, %d missing an element, %d full, set total %d, rematched total %d\n", name, edits, missing, full, set, rematched; exit (missing > 0) }
		' "$out" || status=1
	done
	return $status
}

structure() {
	page=$1
	shift
	mkdir -p "$work/structure"
	status=0
	for kind in "$@"; do
		script=build/x5/scripts/$page-$kind.edits
		[ -f "$script" ] || script=$work/scripts/$page-$kind.edits
		[ -f "$script" ] || script=$cases/$page-$kind.edits
		out=$work/structure/$page-$kind.txt
		# shellcheck disable=SC2046
		"${STYLE:-$work/style_seq}" structure "$script" $(page_args "$page") >"$out" || status=1
		awk -v name="$page-$kind" '/^structure edits/ { print name ": " $3 " edits, " $5 " differ, " $7 " fallbacks"; found = 1 } END { exit !found }' "$out" || status=1
	done
	return $status
}

reach() {
	page=$1
	shift
	mkdir -p "$work/reach"
	status=0
	for kind in "$@"; do
		script=build/x5/scripts/$page-$kind.edits
		[ -f "$script" ] || script=$work/scripts/$page-$kind.edits
		[ -f "$script" ] || script=$cases/$page-$kind.edits
		out=$work/reach/$page-$kind.txt
		# Keep the summary even when the oracle exits nonzero for missing nodes.
		# shellcheck disable=SC2046
		"${STYLE:-$work/style_seq}" reach "$script" $(page_args "$page") >"$out" || status=1
		awk -v name="$page-$kind" '
			/^reach/ {
				edits++
				for (i = 3; i < NF; i++) {
					if ($i == "set") { total += $(i + 1); if (partial++ == 0 || $(i + 1) < lo) lo = $(i + 1); if ($(i + 1) > hi) hi = $(i + 1) }
					if ($i == "changed") changed += $(i + 1)
					if ($i == "missing") { missing += $(i + 1); if ($(i + 1) > 0) missed++ }
				}
				if ($3 == "full") full++
			}
			END { printf "%s: %d edits, %d missing an element, %d full, set total %d (min %d max %d), changed total %d, missing total %d\n", name, edits, missed, full, total, lo, hi, changed, missing; exit (missing > 0 || edits == 0) }
		' "$out" || status=1
	done
	return $status
}

incremental() {
	page=$1
	shift
	mkdir -p "$work/incremental"
	status=0
	for kind in "$@"; do
		script=build/x5/scripts/$page-$kind.edits
		[ -f "$script" ] || script=$work/scripts/$page-$kind.edits
		out=$work/incremental/$page-$kind.txt
		# shellcheck disable=SC2046
		"${STYLE:-$work/style_seq}" incremental "$script" $(page_args "$page") >"$out"
		awk -v name="$page-$kind" '
			/^restyle/ {
				edits++
				for (i = 3; i < NF; i++) {
					if ($i == "visited") visited += $(i + 1)
					if ($i == "differ" && $(i + 1) > 0) differ++
				}
				for (i = 3; i <= NF; i++) if ($i == "rebuilt") rebuilt++
			}
			END { printf "%s: %d edits, %d differ, %d rebuilt, %d elements visited\n", name, edits, differ, rebuilt, visited; exit (differ > 0 || edits == 0) }
		' "$out" || status=1
	done
	return $status
}

command=${1:-}
[ $# -gt 0 ] && shift
case $command in
scripts) scripts "$@" ;;
restyle) restyle "$@" ;;
structure) structure "$@" ;;
reach) reach "$@" ;;
incremental) incremental "$@" ;;
*)
	echo "usage: run.sh scripts|restyle|structure|incremental ..." >&2
	exit 2
	;;
esac
