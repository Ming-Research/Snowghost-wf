#!/bin/sh
# The harness of experiment X5 (DESIGN.md in this directory).
#
#   run.sh self-test                runs lightweight raw-output protocol
#                                   controls only; it does not run the renderer
#   run.sh prepare PAGE...          writes, under build/x5/, each page's node
#                                   listing, its dump and the edit scripts
#                                   scripts/edits.py generates from them
#   run.sh edit BUILD PAGE KIND     runs the script PAGE-KIND.edits with the
#                                   driver build/layout_oracle_BUILD (seq or
#                                   par), validates raw stdout (*.txt.raw),
#                                   and keeps comparable output lines in
#                                   build/x5/out/PAGE-KIND.BUILD.txt
#   run.sh roundtrip BUILD PAGE...  runs every kind with inverses (word,
#                                   sentence, colour, fontsize, rootfont,
#                                   block) and checks that each inverse edit
#                                   returns the base hash and each forward
#                                   edit changes it
#   run.sh same PAGE KIND...        compares the sequential and the --par
#                                   builds' output lines for the scripts
#   run.sh reparse PAGE KIND COUNT  applies the first COUNT forward text edits
#                                   of PAGE-KIND.edits to a copy of the page's
#                                   HTML source (scripts/reparse.py), dumps
#                                   each copy with the plain dump mode and
#                                   compares its hash with the edit mode's
#                                   (the seq run of `edit`)
#   run.sh dumps MAIN PAGE...       compares the dump mode with the driver
#                                   MAIN (a build of the commit before the
#                                   edit modes) byte for byte
#   run.sh inc BUILD PAGE KIND...   runs each script with `edit` (as run.sh
#                                   edit) and counts its T and D edits whose
#                                   incremental dump (text_changed and update
#                                   on a layout kept across edits) is the
#                                   same as the rebuilt one; differences,
#                                   refusals and incomplete runs fail
#   run.sh q77 [OPTIONS]            runs the fixed background-predicate oracle
#                                   through scripts/stylecheck.py q77; OPTIONS
#                                   override four binaries and a fresh output
#                                   directory (backgroundcheck.py --help);
#                                   retains complete raw evidence and fails on
#                                   any flags/work/dump/seq-par disagreement
#   run.sh time BUILD PAGE KIND [RUNS]
#                                   times text_changed + update per edit
#                                   with the driver's incremental mode, RUNS
#                                   process runs (3 by default) under the
#                                   host lock, keeps each run's lines in
#                                   build/x5/time/ and prints
#                                   scripts/inctime.py's summary; WF_WORKERS
#                                   passes through to the --par build;
#                                   RUN_CHECK names the lock script (by
#                                   default the pinned checkout's
#                                   .github/run-check.pl)
#   run.sh style-update OPTIONS... checks style edit identity and measures
#                                   three runs with baseline/candidate seq
#                                   and four-worker drivers; source revisions
#                                   and build-time provenance are required.
#                                   See DESIGN.md, Maintained style-update
#                                   measurement. --self-test is lightweight.
#   run.sh value-falsify ...        prepares/verifies Q78 diagnostic copies;
#                                   --controls runs stub checks, --execute
#                                   takes the host lock to build/run the
#                                   five falsifiers (no timing evidence)
#
# PAGE is ecma262, html5 or apollo11, fetched to build/research/concurrency by
# research/investigations/concurrency/run.sh and run with the sheets of
# research/investigations/layout/run.sh; the fonts are in build/fonts. The
# drivers are built by
#   cd renderer && whitefootc --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_seq
#   cd renderer && whitefootc --par --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_par
# under the host-wide lock (.github/run-check.pl of the pinned checkout). The
# ordinary result checks are not timed; time, style-update and value-falsify --execute
# take the lock (the latter builds diagnostic binaries).
# POSIX sh plus python3.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=${PAGES:-build/research/concurrency}
ua=${UA:-renderer/style/ua.css}
work=build/x5
kinds="word sentence colour fontsize rootfont block"

