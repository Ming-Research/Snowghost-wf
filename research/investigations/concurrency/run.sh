#!/bin/sh
# The harness of the concurrency investigation (DESIGN.md in this directory).
#
#   run.sh fetch                 downloads the three real pages and the style
#                                sheets they load, each checked against its
#                                pinned SHA-256
#   run.sh synth                 writes the four synthetic pages
#   run.sh check [PAGE...]       builds the style driver and runs its check
#                                (A, B and C agree, the intern pass is sound)
#   run.sh style [PAGE [REPS]]   builds the style driver and times the style
#                                stage on every page, or on PAGE
#
# Pages and sheets live in build/research/concurrency/. PAGE is one of
# ecma262, html5, apollo11, flat, deep, unbalanced and paragraph.
#
# style prints, per page, shape (A, B, C and the intern pass) and build, T(0)
# and T(REPS) as the best of RUNS runs (seven by default) and the stage time
# (T(REPS) - T(0)) / REPS in seconds: the --par build at WF_WORKERS 1, 2 and 4
# (WORKERS overrides the list) and the sequential build. REPS is chosen per
# page and stage so the stage dominates T(REPS); a second argument overrides
# it. The timed runs hold the Whitefoot check lock, taken with RUN_CHECK (by
# default the pinned checkout's .github/run-check.pl), so no other heavy job
# shares the machine.
#
# The driver is built with WHITEFOOTC (by default the pinned compiler's gate
# build, as the Makefile builds it).
#
# POSIX sh plus curl and sha256sum.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=build/research/concurrency
ua=research/investigations/concurrency/ua.css
compiler=${WHITEFOOTC:-$root/whitefoot/compiler/target/gate/whitefootc}
lock=${RUN_CHECK:-$root/whitefoot/.github/run-check.pl}
runs=${RUNS:-7}
workers=${WORKERS:-1 2 4}
real_pages='ecma262 html5 apollo11'
synthetic_pages='flat deep unbalanced paragraph'

# name  url  sha256
# ecma262: the ECMAScript specification, tc39/ecma262 gh-pages at commit
# 24620d3341aaf1a59440fde65343cda3e3f0ad4c, with the two sheets its links load.
# html5: WebKit's parser benchmark copy of the HTML specification at WebKit
# commit e9f2cf896959ec35ce49b0458b2b1bcfbd301e86; its links load nothing, and
# its first style element holds the WHATWG specification style sheet.
# apollo11: the English Wikipedia article Apollo 11 at oldid 1371120273, as
# index.php renders it with its skin, and the two ResourceLoader sheets of the
# skin that the page links. The oldid pins the article's text only: Wikimedia
# serves the page from its cache with per-request fields (the server's name,
# its response time, experiment classes on body) and each ResourceLoader sheet
# as currently deployed, with no revision to request, so the SHA-256 pins the
# copies fetched on 2026-09-28. A later fetch that Wikimedia serves
# differently fails the check; fetch keeps a file that already matches its
# pin, so copying the verified files over reproduces the pages.
pins() {
	cat <<'EOF'
ecma262.html https://raw.githubusercontent.com/tc39/ecma262/24620d3341aaf1a59440fde65343cda3e3f0ad4c/index.html e2b29c85f37b8ded51873ce385b6573a35cbc26b467c21c14f8184f3bab5aa26
ecma262-ecmarkup.css https://raw.githubusercontent.com/tc39/ecma262/24620d3341aaf1a59440fde65343cda3e3f0ad4c/assets/css/ecmarkup.css 8bef2688107197ac28abe81b62a61100904cec548e223d03a10ac7ea7b6b2fc7
ecma262-print.css https://raw.githubusercontent.com/tc39/ecma262/24620d3341aaf1a59440fde65343cda3e3f0ad4c/assets/css/print.css e80f1880ab96cb3418cddbcd7a529aa6e474113f4a87c2555d079f84fc09c53f
html5.html https://raw.githubusercontent.com/WebKit/WebKit/e9f2cf896959ec35ce49b0458b2b1bcfbd301e86/PerformanceTests/Parser/resources/html5.html f0466f5a8c8099935a9394607abcd4bbbb3b41384a14b3f906eea80a521fe06e
apollo11.html https://en.wikipedia.org/w/index.php?title=Apollo_11&oldid=1371120273 21dd01f291dfbbe9e6a16796f58939cf6081c890881855c3385b8e498a0b6a6c
apollo11-modules.css https://en.wikipedia.org/w/load.php?lang=en&modules=ext.cite.parsoid.styles%7Cext.cite.styles%7Cext.tmh.player.styles%7Cext.uls.interlanguage%7Cext.visualEditor.desktopArticleTarget.noscript%7Cext.wikimediaBadges%7Cext.wikimediaBadges.ulsV2%7Cext.wikimediamessages.styles%7Cjquery.makeCollapsible.styles%7Cmediawiki.action.styles%7Cmediawiki.codex.messagebox.styles%7Cmediawiki.interface.helpers.linker.styles%7Cmediawiki.interface.helpers.styles%7Cmediawiki.skinning.content.parsoid%7Cmediawiki.skins.legacy%7Cskins.vector.icons%2Cstyles%7Cskins.vector.search.codex.styles%7Cwikibase.client.init&only=styles&skin=vector-2022 aed8ebf3dcc139ef4ca78515ba07c449cf11ab17e4518393d3c4f29dfdde2e66
apollo11-site.css https://en.wikipedia.org/w/load.php?lang=en&modules=site.styles&only=styles&skin=vector-2022 3f439934c51c220c4b92072d4dec2219920cef1bbafb58eda32a7161df7b9d0c
EOF
}

