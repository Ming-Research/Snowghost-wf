#!/bin/sh
# The harness of the layout investigation (DESIGN.md in this directory).
#
#   run.sh check [PAGE...]      builds the layout_oracle driver sequentially
#                               and with --par, dumps every page with both,
#                               requires the two dumps to be byte-identical
#                               (criterion 3), judges the dump against
#                               Chromium's (criterion 1) and prints the
#                               parallelism ledger's lines for the stage's
#                               loops; it exits with 1 when the dumps differ,
#                               a real page's comparison exits non-zero or a
#                               case page's structure differs from Chromium's
#                               (compare exits 3) or matches fewer boxes or
#                               text nodes than its floor
#   run.sh judge [PAGE...]      judges the dumps already in build/research/
#                               layout against Chromium's, as check does,
#                               without building or dumping
#   run.sh time [PAGE [REPS]]   builds both drivers and times the stage's
#                               parts on every page, or on PAGE (criterion 2)
#
# A real page (ecma262, html5, apollo11) must meet the criterion: compare
# exits 0. A case page (tests/layout/*-cases.html) also probes known gaps, so
# it may miss the criterion, but it must not regress: the table in
# case_floors holds the least number of matched block-level boxes,
# inline-level boxes and text nodes compare reports for each case page, the
# counts when the table was last set. Raise a floor in the change that raises
# the count; lowering one is a decision about the stage.
#
# PAGE is one of ecma262, html5 and apollo11, the real pages of the
# concurrency investigation, or the name of a case page
# tests/layout/NAME.html, such as flow-cases (checked, not timed);
# `research/investigations/concurrency/run.sh fetch` downloads the pages and
# their sheets to build/research/concurrency/, `make oracle-fonts` copies the
# fonts the driver loads to build/fonts, and `make oracle-layout-dump` writes
# Chromium's dumps to build/oracle/layout/.
#
# time prints, per page, the mode (boxes, text and layout, in nested order:
# boxes builds the box tree; text also matches the fonts and prepares every
# paragraph's text, which is font matching, shaping and break opportunities;
# layout also lays the tree out; MODES overrides the list), the build, REPS,
# T(0) and T(REPS) as the best of RUNS runs (five by default) and the per-run
# time (T(REPS) - T(0)) / REPS in seconds: the --par build at WF_WORKERS 1, 2
# and 4 (WORKERS overrides the list) and the sequential build. A part's time
# is the difference between its mode and the one before it: the box tree is
# boxes, the text preparation with the font matching is text minus boxes and
# the layout passes are layout minus text. The timed runs hold the host lock
# RUN_CHECK names, such as Whitefoot's .github/run-check.pl, so no other heavy
# job shares the machine; without RUN_CHECK they run as they are, as on a CI
# runner that runs one job at a time.
#
# PAGES replaces the directory of the real pages and their sheets,
# build/research/concurrency by default; a worktree whose build directory
# links to another checkout's needs a copy outside the link, since the driver
# opens no path through a symbolic link (docs/todo.md, Whitefoot
# requirements).
#
# UA replaces the user-agent sheet, a path relative to the repository, for a
# diagnostic run.
#
# The drivers are built with WHITEFOOTC (by default the release whitefoot.pin
# names, which make compiler downloads). POSIX sh plus node and sha256sum.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=${PAGES:-build/research/concurrency}
oracle=build/oracle/layout
out=build/research/layout
ua=${UA:-renderer/style/ua.css}
compiler=${WHITEFOOTC:-$root/build/whitefoot/$(sed -n "s/^release = //p" "$root/whitefoot.pin")/whitefootc}
lock=${RUN_CHECK:-}
runs=${RUNS:-5}
workers=${WORKERS:-1 2 4}
pages="ecma262 html5 apollo11 $(cd tests/layout && ls *-cases.html | sed 's/\.html$//' | tr '\n' ' ')"
modes=${MODES:-boxes text layout}