sheets_of() {
	case $1 in
	ecma262) echo "assets/css/ecmarkup.css=$data/ecma262-ecmarkup.css assets/css/print.css=$data/ecma262-print.css" ;;
	html5) echo "" ;;
	apollo11) echo "wikibase.client.init&only=styles&skin=vector-2022=$data/apollo11-modules.css modules=site.styles&only=styles&skin=vector-2022=$data/apollo11-site.css" ;;
	*)
		echo "run.sh: unknown page $1" >&2
		exit 2
		;;
	esac
}

driver() {
	echo "build/layout_oracle_$1"
}

prepare() {
	mkdir -p "$work/scripts"
	for page in "$@"; do
		# shellcheck disable=SC2046
		"$(driver seq)" nodes 0 "$data/$page.html" "$ua" $(sheets_of "$page") >"$work/$page.nodes"
		# shellcheck disable=SC2046
		"$(driver seq)" dump 1 "$data/$page.html" "$ua" $(sheets_of "$page") >"$work/$page.dump"
		python3 "$here/scripts/edits.py" "$page" "$work/$page.nodes" "$work/scripts" --dump "$work/$page.dump"
	done
}

edit() {
	build=$1 page=$2 kind=$3
	mkdir -p "$work/out"
	out=$work/out/$page-$kind.$build.txt
	raw=$out.raw
	: >"$out"
	# Save stdout before filtering; a pipeline would hide the driver's exit.
	# shellcheck disable=SC2046
	if "$(driver "$build")" edit "$work/scripts/$page-$kind.edits" "$data/$page.html" "$ua" $(sheets_of "$page") >"$raw"; then
		:
	else
		edit_status=$?
		return "$edit_status"
	fi
	python3 "$here/scripts/inctime.py" --check "$work/scripts/$page-$kind.edits" "$raw" || return "$?"
	grep -a '^base hash \|^edit [0-9]* hash \|^created ' "$raw" >"$out"
}

roundtrip() {
	build=$1
	shift
	[ "$#" -gt 0 ] || return 2
	roundtrip_status=0
	for page in "$@"; do
		for kind in $kinds; do
			printf '%s %s: ' "$page" "$kind"
			edit "$build" "$page" "$kind" || {
				echo "run failed"
				roundtrip_status=1
				continue
			}
			python3 "$here/scripts/roundtrip.py" "$work/out/$page-$kind.$build.txt" "$work/scripts/$page-$kind.edits" || {
				echo "  ^ an inverse edit did not restore the base hash"
				roundtrip_status=1
			}
		done
	done
	return "$roundtrip_status"
}

same() {
	page=$1
	shift
	[ "$#" -gt 0 ] || return 2
	same_status=0
	for kind in "$@"; do
		if ! python3 "$here/scripts/inctime.py" --check "$work/scripts/$page-$kind.edits" "$work/out/$page-$kind.seq.txt" ||
		   ! python3 "$here/scripts/inctime.py" --check "$work/scripts/$page-$kind.edits" "$work/out/$page-$kind.par.txt"; then
			same_status=1
			continue
		fi
		if cmp "$work/out/$page-$kind.seq.txt" "$work/out/$page-$kind.par.txt"; then
			echo "$page $kind: seq and par identical ($(wc -l <"$work/out/$page-$kind.seq.txt") lines)"
		else
			echo "$page $kind: seq and par DIFFER"
			same_status=1
		fi
	done
	return "$same_status"
}

reparse() {
	page=$1 kind=$2 count=$3
	mkdir -p "$work/out"
	# shellcheck disable=SC2046
	if python3 "$here/scripts/reparse.py" "$data/$page.html" "$work/$page.nodes" "$work/scripts/$page-$kind.edits" \
		"$work" "$(driver seq)" "$ua" "$count" $(sheets_of "$page") >"$work/out/$page-$kind.reparse.txt"; then
		:
	else
		reparse_status=$?
		return "$reparse_status"
	fi
	python3 "$here/scripts/inctime.py" --reparse "$work/scripts/$page-$kind.edits" \
		"$work/out/$page-$kind.seq.txt" "$work/out/$page-$kind.reparse.txt" "$count"
}

