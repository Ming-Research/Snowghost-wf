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
#   run.sh profile [PAGE...]    builds both drivers, requires the dump of the
#                               profiled path to equal MODE dump's (and, with
#                               BASE_DRIVERS naming a directory with the
#                               style_oracle of an earlier build, that build's
#                               dump),
#                               runs MODE profile on every page, or on PAGE...,
#                               sequentially and with --par at one and four
#                               workers, and prints each step's time
#                               (the step-timing investigation below), then
#                               the fourth part again through the profiled
#                               copy of interning, step by step and table by
#                               table, with a summary per page and mode
#                               (DESIGN.md, "Interning in parallel")
#   run.sh overhead [PAGE...]   with BASE_DRIVERS naming a directory with the
#                               style_oracle and style_oracle_par of an
#                               earlier build, times MODE match with each build
#                               in turn (RUNS_OVERHEAD rounds, five by default),
#                               to bound what the matcher's counters cost when
#                               they count nothing
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
# profile prints, per page, mode (seq, par1, par4: the sequential build, the
# --par build at WF_WORKERS 1 and 4) and step, the least over RUNS_PROFILE
# processes (three by default) of each process's least time over its repetitions
# (PROFILE_REPS overrides the per-page counts 5, 5 and 10), in milliseconds,
# the spread (the greatest of those over the least), and the share of the
# stage's total, then the matcher's counters, and writes the raw lines to
# build/research/style/profile-*.txt and the table to profile-table.txt. It
# exits with 1 when a dump differs, the identity control fails to differ, the
# ledger does not split match_all, a counter is out of order (matched above
# admitted, admitted above offered) or two runs of one page count differently.
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

# Repetitions of MODE profile per page (the stage's four parts, once each per
# repetition, plus the two steps run alone).
profile_reps_of() {
	case $1 in
	ecma262 | html5) echo "${PROFILE_REPS:-5}" ;;
	apollo11) echo "${PROFILE_REPS:-10}" ;;
	*) echo "${PROFILE_REPS:-5}" ;;
	esac
}

# Prints the step lines of every profile file as one table. The input is
# profile-all.txt, whose lines are the profile output with the page, the mode
# and the run in front.
profile_table() {
	awk '
	BEGIN {
		n = split("match match.rule_index match.positions match.pseudo_flags match.numbering match.allocation match.loop inherited reset intern total alone.positions alone.depth_check intern.prepare intern.setup intern.box intern.size intern.spacing intern.border intern.font intern.text intern.background intern.custom intern.container intern.item intern.table intern.content intern.ids intern.place intern.whole hash.box hash.size hash.spacing hash.border hash.font hash.text hash.background", names, " ")
		t = split("intern.box intern.size intern.spacing intern.border intern.font intern.text intern.background intern.custom intern.container intern.item intern.table intern.content", tables, " ")
		h = split("hash.box hash.size hash.spacing hash.border hash.font hash.text hash.background", hashes, " ")
		m = split("seq par1 par4", modes, " ")
	}
	$4 == "step" {
		key = $1 SUBSEP $2 SUBSEP $5
		pages[$1] = 1
		if (!(key in least) || $7 < least[key]) least[key] = $7
		if (!(key in most) || $7 > most[key]) most[key] = $7
	}
	$4 == "count" { count[$1, $5] = $6 }
	END {
		print "page mode step best_ms spread share_of_total"
		for (page in pages) {
			for (j = 1; j <= m; j++) {
				mode = modes[j]
				total = least[page, mode, "total"]
				for (i = 1; i <= n; i++) {
					key = page SUBSEP mode SUBSEP names[i]
					if (!(key in least)) continue
					spread = (least[key] > 0) ? most[key] / least[key] : 0
					share = (total > 0) ? 100 * least[key] / total : 0
					printf "%s %s %s %.3f %.2f %.1f%%\n", page, mode, names[i], least[key] / 1e6, spread, share
				}
			}
		}
		print ""
		print "page mode whole_ms groups7_ms others5_ms largest_table largest_ms rest_ms hash7_ms stage_intern_ms"
		for (page in pages) {
			for (j = 1; j <= m; j++) {
				mode = modes[j]
				whole = least[page, mode, "intern.whole"]
				if (!(whole > 0)) continue
				groups = 0; others = 0; big = ""; bigv = 0; hashed = 0
				for (i = 1; i <= t; i++) {
					v = least[page, mode, tables[i]]
					if (i <= 7) groups += v; else others += v
					if (v > bigv) { bigv = v; big = tables[i] }
				}
				for (i = 1; i <= h; i++) hashed += least[page, mode, hashes[i]]
				rest = whole - groups - others
				printf "%s %s %.3f %.3f %.3f %s %.3f %.3f %.3f %.3f\n", page, mode, whole / 1e6, groups / 1e6, others / 1e6, big, bigv / 1e6, rest / 1e6, hashed / 1e6, least[page, mode, "intern"] / 1e6
			}
		}
		print ""
		print "page counter value"
		for (key in count) {
			split(key, parts, SUBSEP)
			printf "%s %s %s\n", parts[1], parts[2], count[key]
		}
		print ""
		print "page mode ns_per_offered_item ns_per_admitted_test ns_per_matched"
		for (page in pages) {
			for (j = 1; j <= m; j++) {
				mode = modes[j]
				loop = least[page, mode, "match.loop"]
				offered = count[page, "candidates_sum"]
				admitted = count[page, "admitted_sum"]
				matched = count[page, "matched_sum"]
				if (offered > 0 && admitted > 0 && matched > 0)
					printf "%s %s %.2f %.2f %.2f\n", page, mode, loop / offered, loop / admitted, loop / matched
			}
		}
	}' "$out/profile-all.txt"
}