# The sheet mappings of each page's stylesheet links, SUFFIX=SHEET as the
# driver and tests/layout/layout_oracle.mjs take them.
sheets_of() {
	case $1 in
	ecma262) echo "assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
	html5 | *-cases) echo "" ;;
	apollo11) echo "wikibase.client.init&only=styles&skin=vector-2022=$data/apollo11-modules.css modules=site.styles&only=styles&skin=vector-2022=$data/apollo11-site.css" ;;
	*)
		echo "run.sh: unknown page $1" >&2
		exit 2
		;;
	esac
}

# Repetitions per page, chosen so the stage dominates T(REPS) at four
# workers.
page_file() {
	case $1 in
	*-cases) echo "tests/layout/$1.html" ;;
	*) echo "$data/$1.html" ;;
	esac
}

reps_of() {
	case $1 in
	ecma262) echo 3 ;;
	html5) echo 3 ;;
	apollo11) echo 10 ;;
	esac
}

build() {
	mkdir -p "$out"
	(cd renderer && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --par --par-ledger --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_par) >"$out/ledger.txt"
	(cd renderer && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle)
}

# The least matched counts of block-level boxes, inline-level boxes and text
# nodes of each case page, as compare prints them ("93/99": matched/judged).
case_floors() {
	case $1 in
	columns-cases) echo "93 2 65" ;;
	flex-cases) echo "259 2 25" ;;
	flow-cases) echo "219 145 294" ;;
	grid-cases) echo "286 2 198" ;;
	table-cases) echo "694 29 306" ;;
	*) echo "" ;;
	esac
}

# Judges the dump of one page against Chromium's: compare's output is shown
# and kept in $out/PAGE.compare.txt; the page fails when compare exits with
# other than 0, when a case page's compare exits with other than 0 or 1 (3 is
# a structure that differs), or when a case page's matched count of a measure
# is below its floor.
judge_page() {
	page=$1
	echo "$page: against Chromium"
	judged=0
	node tests/layout/layout_oracle.mjs compare "$oracle/$page.chromium.tsv" "$out/$page.seq.tsv" >"$out/$page.compare.txt" || judged=$?
	cat "$out/$page.compare.txt"
	case $page in
	*-cases)
		floors=$(case_floors "$page")
		if [ -z "$floors" ]; then
			echo "$page: FAIL, no floor in case_floors" >&2
			return 1
		fi
		if [ "$judged" -gt 1 ]; then
			echo "$page: FAIL, compare exited $judged (3: the structure differs from Chromium's)" >&2
			return 1
		fi
		matched=$(awk '
			/^block-level boxes: / { split($3, n, "/"); blocks = n[1] }
			/^inline-level boxes: / { split($3, n, "/"); inlines = n[1] }
			/^text nodes: / { split($3, n, "/"); texts = n[1] }
			END { print blocks + 0, inlines + 0, texts + 0 }' "$out/$page.compare.txt")
		set -- $floors
		floor_blocks=$1 floor_inlines=$2 floor_texts=$3
		set -- $matched
		failed=0
		if [ "$1" -lt "$floor_blocks" ]; then
			echo "$page: FAIL, $1 block-level boxes match, floor $floor_blocks" >&2
			failed=1
		fi
		if [ "$2" -lt "$floor_inlines" ]; then
			echo "$page: FAIL, $2 inline-level boxes match, floor $floor_inlines" >&2
			failed=1
		fi
		if [ "$3" -lt "$floor_texts" ]; then
			echo "$page: FAIL, $3 text nodes match, floor $floor_texts" >&2
			failed=1
		fi
		return $failed
		;;
	*)
		if [ "$judged" -ne 0 ]; then
			echo "$page: FAIL, compare exited $judged" >&2
			return 1
		fi
		;;
	esac
}

