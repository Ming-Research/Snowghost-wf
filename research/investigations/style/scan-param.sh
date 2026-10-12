#!/bin/sh
# The scan-parameter experiment of the style step-timing investigation
# (DESIGN.md in this directory): does the sibling positions slice that
# pkg::css::selectors passes down its matching chain make the scanning entry,
# selector_matches, slower?
#
#   scan-param.sh build            builds the sequential proto_style driver
#                                  three times in build/scan-param: base (this
#                                  checkout), noparam (this checkout with
#                                  scan-without-positions.patch applied) and
#                                  twin (a copy of base's binary)
#   scan-param.sh check [PAGE...]  runs `proto_style check 1` with each build
#                                  and requires the same output, which carries
#                                  the checksum the shapes agree on
#   scan-param.sh time [PAGE...]   times shape A, which calls selector_matches
#                                  for every rule and element, with each build
#                                  in turn, ROUNDS rounds (five by default),
#                                  and prints the stage time (T(1) - T(0)) per
#                                  build, then the least and median of each
#                                  build's rounds and the ratios to base
#
# The patch removes the positions parameter from the eight matcher functions
# between selector_matches and the leaf tests, giving each leaf (the :nth-*
# tests) and the class test a local empty slice where they read one, so the
# scanning entry runs the chain as it did before the parameter existed and
# every other entry scans too; the positioned entries then compute what they
# computed, by scanning, which is why `check` still agrees. The twin is the
# same binary as base run in its own turn: the spread between them is the
# noise the other ratio has to clear. Pages as in
# research/investigations/concurrency/run.sh (`run.sh fetch`).
#
# POSIX sh plus patch, awk and sha256sum.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=${PAGES:-build/research/concurrency}
work=build/scan-param
ua=research/investigations/concurrency/ua.css
compiler=${WHITEFOOTC:-$root/build/whitefoot/$(sed -n "s/^release = //p" "$root/whitefoot.pin")/whitefootc}
rounds=${ROUNDS:-5}

sheets_of() {
	case $1 in
	ecma262) echo "$data/ecma262-ecmarkup.css $data/ecma262-print.css" ;;
	apollo11) echo "$data/apollo11-modules.css $data/apollo11-site.css" ;;
	html5) echo "" ;;
	*)
		echo "scan-param.sh: unknown page $1" >&2
		exit 2
		;;
	esac
}

build() {
	rm -rf "$work"
	mkdir -p "$work/base" "$work/noparam"
	(cd renderer && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --graph modules.wfg --entry proto_style -o "$root/$work/base/proto_style_seq")
	cp -R renderer "$work/noparam/renderer"
	patch -p1 -d "$work/noparam" <"$here/scan-without-positions.patch"
	(cd "$work/noparam/renderer" && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --graph modules.wfg --entry proto_style -o "$root/$work/noparam/proto_style_seq")
	cp "$work/base/proto_style_seq" "$work/twin_proto_style_seq"
	mkdir -p "$work/twin"
	mv "$work/twin_proto_style_seq" "$work/twin/proto_style_seq"
	for name in base noparam twin; do
		echo "$name: $(sha256sum <"$work/$name/proto_style_seq" | cut -c1-16)"
	done
}

check() {
	status=0
	for page in ${*:-ecma262 apollo11}; do
		sheets=$(sheets_of "$page")
		for name in base noparam twin; do
			"$work/$name/proto_style_seq" check 1 "$data/$page.html" "$ua" $sheets >"$work/check-$page-$name.txt"
		done
		if cmp -s "$work/check-$page-base.txt" "$work/check-$page-noparam.txt" && cmp -s "$work/check-$page-base.txt" "$work/check-$page-twin.txt"; then
			echo "$page: $(cat "$work/check-$page-base.txt")"
		else
			echo "scan-param.sh: $page: the builds print different checks" >&2
			status=1
		fi
	done
	return $status
}

elapsed() {
	if ! WF_WORKERS=1 command time -p sh -c 'exec "$@" >/dev/null 2>&1' sh "$@" 2>"$work/time.txt"; then
		echo "scan-param.sh: $* failed" >&2
		exit 1
	fi
	awk '$1 == "real" { print $2 }' "$work/time.txt"
}

timing() {
	: >"$work/times.txt"
	for page in ${*:-ecma262 apollo11}; do
		sheets=$(sheets_of "$page")
		round=1
		while [ "$round" -le "$rounds" ]; do
			case $((round % 3)) in
			0) order="base noparam twin" ;;
			1) order="noparam twin base" ;;
			2) order="twin base noparam" ;;
			esac
			for name in $order; do
				zero=$(elapsed "$work/$name/proto_style_seq" A 0 "$data/$page.html" "$ua" $sheets)
				full=$(elapsed "$work/$name/proto_style_seq" A 1 "$data/$page.html" "$ua" $sheets)
				echo "$page $name $round $zero $full" | awk '{ printf "%s %s %s %s %s %.3f\n", $1, $2, $3, $4, $5, $5 - $4 }' | tee -a "$work/times.txt"
			done
			round=$((round + 1))
		done
	done
	echo "page build least_s median_s ratio_least_to_base ratio_median_to_base"
	awk '
	{ page = $1; name = $2; n[page, name]++; v[page, name, n[page, name]] = $6; pages[page] = 1 }
	END {
		for (page in pages) {
			split("base noparam twin", list, " ")
			for (i = 1; i <= 3; i++) {
				name = list[i]
				c = n[page, name]
				for (a = 1; a <= c; a++) for (b = a + 1; b <= c; b++) if (v[page, name, b] < v[page, name, a]) { t = v[page, name, a]; v[page, name, a] = v[page, name, b]; v[page, name, b] = t }
				least[page, name] = v[page, name, 1]
				median[page, name] = v[page, name, int((c + 1) / 2)]
			}
			for (i = 1; i <= 3; i++) {
				name = list[i]
				printf "%s %s %.3f %.3f %.3f %.3f\n", page, name, least[page, name], median[page, name], least[page, name] / least[page, "base"], median[page, name] / median[page, "base"]
			}
		}
	}' "$work/times.txt"
}

case ${1:-} in
build) build ;;
check)
	shift
	check "$@"
	;;
time)
	shift
	timing "$@"
	;;
*)
	echo "usage: scan-param.sh build | check [PAGE...] | time [PAGE...]" >&2
	exit 2
	;;
esac