profile() {
	build
	status=0
	echo "machine: $(uname -srm), $(getconf _NPROCESSORS_ONLN) processors"
	echo "compiler: $compiler $(sha256sum <"$compiler" | cut -c1-16)"
	echo "commit: $(git rev-parse --short HEAD)"
	echo "parallelism ledger ($out/ledger.txt):"
	grep -E 'PAR split +style\.' "$out/ledger.txt" || true
	if ! grep -E 'PAR split +style\.match_all ' "$out/ledger.txt" | grep -v declined | grep -q .; then
		echo "run.sh: the ledger does not split match_all" >&2
		status=1
	fi
	pages_run=${*:-ecma262 html5 apollo11}
	first=
	for page in $pages_run; do
		first=${first:-$page}
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		build/style_oracle dump 1 "$file" "$ua" $sheets >"$out/$page.seq.tsv"
		build/style_oracle profdump 1 "$file" "$ua" $sheets >"$out/$page.prof-seq.tsv"
		WF_WORKERS=4 build/style_oracle_par profdump 1 "$file" "$ua" $sheets >"$out/$page.prof-par.tsv"
		for kind in prof-seq prof-par; do
			if cmp -s "$out/$page.seq.tsv" "$out/$page.$kind.tsv"; then
				echo "$page: $kind dump identical to MODE dump, $(sha256sum <"$out/$page.seq.tsv" | cut -c1-16)"
			else
				echo "$page: $kind dump differs from MODE dump" >&2
				status=1
			fi
		done
		if [ -n "${BASE_DRIVERS:-}" ]; then
			"$BASE_DRIVERS/style_oracle" dump 1 "$file" "$ua" $sheets >"$out/$page.base.tsv"
			if cmp -s "$out/$page.base.tsv" "$out/$page.seq.tsv"; then
				echo "$page: dump identical to the earlier build's, $(sha256sum <"$out/$page.base.tsv" | cut -c1-16)"
			else
				echo "$page: dump differs from the earlier build's" >&2
				status=1
			fi
		fi
	done
	# Control: a user-agent sheet with one more rule must change the dump of the
	# profiled path, or the comparisons above could not have failed. The rule is
	# important: a plain user-agent declaration loses to the page's own sheets
	# (ecma262's sets display on body), an important one beats every origin.
	{ cat "$ua"; printf '\nbody { display: none !important; }\n'; } >"$out/ua-control.css"
	sheets=$(sheets_of "$first")
	file=$(page_file "$first")
	build/style_oracle profdump 1 "$file" "$out/ua-control.css" $sheets >"$out/$first.control.tsv"
	if cmp -s "$out/$first.seq.tsv" "$out/$first.control.tsv"; then
		echo "run.sh: the control dump equals the plain one; the identity check cannot fail" >&2
		status=1
	else
		echo "control: a changed user-agent sheet changes the profiled dump of $first"
	fi
	: >"$out/profile-all.txt"
	for page in $pages_run; do
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		reps=$(profile_reps_of "$page")
		for mode in seq par1 par4; do
			run=1
			while [ "$run" -le "${RUNS_PROFILE:-3}" ]; do
				raw=$out/profile-$page-$mode-$run.txt
				case $mode in
				seq) build/style_oracle profile "$reps" "$file" "$ua" $sheets >"$raw" ;;
				par1) WF_WORKERS=1 build/style_oracle_par profile "$reps" "$file" "$ua" $sheets >"$raw" ;;
				par4) WF_WORKERS=4 build/style_oracle_par profile "$reps" "$file" "$ua" $sheets >"$raw" ;;
				esac
				sed "s/^/$page $mode $run /" "$raw" >>"$out/profile-all.txt"
				run=$((run + 1))
			done
		done
		# The counters do not depend on the build, the workers or the run.
		distinct=$(grep -h '^count ' "$out"/profile-"$page"-*.txt | grep -v '^count reps ' | sort -u | wc -l | tr -d ' ')
		if [ "$distinct" != 9 ]; then
			echo "run.sh: $page: counters differ between runs ($distinct distinct lines, not 9)" >&2
			status=1
		fi
		hists=$(grep -h '^hist ' "$out"/profile-"$page"-*.txt | sort -u | wc -l | tr -d ' ')
		if [ "$hists" != 2 ]; then
			echo "run.sh: $page: histograms differ between runs" >&2
			status=1
		fi
		offered=$(sed -n 's/^count candidates_sum //p' "$out/profile-$page-seq-1.txt")
		admitted=$(sed -n 's/^count admitted_sum //p' "$out/profile-$page-seq-1.txt")
		matched=$(sed -n 's/^count matched_sum //p' "$out/profile-$page-seq-1.txt")
		if [ "$offered" -ge "$admitted" ] && [ "$admitted" -ge "$matched" ] && [ "$matched" -gt 0 ]; then
			echo "$page: counters in order, offered $offered >= admitted $admitted >= matched $matched > 0"
		else
			echo "run.sh: $page: counters out of order: offered $offered admitted $admitted matched $matched" >&2
			status=1
		fi
	done
	profile_table | tee "$out/profile-table.txt"
	return $status
}