check() {
	build
	status=0
	for page in ${*:-$pages}; do
		sheets=$(sheets_of "$page")
		build/layout_oracle dump 1 "$(page_file "$page")" "$ua" $sheets >"$out/$page.seq.tsv"
		WF_WORKERS=4 build/layout_oracle_par dump 1 "$(page_file "$page")" "$ua" $sheets >"$out/$page.par.tsv"
		if cmp -s "$out/$page.seq.tsv" "$out/$page.par.tsv"; then
			echo "$page: sequential and --par dumps identical, $(sha256sum <"$out/$page.seq.tsv" | cut -c1-16)"
		else
			echo "$page: sequential and --par dumps differ" >&2
			status=1
		fi
		judge_page "$page" || status=1
	done
	echo "parallelism ledger ($out/ledger.txt):"
	grep -E '^PAR split +layout\.' "$out/ledger.txt" || true
	return $status
}

# Prints the elapsed seconds of one run: the sequential build for "seq",
# otherwise the --par build with WF_WORKERS set to the first argument.
elapsed() {
	lanes=$1
	shift
	if [ "$lanes" = seq ]; then
		binary=build/layout_oracle
		lanes=1
	else
		binary=build/layout_oracle_par
	fi
	if ! WF_WORKERS=$lanes command time -p sh -c 'exec "$@" >/dev/null 2>&1' sh "$binary" "$@" 2>"$out/time.txt"; then
		echo "run.sh: $binary $* failed" >&2
		exit 1
	fi
	awk '$1 == "real" { print $2 }' "$out/time.txt"
}

# Prints the least of RUNS elapsed times.
best() {
	times=
	i=0
	while [ "$i" -lt "$runs" ]; do
		seconds=$(elapsed "$@")
		times="$times $seconds"
		i=$((i + 1))
	done
	echo "$times" | awk '{ least = $1; for (i = 2; i <= NF; i++) if ($i < least) least = $i; print least }'
}

time_parts() {
	if [ -n "$lock" ] && [ -z "${WHITEFOOT_CHECK_OWNER:-}" ]; then
		WHITEFOOT_CHECK_TIMEOUT=${WHITEFOOT_CHECK_TIMEOUT:-43200} exec perl "$lock" layout-time sh "$here/run.sh" time "$@"
	fi
	build
	echo "machine: $(uname -srm), $(getconf _NPROCESSORS_ONLN) processors"
	echo "compiler: $(basename "$compiler") $(sha256sum <"$compiler" | cut -c1-16)"
	echo "drivers: $(sha256sum <build/layout_oracle_par | cut -c1-16) $(sha256sum <build/layout_oracle | cut -c1-16)"
	echo "runs: $runs, commit: $(git rev-parse --short HEAD)"
	echo "page mode build reps T(0) T(REPS) per-run"
	for page in ${1:-ecma262 html5 apollo11}; do
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		counts=$(build/layout_oracle layout 1 "$file" "$ua" $sheets)
		echo "# $page: $counts"
		reps=${2:-$(reps_of "$page")}
		for mode in $modes; do
			for lanes in $workers seq; do
				zero=$(best "$lanes" "$mode" 0 "$file" "$ua" $sheets)
				full=$(best "$lanes" "$mode" "$reps" "$file" "$ua" $sheets)
				case $lanes in
				seq) label=seq ;;
				*) label=par-$lanes ;;
				esac
				echo "$page $mode $label $reps $zero $full" | awk '{ printf "%s %s %s %s %s %s %.4f\n", $1, $2, $3, $4, $5, $6, ($6 - $5) / $4 }'
			done
		done
	done
}

case ${1:-} in
check)
	shift
	check "$@"
	;;
judge)
	shift
	status=0
	for page in ${*:-$pages}; do
		judge_page "$page" || status=1
	done
	exit $status
	;;
time)
	shift
	time_parts "$@"
	;;
*)
	echo "usage: run.sh check [PAGE...] | judge [PAGE...] | time [PAGE [REPS]]" >&2
	exit 2
	;;
esac