# The style sheet files each page's links load, in document order; the
# driver adds the page's style elements after them.
sheets_of() {
	case $1 in
	ecma262) echo "$data/ecma262-ecmarkup.css $data/ecma262-print.css" ;;
	apollo11) echo "$data/apollo11-modules.css $data/apollo11-site.css" ;;
	html5 | flat | deep | unbalanced | paragraph) echo "" ;;
	*) echo "run.sh: unknown page $1" >&2; exit 2 ;;
	esac
}

# Repetitions per page and stage, chosen so the stage is at least two thirds
# of T(REPS) with the --par build at four workers, the configuration with the
# shortest stage and, because the HTML tree builder hands out statement-sized
# tasks under --par, the longest T(0): 17.5 s on ecma262 and 10 s on html5
# against 0.3 s at one worker, and up to 0.65 s on unbalanced against 0.03 s,
# measured on the development machine. One count serves the shapes A, B and
# C, and one the intern post-pass, which costs far less than a shape while
# its T(0) holds one run of C.
reps_of() {
	case $1 in
	ecma262) shapes=20 intern=800 ;;
	html5) shapes=15 intern=800 ;;
	apollo11) shapes=6 intern=2000 ;;
	flat) shapes=100 intern=1000 ;;
	deep) shapes=1000 intern=2000 ;;
	unbalanced) shapes=150 intern=1000 ;;
	paragraph) shapes=20000 intern=100000 ;;
	*) echo "run.sh: unknown page $1" >&2; exit 2 ;;
	esac
	case $2 in
	intern) echo "$intern" ;;
	*) echo "$shapes" ;;
	esac
}

verified() {
	[ -f "$1" ] && echo "$2  $1" | sha256sum -c --status
}

fetch() {
	mkdir -p "$data"
	pins | while read -r name url sum; do
		if verified "$data/$name" "$sum"; then
			echo "$name: present"
			continue
		fi
		curl -fsSL --retry 3 -o "$data/$name.part" "$url"
		if verified "$data/$name.part" "$sum"; then
			mv "$data/$name.part" "$data/$name"
			echo "$name: fetched"
		else
			mv "$data/$name.part" "$data/$name.unverified"
			echo "run.sh: $name does not match its pinned SHA-256; kept as $data/$name.unverified" >&2
			exit 1
		fi
	done
}

# Forty words, repeated by every synthetic page.
words='style and layout run in parallel only where the compiler proves the work independent from the shape of its data, so this page measures how much of each stage a renderer can spread over four cores on every real page'

repeat() {
	count=$1
	format=$2
	i=0
	while [ "$i" -lt "$count" ]; do
		printf "$format" "$words"
		i=$((i + 1))
	done
}

page_start() {
	printf '<!DOCTYPE html>\n<html lang=en>\n<head><meta charset=utf-8><title>%s</title></head>\n<body>\n' "$1"
}

page_end() {
	printf '</body>\n</html>\n'
}

