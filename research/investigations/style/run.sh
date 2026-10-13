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
#   run.sh compare [PAGE...]    with BASE_DRIVERS naming a directory with the
#                               style_oracle, style_oracle_par and ledger.txt
#                               of an earlier build by the same compiler,
#                               builds this one (unless BUILT is set), requires
#                               its dumps and distinct counts to equal the
#                               earlier build's, checks that the ledger
#                               permits the seven hashing loops, reports which
#                               value groups' calls each build offers, and
#                               times the stage's interning with the earlier
#                               build, this one, a copy of the earlier build
#                               (the twin) and, with BONLY_DRIVERS, this
#                               revision with the seven calls kept apart, in
#                               interleaved rounds (DESIGN.md, "Hashing
#                               outside the chain (B)" and "Attributing the
#                               four-worker gain")
#   run.sh identity DIR [PAGE...]
#                               with BASE_DRIVERS as for compare, requires the
#                               dumps and distinct counts of the drivers in
#                               DIR to equal the earlier build's
#   run.sh falsify [PAGE]       after profile, shows that its counter and
#                               ledger checks fail on deliberately wrong
#                               copies of PAGE's files (apollo11 by default)
#
# profile, overhead and falsify serve the step-timing investigation of
# DESIGN.md and are one-shot: overhead compares this source with an earlier
# build (BASE_DRIVERS, origin/main's in the temporary workflow
# style-build-timing), which becomes a comparison of a build with itself once
# this source is on main, and profile's comparison with BASE_DRIVERS likewise.
# They are kept to repeat the investigation at the commit it records.
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
# ledger does not split both instances of match_all (the stage's, which does
# not count, and the profiled path's), a counter is out of order (matched
# above admitted, admitted above offered, or none matched) or two runs of one
# page count differently.
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

# Exits with 1 unless the ledger FILE splits the loop of every instance of
# match_all, and names at least two: the stage's (tally_none) and the
# profiled path's (tally_count). A generic function's instance is named
# style.match_all$instance$SUFFIX in the ledger.
ledger_check() {
	instances=$(grep -oE 'style\.match_all(\$instance\$[0-9a-f]+)? ' "$1" | sort -u | wc -l | tr -d ' ')
	split=$(grep -E 'PAR split +style\.match_all(\$instance\$[0-9a-f]+)? ' "$1" | grep -v declined | grep -oE 'style\.match_all(\$instance\$[0-9a-f]+)? ' | sort -u | wc -l | tr -d ' ')
	if [ "$instances" -ge 2 ] && [ "$split" = "$instances" ]; then
		echo "ledger: all $instances instances of match_all split"
		return 0
	fi
	echo "run.sh: the ledger does not split every instance of match_all ($split of $instances, at least 2 expected); its lines naming match_all:" >&2
	grep 'match_all' "$1" >&2 || true
	return 1
}

# Exits with 1 unless the profile files DIR/profile-PAGE-*.txt count alike in
# every build, worker count and run (9 distinct count lines, the repetitions
# aside, and 2 histogram lines), and the counts of the first sequential run
# are in order: offered >= admitted >= matched > 0.
counter_check() {
	profiles=$1
	page=$2
	counted=0
	distinct=$(grep -h '^count ' "$profiles"/profile-"$page"-*.txt | grep -v '^count reps ' | sort -u | wc -l | tr -d ' ')
	if [ "$distinct" != 9 ]; then
		echo "run.sh: $page: counters differ between runs ($distinct distinct lines, not 9)" >&2
		counted=1
	fi
	hists=$(grep -h '^hist ' "$profiles"/profile-"$page"-*.txt | sort -u | wc -l | tr -d ' ')
	if [ "$hists" != 2 ]; then
		echo "run.sh: $page: histograms differ between runs" >&2
		counted=1
	fi
	offered=$(sed -n 's/^count candidates_sum //p' "$profiles/profile-$page-seq-1.txt")
	admitted=$(sed -n 's/^count admitted_sum //p' "$profiles/profile-$page-seq-1.txt")
	matched=$(sed -n 's/^count matched_sum //p' "$profiles/profile-$page-seq-1.txt")
	if [ "$offered" -ge "$admitted" ] && [ "$admitted" -ge "$matched" ] && [ "$matched" -gt 0 ]; then
		echo "$page: counters in order, offered $offered >= admitted $admitted >= matched $matched > 0"
	else
		echo "run.sh: $page: counters out of order: offered $offered admitted $admitted matched $matched" >&2
		counted=1
	fi
	return $counted
}