# Times MODE match with the earlier build (BASE_DRIVERS) and this one in turn,
# RUNS_OVERHEAD rounds (five by default) of one timed process each, per
# build, worker count and page; prints the least over the rounds per build
# and the ratio of this build's to the earlier one's.
overhead() {
	if [ -z "${BASE_DRIVERS:-}" ]; then
		echo "run.sh: overhead needs BASE_DRIVERS" >&2
		exit 2
	fi
	mkdir -p "$out"
	echo "page workers reps base_s new_s base_twin_s new_over_base"
	for page in ${*:-ecma262 html5 apollo11}; do
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		reps=$(reps_of "$page")
		for lanes in seq 4; do
			round=1
			base_best=
			twin_best=
			new_best=
			while [ "$round" -le "${RUNS_OVERHEAD:-5}" ]; do
				for who in base new twin; do
					case $who in
					new) dir=build ;;
					*) dir=$BASE_DRIVERS ;;
					esac
					if [ "$lanes" = seq ]; then
						binary=$dir/style_oracle
						workers_env=1
					else
						binary=$dir/style_oracle_par
						workers_env=$lanes
					fi
					zero=$(elapsed_of "$workers_env" "$binary" match 0 "$file" "$ua" $sheets)
					full=$(elapsed_of "$workers_env" "$binary" match "$reps" "$file" "$ua" $sheets)
					stage=$(echo "$zero $full $reps" | awk '{ printf "%.4f", ($2 - $1) / $3 }')
					case $who in
					base) base_best=$(least_of "$base_best" "$stage") ;;
					new) new_best=$(least_of "$new_best" "$stage") ;;
					twin) twin_best=$(least_of "$twin_best" "$stage") ;;
					esac
				done
				round=$((round + 1))
			done
			echo "$page $lanes $reps $base_best $new_best $twin_best" | awk '{ printf "%s %s %s %s %s %s %.3f\n", $1, $2, $3, $4, $5, $6, $5 / $4 }'
		done
	done
}

# Prints the elapsed seconds of one run of binary, with WF_WORKERS set to lanes.
elapsed_of() {
	lanes=$1
	binary=$2
	shift 2
	if ! WF_WORKERS=$lanes command time -p sh -c 'exec "$@" >/dev/null 2>&1' sh "$binary" "$@" 2>"$out/time.txt"; then
		echo "run.sh: $binary $* failed" >&2
		exit 1
	fi
	awk '$1 == "real" { print $2 }' "$out/time.txt"
}

# Prints the lesser of two numbers, the second alone when the first is empty.
least_of() {
	if [ -z "$1" ]; then
		echo "$2"
	else
		echo "$1 $2" | awk '{ print ($2 < $1) ? $2 : $1 }'
	fi
}

case ${1:-} in
profile)
	shift
	profile "$@"
	;;
overhead)
	shift
	overhead "$@"
	;;
check)
	shift
	check "$@"
	;;
time)
	shift
	time_parts "$@"
	;;
*)
	echo "usage: run.sh check [PAGE...] | time [PAGE [REPS]] | profile [PAGE...] | overhead [PAGE...]" >&2
	exit 2
	;;
esac