synth() {
	mkdir -p "$data"
	set -- $words
	if [ "$#" -ne 40 ]; then
		echo "run.sh: the synthetic text has $# words, not 40" >&2
		exit 1
	fi
	# flat: 20,000 paragraphs of 40 words in body.
	{
		page_start flat
		repeat 20000 '<p>%s</p>\n'
		page_end
	} >"$data/flat.html"
	# deep: 200 nested divs, each with a paragraph.
	{
		page_start deep
		repeat 200 '<div><p>%s</p>\n'
		i=0
		while [ "$i" -lt 200 ]; do
			printf '</div>'
			i=$((i + 1))
		done
		printf '\n'
		page_end
	} >"$data/deep.html"
	# unbalanced: two short siblings beside a chain five levels deep that holds
	# 10,000 paragraphs.
	{
		page_start unbalanced
		repeat 2 '<p>%s</p>\n'
		printf '<div><div><div><div><div>\n'
		repeat 10000 '<p>%s</p>\n'
		printf '</div></div></div></div></div>\n'
		page_end
	} >"$data/unbalanced.html"
	# paragraph: a single paragraph of 200,000 words.
	{
		page_start paragraph
		printf '<p>\n'
		repeat 5000 '%s\n'
		printf '</p>\n'
		page_end
	} >"$data/paragraph.html"
	for page in $synthetic_pages; do
		echo "$page: $(wc -c <"$data/$page.html") bytes"
	done
}

build() {
	if [ ! -x "$compiler" ]; then
		echo "run.sh: no compiler at $compiler; set WHITEFOOTC" >&2
		exit 2
	fi
	mkdir -p build
	(cd renderer && "$compiler" --par --graph modules.wfg --entry proto_style -o ../build/proto_style)
	(cd renderer && "$compiler" --graph modules.wfg --entry proto_style -o ../build/proto_style_seq)
}

page_file() {
	file=$data/$1.html
	if [ ! -f "$file" ]; then
		echo "run.sh: $file is missing; run run.sh fetch and run.sh synth" >&2
		exit 2
	fi
	echo "$file"
}

check() {
	build
	for page in ${*:-$real_pages $synthetic_pages}; do
		file=$(page_file "$page")
		printf '%s: ' "$page"
		build/proto_style check 1 "$file" "$ua" $(sheets_of "$page")
	done
}

# Prints the elapsed seconds of one run of the driver: the sequential build
# for "seq", whose runtime still refuses a WF_WORKERS that is no count, and
# otherwise the --par build with WF_WORKERS set to the first argument. A run
# that fails stops the script.
elapsed() {
	mode=$1
	shift
	if [ "$mode" = seq ]; then
		binary=build/proto_style_seq
		lanes=1
	else
		binary=build/proto_style
		lanes=$mode
	fi
	if ! WF_WORKERS=$lanes command time -p sh -c 'exec "$@" >/dev/null 2>&1' sh "$binary" "$@" 2>"$data/time.txt"; then
		echo "run.sh: $binary $* failed" >&2
		exit 1
	fi
	awk '$1 == "real" { print $2 }' "$data/time.txt"
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

style() {
	if [ -z "${WHITEFOOT_CHECK_OWNER:-}" ]; then
		WHITEFOOT_CHECK_TIMEOUT=${WHITEFOOT_CHECK_TIMEOUT:-43200} exec perl "$lock" concurrency-style sh "$here/run.sh" style "$@"
	fi
	build
	pages=${1:-$real_pages $synthetic_pages}
	echo "machine: $(uname -srm), $(getconf _NPROCESSORS_ONLN) processors"
	echo "compiler: $compiler $(sha256sum <"$compiler" | cut -c1-16)"
	echo "page shape build reps T(0) T(REPS) stage"
	for page in $pages; do
		file=$(page_file "$page")
		sheets=$(sheets_of "$page")
		counts=$(build/proto_style C 0 "$file" "$ua" $sheets | awk '{ print $2, $3, $4, $5 }')
		echo "# $page: $counts"
		for shape in A B C intern; do
			reps=${2:-$(reps_of "$page" "$shape")}
			for mode in $workers seq; do
				zero=$(best "$mode" "$shape" 0 "$file" "$ua" $sheets)
				full=$(best "$mode" "$shape" "$reps" "$file" "$ua" $sheets)
				case $mode in
				seq) label=seq ;;
				*) label=par-$mode ;;
				esac
				echo "$page $shape $label $reps $zero $full" | awk '{ printf "%s %s %s %s %s %s %.4f\n", $1, $2, $3, $4, $5, $6, ($6 - $5) / $4 }'
			done
		done
	done
}

case ${1:-} in
fetch) fetch ;;
synth) synth ;;
check)
	shift
	check "$@"
	;;
style)
	shift
	style "$@"
	;;
*)
	echo "usage: run.sh fetch | synth | check [PAGE...] | style [PAGE [REPS]]" >&2
	exit 2
	;;
esac
