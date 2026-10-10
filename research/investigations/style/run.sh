#!/bin/sh
# The harness of the style investigation (DESIGN.md in this directory).
#
#   run.sh check [PAGE...]      builds the style_oracle driver sequentially
#                               and with --par, dumps every page with both,
#                               requires the two dumps to be byte-identical
#                               (criterion 3), compares the dump with
#                               Chromium's (criterion 1) and prints the
#                               parallelism ledger's lines for the stage's
#                               loops and interning calls; it exits with 1
#                               when a page misses criterion 1 or 3
#   run.sh time [PAGE [REPS]]   builds both drivers and times the stage's
#                               parts on every page, or on PAGE (criterion 2)
#
# PAGE is one of ecma262, html5 and apollo11, the real pages of the
# concurrency investigation, or cases, tests/css/style-cases.html (checked,
# not timed); `research/investigations/concurrency/run.sh
# fetch` downloads them and their sheets to build/research/concurrency/, and
# `make oracle-style-dump` writes Chromium's dumps to build/oracle/style/.
#
# time prints, per page, the mode (match, inherited, reset and all, each
# running the stage up to and including that part; MODES overrides the
# list), the build, REPS, T(0)
# and T(REPS) as the best of RUNS runs (five by default) and the per-run time
# (T(REPS) - T(0)) / REPS in seconds: the --par build at WF_WORKERS 1, 2 and
# 4 (WORKERS overrides the list) and the sequential build. A part's time is
# the difference between its mode and the one before it. The timed runs hold
# the host lock RUN_CHECK names, such as Whitefoot's .github/run-check.pl,
# so no other heavy job shares the machine; without RUN_CHECK they run as they
# are, as on a CI runner that runs one job at a time.
#
# PAGES replaces the directory of the real pages and their sheets,
# build/research/concurrency by default; a worktree whose build directory
# links to another checkout's needs a copy outside the link, since the driver
# opens no path through a symbolic link (follow-up
# sg-fraga-host-symlink).
#
# UA replaces the user-agent sheet, a path relative to the repository, for a
# diagnostic run such as the one in runs/ua-table-gray.txt, whose sheet is
# renderer/style/ua.css followed by the line `table { border-color: gray; }`.
#
# The drivers are built with WHITEFOOTC (by default the release whitefoot.pin
# names, which make compiler downloads). POSIX sh plus node and sha256sum.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=${PAGES:-build/research/concurrency}
oracle=build/oracle/style
out=build/research/style
ua=${UA:-renderer/style/ua.css}
compiler=${WHITEFOOTC:-$root/build/whitefoot/$(sed -n "s/^release = //p" "$root/whitefoot.pin")/whitefootc}
lock=${RUN_CHECK:-}
runs=${RUNS:-5}
workers=${WORKERS:-1 2 4}
pages='ecma262 html5 apollo11 cases'
modes=${MODES:-match inherited reset all}

# The sheet mappings of each page's stylesheet links, SUFFIX=SHEET as the
# driver and tests/css/style_oracle.mjs take them.
sheets_of() {
	case $1 in
	ecma262) echo "assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
	html5 | cases) echo "" ;;
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
	cases) echo tests/css/style-cases.html ;;
	*) echo "$data/$1.html" ;;
	esac
}

reps_of() {
	case $1 in
	ecma262) echo 5 ;;
	html5) echo 5 ;;
	apollo11) echo 20 ;;
	esac
}

build() {
	mkdir -p "$out"
	(cd renderer && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --par --par-ledger --graph modules.wfg --entry style_oracle -o ../build/style_oracle_par) >"$out/ledger.txt"
	(cd renderer && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --graph modules.wfg --entry style_oracle -o ../build/style_oracle)
}

check() {
	build
	status=0
	for page in ${*:-$pages}; do
		sheets=$(sheets_of "$page")
		build/style_oracle dump 1 "$(page_file "$page")" "$ua" $sheets >"$out/$page.seq.tsv"
		WF_WORKERS=4 build/style_oracle_par dump 1 "$(page_file "$page")" "$ua" $sheets >"$out/$page.par.tsv"
		if cmp -s "$out/$page.seq.tsv" "$out/$page.par.tsv"; then
			echo "$page: sequential and --par dumps identical, $(sha256sum <"$out/$page.seq.tsv" | cut -c1-16)"
		else
			echo "$page: sequential and --par dumps differ" >&2
			status=1
		fi
		echo "$page: against Chromium"
		node tests/css/style_oracle.mjs compare "$oracle/$page.chromium.tsv" "$out/$page.seq.tsv" || status=1
	done
	echo "parallelism ledger ($out/ledger.txt):"
	grep -E 'PAR split +style\.|pair\(intern_[a-z_]*, intern_[a-z_]*\)' "$out/ledger.txt" || true
	return $status
}

# Prints the elapsed seconds of one run: the sequential build for "seq",
# otherwise the --par build with WF_WORKERS set to the first argument.
elapsed() {
	lanes=$1
	shift
	if [ "$lanes" = seq ]; then
		binary=build/style_oracle
		lanes=1
	else
		binary=build/style_oracle_par
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
		WHITEFOOT_CHECK_TIMEOUT=${WHITEFOOT_CHECK_TIMEOUT:-43200} exec perl "$lock" style-time sh "$here/run.sh" time "$@"
	fi
	if [ -n "${BUILT:-}" ]; then mkdir -p "$out"; else build; fi
	echo "machine: $(uname -srm), $(getconf _NPROCESSORS_ONLN) processors"
	echo "compiler: $compiler $(sha256sum <"$compiler" | cut -c1-16)"
	echo "drivers: $(sha256sum <build/style_oracle_par | cut -c1-16) $(sha256sum <build/style_oracle | cut -c1-16)"
	echo "runs: $runs, commit: $(git rev-parse --short HEAD)"
	echo "page mode build reps T(0) T(REPS) per-run"
	for page in ${1:-ecma262 html5 apollo11}; do
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		counts=$(build/style_oracle all 1 "$file" "$ua" $sheets)
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
time)
	shift
	time_parts "$@"
	;;
*)
	echo "usage: run.sh check [PAGE...] | time [PAGE [REPS]]" >&2
	exit 2
	;;
esac
