#!/bin/sh
# The harness of experiment X5 (DESIGN.md in this directory).
#
#   run.sh prepare PAGE...          writes, under build/x5/, each page's node
#                                   listing, its dump and the edit scripts
#                                   scripts/edits.py generates from them
#   run.sh edit BUILD PAGE KIND     runs the script PAGE-KIND.edits with the
#                                   driver build/layout_oracle_BUILD (seq or
#                                   par) and keeps its output lines in
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
#                                   same as the rebuilt one, differs, or was
#                                   refused
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
#
# PAGE is ecma262, html5 or apollo11, fetched to build/research/concurrency by
# research/investigations/concurrency/run.sh and run with the sheets of
# research/investigations/layout/run.sh; the fonts are in build/fonts. The
# drivers are built by
#   cd renderer && whitefootc --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_seq
#   cd renderer && whitefootc --par --graph modules.wfg --entry layout_oracle -o ../build/layout_oracle_par
# under the host-wide lock (.github/run-check.pl of the pinned checkout). The
# other runs here check results and are not timed, so only time takes the
# lock.
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
	status=0
	# The driver's output holds the hash lines and any requested dumps; keep
	# only the lines this harness compares.
	# shellcheck disable=SC2046
	"$(driver "$build")" edit "$work/scripts/$page-$kind.edits" "$data/$page.html" "$ua" $(sheets_of "$page") |
		grep -a '^base hash \|^edit [0-9]* hash \|^created ' >"$out" || status=$?
	return "$status"
}

roundtrip() {
	build=$1
	shift
	for page in "$@"; do
		for kind in $kinds; do
			printf '%s %s: ' "$page" "$kind"
			edit "$build" "$page" "$kind" || {
				echo "run failed"
				continue
			}
			python3 "$here/scripts/roundtrip.py" "$work/out/$page-$kind.$build.txt" "$work/scripts/$page-$kind.edits" || echo "  ^ an inverse edit did not restore the base hash"
		done
	done
}

same() {
	page=$1
	shift
	for kind in "$@"; do
		if cmp "$work/out/$page-$kind.seq.txt" "$work/out/$page-$kind.par.txt"; then
			echo "$page $kind: seq and par identical ($(wc -l <"$work/out/$page-$kind.seq.txt") lines)"
		else
			echo "$page $kind: seq and par DIFFER"
		fi
	done
}

reparse() {
	page=$1 kind=$2 count=$3
	# shellcheck disable=SC2046
	python3 "$here/scripts/reparse.py" "$data/$page.html" "$work/$page.nodes" "$work/scripts/$page-$kind.edits" \
		"$work" "$(driver seq)" "$ua" "$count" $(sheets_of "$page") >"$work/out/$page-$kind.reparse.txt"
	while read -r _ number _ hash _ size; do
		edit=$(grep -a "^edit $number hash " "$work/out/$page-$kind.seq.txt" | cut -d' ' -f4,6)
		if [ "$edit" = "$hash $size" ]; then
			echo "$page $kind edit $number: edit mode and re-parse agree (hash $hash, $size bytes)"
		else
			echo "$page $kind edit $number: DIFFER, edit mode '$edit', re-parse '$hash $size'"
		fi
	done <"$work/out/$page-$kind.reparse.txt"
}

inc() {
	build=$1 page=$2
	shift 2
	for kind in "$@"; do
		edit "$build" "$page" "$kind" || {
			echo "$page $kind: run failed"
			continue
		}
		out=$work/out/$page-$kind.$build.txt
		same=$(grep -c ' inc same$' "$out" || true)
		differs=$(grep -c ' inc DIFF$' "$out" || true)
		refused=$(grep -c ' inc refused$' "$out" || true)
		edits=$(grep -c '^edit [0-9]* hash ' "$out" || true)
		echo "$page $kind ($build): $edits edits, inc same $same, DIFF $differs, refused $refused"
	done
}

time_edits() {
	build=$1 page=$2 kind=$3 runs=${4:-3}
	if [ -z "${WHITEFOOT_CHECK_OWNER:-}" ]; then
		exec perl "${RUN_CHECK:-$root/whitefoot/.github/run-check.pl}" x5-time sh "$here/run.sh" time "$@"
	fi
	mkdir -p "$work/time"
	files=
	i=1
	while [ "$i" -le "$runs" ]; do
		out=$work/time/$page-$kind.$build.w${WF_WORKERS:-none}.r$i.txt
		# shellcheck disable=SC2046
		"$(driver "$build")" incremental "$work/scripts/$page-$kind.edits" "$data/$page.html" "$ua" $(sheets_of "$page") >"$out"
		files="$files $out"
		i=$((i + 1))
	done
	echo "$page $kind $build WF_WORKERS=${WF_WORKERS:-unset}:"
	# shellcheck disable=SC2086
	python3 "$here/scripts/inctime.py" $files
}

dumps() {
	main=$1
	shift
	for page in "$@"; do
		# shellcheck disable=SC2046
		"$main" dump 1 "$data/$page.html" "$ua" $(sheets_of "$page") >"$work/$page.main.dump"
		if cmp "$work/$page.main.dump" "$work/$page.dump"; then
			echo "$page: dump identical to the main driver's ($(wc -c <"$work/$page.dump") bytes)"
		else
			echo "$page: dump DIFFERS"
		fi
	done
}

cmd=$1
shift
case $cmd in
prepare) prepare "$@" ;;
edit) edit "$@" ;;
roundtrip) roundtrip "$@" ;;
same) same "$@" ;;
reparse) reparse "$@" ;;
dumps) dumps "$@" ;;
inc) inc "$@" ;;
time) time_edits "$@" ;;
*)
	echo "usage: run.sh prepare|edit|roundtrip|same|reparse|dumps|inc|time ..." >&2
	exit 2
	;;
esac