# The falsifiers of ledger_check and counter_check, run after `run.sh
# profile` has profiled PAGE (apollo11 by default): both checks must pass on
# that run's files, and each must fail, with the message of its fault, on a
# copy with one deliberate fault: one run counting differently, one histogram
# differing, admitted above offered, matched above admitted, nothing matched,
# one instance of match_all declined, and only one instance in the ledger.
falsify() {
	page=${1:-apollo11}
	if ! counter_check "$out" "$page" || ! ledger_check "$out/ledger.txt"; then
		echo "run.sh: falsify: the checks fail on the unmodified files of $page; run run.sh profile $page first" >&2
		return 1
	fi
	result=0
	# expect CASE PATTERN COMMAND...: COMMAND must exit with 1 and print PATTERN.
	expect() {
		name=$1
		pattern=$2
		shift 2
		if "$@" >"$out/falsify-$name.txt" 2>&1; then
			echo "run.sh: falsify: $name passed; the check cannot see this fault" >&2
			result=1
		elif grep -q "$pattern" "$out/falsify-$name.txt"; then
			echo "falsify: $name fails as it should: $(grep "$pattern" "$out/falsify-$name.txt" | head -1)"
		else
			echo "run.sh: falsify: $name failed without its message:" >&2
			cat "$out/falsify-$name.txt" >&2
			result=1
		fi
	}
	# faulty CASE SED_SCRIPT FILE_GLOB: a copy of the profile files with the
	# sed script applied to the files the glob names.
	faulty() {
		dir=$out/falsify/$1
		rm -rf "$dir"
		mkdir -p "$dir"
		cp "$out"/profile-"$page"-*.txt "$dir/"
		for file in "$dir"/$3; do
			sed -i "$2" "$file"
		done
		echo "$dir"
	}
	dir=$(faulty runs 's/^\(count candidates_sum [0-9]*\)$/\11/' "profile-$page-par4-2.txt")
	expect runs 'counters differ between runs' counter_check "$dir" "$page"
	dir=$(faulty hist 's/^\(hist admitted [0-9]*\)/\19/' "profile-$page-par1-1.txt")
	expect hist 'histograms differ between runs' counter_check "$dir" "$page"
	offered=$(sed -n 's/^count candidates_sum //p' "$out/profile-$page-seq-1.txt")
	admitted=$(sed -n 's/^count admitted_sum //p' "$out/profile-$page-seq-1.txt")
	dir=$(faulty admitted "s/^count admitted_sum .*/count admitted_sum $((offered + 1))/" "profile-$page-*.txt")
	expect admitted 'counters out of order' counter_check "$dir" "$page"
	dir=$(faulty matched "s/^count matched_sum .*/count matched_sum $((admitted + 1))/" "profile-$page-*.txt")
	expect matched 'counters out of order' counter_check "$dir" "$page"
	dir=$(faulty zero 's/^count matched_sum .*/count matched_sum 0/' "profile-$page-*.txt")
	expect zero 'counters out of order' counter_check "$dir" "$page"
	# The ledger: one instance's split declined, and only one instance named.
	first=$(grep -E 'PAR split +style\.match_all(\$instance\$[0-9a-f]+)? ' "$out/ledger.txt" | grep -v declined | grep -oE 'style\.match_all(\$instance\$[0-9a-f]+)? ' | sort -u | head -1)
	grep -vF "$first" "$out/ledger.txt" >"$out/falsify-ledger-declined.txt"
	grep -F "$first" "$out/ledger.txt" | sed 's/$/  declined (falsifier)/' >>"$out/falsify-ledger-declined.txt"
	expect declined 'does not split every instance' ledger_check "$out/falsify-ledger-declined.txt"
	grep -F "$first" "$out/ledger.txt" >"$out/falsify-ledger-one.txt"
	expect one 'does not split every instance' ledger_check "$out/falsify-ledger-one.txt"
	return $result
}

