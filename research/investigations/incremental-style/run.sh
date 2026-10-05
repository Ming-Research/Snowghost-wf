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

data=build/research/concurrency
apollo=build/x5/apollo-supplement
ua=renderer/style/ua.css
work=build/m1

page_args() {
	case $1 in
	ecma262) echo "$data/ecma262.html $ua assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
	html5) echo "$data/html5.html $ua" ;;
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
				if ($NF == "rebuilt") rebuilt++
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
incremental) incremental "$@" ;;
*)
	echo "usage: run.sh scripts|restyle|incremental ..." >&2
	exit 2
	;;
esac