inc() {
	build=$1 page=$2
	shift 2
	[ "$#" -gt 0 ] || return 2
	inc_status=0
	for kind in "$@"; do
		edit "$build" "$page" "$kind" || {
			echo "$page $kind: run failed"
			inc_status=1
			continue
		}
		out=$work/out/$page-$kind.$build.txt
		same=$(grep -c ' inc same$' "$out" || true)
		differs=$(grep -c ' inc DIFF$' "$out" || true)
		refused=$(grep -c ' inc refused$' "$out" || true)
		edits=$(grep -c '^edit [0-9]* hash ' "$out" || true)
		echo "$page $kind ($build): $edits edits, inc same $same, DIFF $differs, refused $refused"
	done
	return "$inc_status"
}

time_edits() {
	build=$1 page=$2 kind=$3 runs=${4:-3}
	if [ -z "${WHITEFOOT_CHECK_OWNER:-}" ]; then
		exec perl "${RUN_CHECK:-$root/whitefoot/.github/run-check.pl}" x5-time sh "$here/run.sh" time "$@"
	fi
	case $runs in
	''|*[!0-9]*) echo "run.sh: RUNS must be a positive integer" >&2; return 2 ;;
	esac
	if [ "$runs" -le 0 ]; then
		echo "run.sh: RUNS must be a positive integer" >&2
		return 2
	fi
	mkdir -p "$work/time"
	files=
	i=1
	while [ "$i" -le "$runs" ]; do
		out=$work/time/$page-$kind.$build.w${WF_WORKERS:-none}.r$i.txt
		# shellcheck disable=SC2046
		if "$(driver "$build")" incremental "$work/scripts/$page-$kind.edits" "$data/$page.html" "$ua" $(sheets_of "$page") >"$out"; then
			:
		else
			time_status=$?
			return "$time_status"
		fi
		files="$files $out"
		i=$((i + 1))
	done
	echo "$page $kind $build WF_WORKERS=${WF_WORKERS:-unset}:"
	# shellcheck disable=SC2086
	python3 "$here/scripts/inctime.py" "$work/scripts/$page-$kind.edits" $files
}

dumps() {
	main=$1
	shift
	[ "$#" -gt 0 ] || return 2
	dumps_status=0
	for page in "$@"; do
		# shellcheck disable=SC2046
		if "$main" dump 1 "$data/$page.html" "$ua" $(sheets_of "$page") >"$work/$page.main.dump"; then
			:
		else
			dumps_status=1
			continue
		fi
		if cmp "$work/$page.main.dump" "$work/$page.dump"; then
			echo "$page: dump identical to the main driver's ($(wc -c <"$work/$page.dump") bytes)"
		else
			echo "$page: dump DIFFERS"
			dumps_status=1
		fi
	done
	return "$dumps_status"
}

style_update() {
	for option in "$@"; do
		if [ "$option" = --self-test ] || [ "$option" = --help ]; then
			python3 "$here/scripts/styleupdate.py" "$@"
			return "$?"
		fi
	done
	if [ -z "${WHITEFOOT_CHECK_OWNER:-}" ]; then
		exec perl "${RUN_CHECK:-$root/whitefoot/.github/run-check.pl}" x5-style-update sh "$here/run.sh" style-update "$@"
	fi
	python3 "$here/scripts/styleupdate.py" "$@"
}

value_falsify() {
	for argument in "$@"; do
		if [ "$argument" = --execute ] && [ -z "${WHITEFOOT_CHECK_OWNER:-}" ]; then
			exec perl "${RUN_CHECK:-$root/whitefoot/.github/run-check.pl}" x5-value-falsify sh "$here/run.sh" value-falsify "$@"
		fi
	done
	python3 "$here/scripts/value_probe.py" "$@"
}

cmd=$1
shift
case $cmd in
self-test) python3 "$here/scripts/inctime.py" --self-test ;;
prepare) prepare "$@" ;;
edit) edit "$@" ;;
roundtrip) roundtrip "$@" ;;
same) same "$@" ;;
reparse) reparse "$@" ;;
dumps) dumps "$@" ;;
inc) inc "$@" ;;
time) time_edits "$@" ;;
q77) python3 "$here/scripts/stylecheck.py" q77 "$@" ;;
style-update) style_update "$@" ;;
value-falsify) value_falsify "$@" ;;
*)
	echo "usage: run.sh self-test|prepare|edit|roundtrip|same|reparse|dumps|inc|time|q77|style-update|value-falsify ..." >&2
	exit 2
	;;
esac