profile() {
	build
	status=0
	echo "machine: $(uname -srm), $(getconf _NPROCESSORS_ONLN) processors"
	echo "compiler: $compiler $(sha256sum <"$compiler" | cut -c1-16)"
	echo "commit: $(git rev-parse --short HEAD)"
	echo "parallelism ledger ($out/ledger.txt):"
	grep -E 'PAR split +style\.' "$out/ledger.txt" || true
	ledger_check "$out/ledger.txt" || status=1
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
		counter_check "$out" "$page" || status=1
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

# Checks the drivers in DIR (its style_oracle and style_oracle_par, either may
# be missing) against the earlier build's style_oracle in BASE_DRIVERS, on
# PAGE... (LABEL names DIR in the messages). A dump checks the computed values;
# MODE all's distinct counts check the sharing, which a dump cannot see: each
# table gives a value the identifier of the first equal value, comparing by
# equality, so a wrong or misaligned hash can only make a value miss its equal
# entry and be appended again, which raises that table's count, and equal
# counts with equal dumps mean equal identifiers (DESIGN.md, "Hashing outside
# the chain (B)"). With style_oracle: MODE dump, MODE profdump and MODE all
# sequentially; with style_oracle_par: MODE profdump and MODE all at four
# workers. Prints one line per check and returns 1 when any differs.
identity_of() {
	label=$1
	dir=$2
	shift 2
	result=0
	for page in "$@"; do
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		if [ ! -s "$out/$page.compare-base.tsv" ]; then
			"$BASE_DRIVERS/style_oracle" dump 1 "$file" "$ua" $sheets >"$out/$page.compare-base.tsv"
			"$BASE_DRIVERS/style_oracle" all 1 "$file" "$ua" $sheets >"$out/$page.compare-base-all.txt"
		fi
		kinds=
		if [ -x "$dir/style_oracle" ]; then
			"$dir/style_oracle" dump 1 "$file" "$ua" $sheets >"$out/$page.$label-dump.tsv"
			"$dir/style_oracle" profdump 1 "$file" "$ua" $sheets >"$out/$page.$label-prof-seq.tsv"
			"$dir/style_oracle" all 1 "$file" "$ua" $sheets >"$out/$page.$label-all-seq.txt"
			kinds="dump prof-seq"
		fi
		if [ -x "$dir/style_oracle_par" ]; then
			WF_WORKERS=4 "$dir/style_oracle_par" profdump 1 "$file" "$ua" $sheets >"$out/$page.$label-prof-par.tsv"
			WF_WORKERS=4 "$dir/style_oracle_par" all 1 "$file" "$ua" $sheets >"$out/$page.$label-all-par.txt"
			kinds="$kinds prof-par"
		fi
		for kind in $kinds; do
			if cmp -s "$out/$page.compare-base.tsv" "$out/$page.$label-$kind.tsv"; then
				echo "$page: $label $kind identical to the earlier build's dump, $(sha256sum <"$out/$page.compare-base.tsv" | cut -c1-16)"
			else
				echo "run.sh: $page: $label $kind differs from the earlier build's dump" >&2
				result=1
			fi
		done
		for counts in "$out/$page.$label-all-seq.txt" "$out/$page.$label-all-par.txt"; do
			[ -f "$counts" ] || continue
			if cmp -s "$out/$page.compare-base-all.txt" "$counts"; then
				echo "$page: $label distinct counts $(basename "$counts" .txt | sed 's/.*-all-//') equal the earlier build's: $(cat "$counts")"
			else
				echo "run.sh: $page: $label distinct counts $(basename "$counts" .txt | sed 's/.*-all-//') differ from the earlier build's" >&2
				echo "  earlier: $(cat "$out/$page.compare-base-all.txt")" >&2
				echo "  $label: $(cat "$counts")" >&2
				result=1
			fi
		done
	done
	return $result
}

# Whether LEDGER publishes the offer of the call to NAME in intern_values: a
# permitted pair names it and no call-grain line omits it.
offer_of() {
	if grep -Eq "^PAR actualization +style\.intern_values +call grain: omitted offer of style\.$2 " "$1"; then
		echo omitted
	elif grep -Eq "^PAR permitted +\./style/intern\.wf:[0-9]+ +pair\(([a-z_]+, )?$2(, [a-z_]+)?\)" "$1"; then
		echo offered
	else
		echo "not permitted"
	fi
}

# Prints the words of the list in $2 rotated left by $1 places.
rotate() {
	echo "$2" | awk -v n="$1" '{ for (i = 0; i < NF; i++) printf "%s%s", $(((i + n) % NF) + 1), ((i < NF - 1) ? " " : "\n") }'
}

# Compares this build's interning with an earlier build's (BASE_DRIVERS, with
# the earlier --par build's ledger.txt) and with a copy of the earlier build
# (the twin), all by the same compiler; with BONLY_DRIVERS naming the
# style_oracle_par and ledger.txt of this revision built with
# intern-tables-in-order.patch, also with that build, in which the seven value
# groups' calls cannot overlap, as in the earlier build, so it has option B
# without the seven calls' offers (DESIGN.md, "Attributing the four-worker
# gain"). Every build's dumps and distinct counts must equal the earlier
# build's (identity_of); the ledger must permit every loop of the seven
# hash_*_values functions of renderer/style/intern.wf; for each of the seven
# value groups the script prints whether each build offers its call in
# intern_values, and the B-only build must offer none of them. Then, per
# page, ROUNDS_COMPARE rounds (five by default) run MODE profile once per build
# in a rotating order, sequentially (earlier, this, twin) and at four workers
# (and the B-only build), and record the stage's own intern step, the
# profiled copy's intern.whole (whose twelve table calls run one after
# another in every build) and the total, each the least over the process's
# repetitions. The summary prints each build's least and median over the
# rounds, the ratios to the earlier build, the twin's spread (|twin - base| /
# base, least times), the attribution and the falsifier's verdicts for
# ecma262 and html5. It exits with 1 when a dump or a count differs, the
# ledger does not permit a hashing loop, the B-only build offers a chained
# call or a run fails; the verdicts do not change the exit status.
compare() {
	if [ -z "${BASE_DRIVERS:-}" ]; then
		echo "run.sh: compare needs BASE_DRIVERS" >&2
		exit 2
	fi
	if [ -n "${BUILT:-}" ]; then mkdir -p "$out"; else build; fi
	twin=$out/twin
	mkdir -p "$twin"
	cp "$BASE_DRIVERS/style_oracle" "$BASE_DRIVERS/style_oracle_par" "$twin/"
	bonly=${BONLY_DRIVERS:-}
	status=0
	echo "machine: $(uname -srm), $(getconf _NPROCESSORS_ONLN) processors"
	echo "compiler: $compiler $(sha256sum <"$compiler" | cut -c1-16)"
	echo "commit: $(git rev-parse --short HEAD)"
	echo "base drivers: $(sha256sum <"$BASE_DRIVERS/style_oracle" | cut -c1-16) $(sha256sum <"$BASE_DRIVERS/style_oracle_par" | cut -c1-16)"
	echo "twin drivers: $(sha256sum <"$twin/style_oracle" | cut -c1-16) $(sha256sum <"$twin/style_oracle_par" | cut -c1-16)"
	echo "change drivers: $(sha256sum <build/style_oracle | cut -c1-16) $(sha256sum <build/style_oracle_par | cut -c1-16)"
	if [ -n "$bonly" ]; then
		echo "B-only driver: $(sha256sum <"$bonly/style_oracle_par" | cut -c1-16)"
	fi
	pages_run=${*:-ecma262 html5 apollo11}
	identity_of change build $pages_run || status=1
	if [ -n "$bonly" ]; then
		identity_of bonly "$bonly" $pages_run || status=1
	fi
	lines=$(awk '/^fn hash_[a-z]*_values\(/ { inside = 1 } /^}/ { inside = 0 } inside && /^  for \(/ { print NR }' renderer/style/intern.wf)
	found=0
	for line in $lines; do
		found=$((found + 1))
		verdict=$(grep -E "^PAR loop +\./style/intern\.wf:$line +loop " "$out/ledger.txt" || true)
		echo "${verdict:-run.sh: no ledger line for ./style/intern.wf:$line}"
		if ! echo "$verdict" | grep -Eq ' loop +permitted '; then
			echo "run.sh: the ledger does not permit the hashing loop at ./style/intern.wf:$line" >&2
			status=1
		fi
	done
	if [ "$found" != 7 ]; then
		echo "run.sh: found $found hashing loops in renderer/style/intern.wf, not 7" >&2
		status=1
	fi
	echo "call grain of intern_values, earlier build:"
	grep -E 'style\.intern_values +call grain: omitted offer of style\.' "$BASE_DRIVERS/ledger.txt" || true
	echo "call grain of intern_values, this build:"
	grep -E 'style\.intern_values +call grain: omitted offer of style\.' "$out/ledger.txt" || true
	echo "offer of each value group's call in intern_values (earlier build / this build):"
	for group in box size spacing border font text background; do
		echo "intern_${group}_group: $(offer_of "$BASE_DRIVERS/ledger.txt" "intern_${group}_group") / $(offer_of "$out/ledger.txt" "intern_${group}_group")"
	done
	if [ -n "$bonly" ]; then
		echo "B-only build, permitted pairs of intern_values's calls:"
		grep -E '^PAR permitted +\./style/intern\.wf:[0-9]+ +pair\(' "$bonly/ledger.txt" | grep -E 'pair\(((intern|chained)_[a-z]+_group|(chained_)?canon_sets), ((intern|chained)_[a-z]+_group|(chained_)?canon_sets)\)' | tee "$out/compare-bonly-pairs.txt" || true
		chained=$(grep -Ec 'pair\([^)]*(chained_[a-z]+_group|intern_box_group)' "$out/compare-bonly-pairs.txt" || true)
		pairs=$(wc -l <"$out/compare-bonly-pairs.txt" | tr -d ' ')
		if [ "$pairs" != 4 ]; then
			echo "run.sh: the B-only build permits $pairs pairs of intern_values's calls, not the 4 among canon_sets and the four other tables" >&2
			status=1
		fi
		if [ "$chained" != 0 ]; then
			echo "run.sh: the B-only build permits $chained pairs with a value group's call; it does not keep the seven calls apart" >&2
			status=1
		else
			echo "B-only build: no value group's call may overlap another call, so the seven run one after another"
		fi
	fi
	if [ "$status" != 0 ]; then
		return $status
	fi
	: >"$out/compare-times.txt"
	for page in $pages_run; do
		sheets=$(sheets_of "$page")
		file=$(page_file "$page")
		reps=$(profile_reps_of "$page")
		round=1
		while [ "$round" -le "${ROUNDS_COMPARE:-5}" ]; do
			for mode in seq par4; do
				if [ "$mode" = par4 ] && [ -n "$bonly" ]; then
					order=$(rotate "$round" "base change twin bonly")
				else
					order=$(rotate "$round" "base change twin")
				fi
				for who in $order; do
					case $who in
					base) dir=$BASE_DRIVERS ;;
					change) dir=build ;;
					twin) dir=$twin ;;
					bonly) dir=$bonly ;;
					esac
					if [ "$mode" = seq ]; then
						binary=$dir/style_oracle
						lanes=1
					else
						binary=$dir/style_oracle_par
						lanes=4
					fi
					if ! WF_WORKERS=$lanes "$binary" profile "$reps" "$file" "$ua" $sheets >"$out/compare-raw.txt"; then
						echo "run.sh: $binary profile $page failed" >&2
						return 1
					fi
					awk -v page="$page" -v mode="$mode" -v who="$who" -v round="$round" '
					$1 == "step" && $2 == "intern" { intern = $4 }
					$1 == "step" && $2 == "intern.whole" { whole = $4 }
					$1 == "step" && $2 == "total" { total = $4 }
					END { print page, mode, who, round, intern, whole, total }' "$out/compare-raw.txt" | tee -a "$out/compare-times.txt"
				done
			done
			round=$((round + 1))
		done
	done
	awk '
	{
		key = $1 SUBSEP $2 SUBSEP $3
		c = ++n[key]
		v[key, c] = $5
		w[key, c] = $6
		if (!(key in total) || $7 < total[key]) total[key] = $7
		pages[$1] = 1
	}
	function sort_values(arr, key,    a, b, t, c) {
		c = n[key]
		for (a = 1; a <= c; a++) for (b = a + 1; b <= c; b++) if (arr[key, b] < arr[key, a]) { t = arr[key, a]; arr[key, a] = arr[key, b]; arr[key, b] = t }
	}
	function rel(a, b) { return 100 * (a - b) / b }
	END {
		split("seq par4", modes, " ")
		nb = split("base change twin bonly", builds, " ")
		print "page mode build intern_least_ms intern_median_ms least_to_base median_to_base whole_least_ms whole_to_base total_least_ms intern_share"
		for (page in pages) for (j = 1; j <= 2; j++) {
			mode = modes[j]
			for (i = 1; i <= nb; i++) {
				key = page SUBSEP mode SUBSEP builds[i]
				if (!(key in n)) continue
				sort_values(v, key)
				sort_values(w, key)
				least[key] = v[key, 1]
				median[key] = v[key, int((n[key] + 1) / 2)]
				wleast[key] = w[key, 1]
			}
			base = page SUBSEP mode SUBSEP "base"
			for (i = 1; i <= nb; i++) {
				key = page SUBSEP mode SUBSEP builds[i]
				if (!(key in n)) continue
				printf "%s %s %s %.3f %.3f %.3f %.3f %.3f %.3f %.3f %.1f%%\n", page, mode, builds[i], least[key] / 1e6, median[key] / 1e6, least[key] / least[base], median[key] / median[base], wleast[key] / 1e6, wleast[key] / wleast[base], total[key] / 1e6, 100 * least[key] / total[key]
			}
		}
		print ""
		print "page mode comparison change twin_spread verdict"
		for (page in pages) for (j = 1; j <= 2; j++) {
			mode = modes[j]
			base = least[page, mode, "base"]
			spread = least[page, mode, "twin"] - base
			if (spread < 0) spread = -spread
			spread = 100 * spread / base
			judged = (page == "ecma262" || page == "html5") ? "" : " (not judged on this page)"
			if (mode == "seq") {
				change = rel(least[page, mode, "change"], base)
				printf "%s seq B-alone(change/base) %+.1f%% %.1f%% %s%s\n", page, change, spread, (change > spread) ? "slower beyond the twin spread: rejected" : "not slower beyond the twin spread", judged
				continue
			}
			change = rel(least[page, mode, "change"], base)
			printf "%s par4 A+B(change/base) %+.1f%% %.1f%% %s\n", page, change, spread, (-change > spread) ? "faster beyond the twin spread" : "not faster beyond the twin spread"
			if ((page SUBSEP mode SUBSEP "bonly") in n) {
				b = rel(least[page, mode, "bonly"], base)
				a = rel(least[page, mode, "change"], least[page, mode, "bonly"])
				printf "%s par4 B-alone(bonly/base) %+.1f%% %.1f%% %s%s\n", page, b, spread, (-b > spread) ? "faster beyond the twin spread" : "not faster beyond the twin spread: rejected", judged
				printf "%s par4 seven-offers-given-B(change/bonly) %+.1f%% %.1f%% %s\n", page, a, spread, (-a > spread) ? "faster beyond the twin spread" : "not faster beyond the twin spread"
				key = page SUBSEP mode SUBSEP "bonly"
				printf "%s par4 B-only intern share %.1f%% of total\n", page, 100 * least[key] / total[key]
			}
			wbase = wleast[page, mode, "base"]
			printf "%s par4 B-alone-profiled-copy(change/base, intern.whole) %+.1f%% (twin %+.1f%%)\n", page, rel(wleast[page, mode, "change"], wbase), rel(wleast[page, mode, "twin"], wbase)
			key = page SUBSEP mode SUBSEP "change"
			share = 100 * least[key] / total[key]
			printf "%s par4 change intern share %.1f%% of total: %s%s\n", page, share, (share <= 15) ? "within 15 percent" : "above 15 percent", judged
		}
	}' "$out/compare-times.txt" | tee "$out/compare-table.txt"
	return $status
}

# Checks DIR's drivers against BASE_DRIVERS's by identity_of (the wrong-hash
# control of the intern-compare job runs it and requires it to fail).
identity() {
	if [ -z "${BASE_DRIVERS:-}" ] || [ -z "${1:-}" ]; then
		echo "run.sh: identity needs BASE_DRIVERS and DIR" >&2
		exit 2
	fi
	mkdir -p "$out"
	dir=$1
	shift
	identity_of "$(basename "$dir")" "$dir" ${*:-ecma262 html5 apollo11}
}

case ${1:-} in
compare)
	shift
	compare "$@"
	;;
identity)
	shift
	identity "$@"
	;;
profile)
	shift
	profile "$@"
	;;
overhead)
	shift
	overhead "$@"
	;;
falsify)
	shift
	falsify "$@"
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
	echo "usage: run.sh check [PAGE...] | time [PAGE [REPS]] | profile [PAGE...] | overhead [PAGE...] | falsify [PAGE] | compare [PAGE...] | identity DIR [PAGE...]" >&2
	exit 2
	;;
esac
