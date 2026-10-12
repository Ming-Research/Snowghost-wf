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
# The scan-cost experiment (DESIGN.md, "Where the scanning entry's extra time
# goes") adds, after build:
#
#   scan-param.sh build-par        builds proto_style with --par for base and
#                                  noparam (proto_style_par beside each
#                                  proto_style_seq), keeps each parallelism
#                                  ledger and diffs them
#   scan-param.sh disasm           lists the matcher chain's machine functions
#                                  in each binary with their sizes, calls and
#                                  callees, and disassembles them (objdump)
#   scan-param.sh emit             writes the compiler's emitted LLVM module
#                                  (--emit-llvm) of base and noparam, sequential
#                                  and --par, extracts the chain's functions
#                                  and diffs them; for the sequential builds
#                                  also the stack ledger (--stack-ledger) and
#                                  the module after clang -O2, whose chain is
#                                  extracted too
#   scan-param.sh callgrind [PAGE] runs shape A at REPS 1 and 0 under callgrind
#                                  (ecma262 by default): base, noparam and twin
#                                  sequential with the cache and branch
#                                  simulators, base and noparam --par at four
#                                  workers counting instructions only; prints
#                                  the stage's difference (scan-cost.py
#                                  compare) and annotates the disassembly with
#                                  each instruction's counts (scan-cost.py
#                                  annotate); callgrind_annotate's exclusive
#                                  and inclusive listings of each A 1 run
#                                  are kept beside them
#
#   scan-param.sh witness          builds witness-argument-words.wf (the
#                                  chain's shape with and without a forwarded
#                                  table) as the renderer is built, runs it,
#                                  and under callgrind prints each copy's calls
#                                  and instructions per call; keeps its
#                                  emitted IR's signatures and the copies'
#                                  disassembly
#
# Its outputs are under build/scan-param/{disasm,emit,callgrind,witness}.
#
# The patch removes the positions parameter from the ten matcher functions
# between selector_matches and the leaf tests (the eight of the chain and the
# two :nth-child scanners, which would otherwise declare a read they never make), giving each leaf (the :nth-*
# tests) and the class test a local empty slice where they read one, so the
# scanning entry runs the chain as it did before the parameter existed and
# every other entry scans too; the positioned entries then compute what they
# computed, by scanning, which is why `check` still agrees. The twin is the
# same binary as base run in its own turn: the spread between them is the
# noise the other ratio has to clear. Pages as in
# research/investigations/concurrency/run.sh (`run.sh fetch`).
#
# POSIX sh plus patch, awk and sha256sum; the scan-cost commands also need
# python3, valgrind, nm, objdump, gzip and /usr/bin/clang.

set -eu

here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../.." && pwd)
cd "$root"

data=${PAGES:-build/research/concurrency}
work=build/scan-param
ua=research/investigations/concurrency/ua.css
compiler=${WHITEFOOTC:-$root/build/whitefoot/$(sed -n "s/^release = //p" "$root/whitefoot.pin")/whitefootc}
rounds=${ROUNDS:-5}

# The matcher functions between the scanning entry and the leaf tests, the
# ones the patch changes and the table lookups it folds, as an extended
# regular expression over a symbol: `wf_` plus the name for the root module,
# the module path and `.` before it elsewhere, `wf__par_seq_` for a --par
# build's sequential clone, and a `.`-suffix for a clone LLVM made
# (`.llvm.<n>`, `.constprop.<n>`, `.specialized.<n>`).
chain_names='selector_matches|list_matches|match_complex|compound_matches|instr_matches|count_siblings|nth_scan|nth_qualifies|positioned_scan|class_records|nth_child_matches|nth_of_type_matches|of_type_edge_matches|of_child_edge_matches'
chain_ere="(^wf_(_par_seq_)?|[.])($chain_names)([.].*)?\$"
# The chain and shape A's callers of selector_matches, for the disassembly.
wanted_ere="(^wf_(_par_seq_)?|[.])($chain_names|style_element|style_level)([.].*)?\$"

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

source_of() {
	case $1 in
	base) echo "$root/renderer" ;;
	noparam) echo "$root/$work/noparam/renderer" ;;
	esac
}

build_par() {
	for name in base noparam; do
		(cd "$(source_of $name)" && "$compiler" --cache "$root/build/whitefoot-cache" --fragments function --par --par-ledger --graph modules.wfg --entry proto_style -o "$root/$work/$name/proto_style_par" >"$root/$work/$name/ledger-par.txt")
		echo "$name par: $(sha256sum <"$work/$name/proto_style_par" | cut -c1-16)"
	done
	if diff "$work/base/ledger-par.txt" "$work/noparam/ledger-par.txt" >"$work/ledger-par.diff"; then
		echo "the --par ledgers of base and noparam are equal"
	else
		status=$?
		if [ "$status" -ne 1 ]; then
			exit "$status"
		fi
		echo "the --par ledgers of base and noparam differ ($work/ledger-par.diff):"
		cat "$work/ledger-par.diff"
	fi
}

# Prints each function of objdump text $1 as one line: its symbol, its
# instruction count, its calls and tail jumps to other symbols with their
# targets, its pushes and the first constant it subtracts from %rsp (the
# frame).
summarize_disassembly() {
	awk '
	function report() {
		printf "%s instructions=%d calls=%d tail_jumps=%d pushes=%d frame=%s\n", name, count, calls, tails, pushes, frame
		for (target in callee) printf "    calls %s x%d\n", target, callee[target]
		for (target in tail) printf "    jumps to %s x%d\n", target, tail[target]
	}
	/^[0-9a-f]+ <.*>:$/ {
		if (name != "") report()
		name = $2; sub(/^</, "", name); sub(/>:$/, "", name)
		count = 0; calls = 0; tails = 0; pushes = 0; frame = "-"
		split("", callee); split("", tail)
		next
	}
	/^ +[0-9a-f]+:\t/ {
		count++
		if ($0 ~ /\tcall/ && $0 ~ /</) {
			calls++
			target = $0; sub(/.*</, "", target); sub(/>.*/, "", target)
			callee[target]++
		} else if ($0 ~ /\tcall/) {
			calls++
			callee["(indirect)"]++
		}
		if ($0 ~ /\tjmp/ && $0 ~ /</ && $0 !~ /\+0x/) {
			tails++
			target = $0; sub(/.*</, "", target); sub(/>.*/, "", target)
			tail[target]++
		}
		if ($0 ~ /\tpush/) pushes++
		if (frame == "-" && $0 ~ /\tsub +\$0x[0-9a-f]+,%rsp/) {
			frame = $0; sub(/.*\$/, "", frame); sub(/,%rsp.*/, "", frame)
		}
	}
	END { if (name != "") report() }' "$1"
}

disasm() {
	mkdir -p "$work/disasm"
	for name in base noparam; do
		for binary in proto_style_seq proto_style_par; do
			executable=$work/$name/$binary
			if [ ! -f "$executable" ]; then
				echo "scan-param.sh: $executable is missing; run build and build-par first" >&2
				exit 1
			fi
			out=$work/disasm/$name-$binary
			nm -S --defined-only "$executable" >"$out.nm"
			awk 'NF == 4 && $3 ~ /^[tTwW]$/ { print $4 } NF == 3 && $2 ~ /^[tTwW]$/ { print $3 }' "$out.nm" | sort -u >"$out.functions"
			grep -E "$wanted_ere" "$out.functions" >"$out.symbols" || :
			: >"$out.s"
			while read -r symbol; do
				objdump -d --no-show-raw-insn --disassemble="$symbol" "$executable" | sed -n '/^[0-9a-f]* <.*>:$/,$p' >>"$out.s"
			done <"$out.symbols"
			summarize_disassembly "$out.s" >"$out.summary"
			echo "== $name $binary: $(wc -l <"$out.symbols") chain functions of $(wc -l <"$out.functions")"
			cat "$out.summary"
		done
	done
}

# Prints the definitions in LLVM module $1 whose symbols match the chain.
extract_chain() {
	awk -v pattern="$chain_ere" '
	/^define / {
		symbol = $0
		sub(/^[^@]*@"?/, "", symbol)
		sub(/"?\(.*/, "", symbol)
		keep = (symbol ~ pattern)
	}
	keep { print }
	/^}/ { if (keep) print ""; keep = 0 }' "$1"
}

emit() {
	mkdir -p "$work/emit"
	for name in base noparam; do
		for mode in seq par; do
			out=$work/emit/$name-$mode
			if [ "$mode" = par ]; then
				(cd "$(source_of $name)" && "$compiler" --emit-llvm --par --graph modules.wfg --entry proto_style -o "$root/$out.ll")
			else
				started=$(date +%s)
				if (cd "$(source_of $name)" && "$compiler" --emit-llvm --stack-ledger --graph modules.wfg --entry proto_style -o "$root/$out.ll" >"$root/$out-stack.txt"); then
					echo "$name $mode: emitted with the stack ledger in $(($(date +%s) - started)) s"
					grep -E "$chain_names" "$out-stack.txt" >"$out-stack-chain.txt" || :
				else
					echo "$name $mode: the stack ledger failed (exit $?); emitting without it"
					(cd "$(source_of $name)" && "$compiler" --emit-llvm --graph modules.wfg --entry proto_style -o "$root/$out.ll")
				fi
				started=$(date +%s)
				/usr/bin/clang -x ir "$out.ll" -O2 -S -emit-llvm -Wno-override-module -o "$out-O2.ll"
				echo "$name $mode: clang -O2 in $(($(date +%s) - started)) s"
				extract_chain "$out-O2.ll" >"$out-O2-chain.ll"
			fi
			extract_chain "$out.ll" >"$out-chain.ll"
			echo "$name $mode: $(grep -c '^define' "$out-chain.ll") chain definitions emitted"
		done
	done
	for kind in seq-chain par-chain seq-O2-chain; do
		if diff -u "$work/emit/base-$kind.ll" "$work/emit/noparam-$kind.ll" >"$work/emit/$kind.diff"; then
			echo "$kind: base and noparam are equal"
		else
			status=$?
			if [ "$status" -ne 1 ]; then
				exit "$status"
			fi
			echo "$kind: base and noparam differ in $(grep -c '^[-+][^-+]' "$work/emit/$kind.diff") lines ($work/emit/$kind.diff)"
		fi
	done
	for file in "$work"/emit/*.ll; do
		case $file in
		*-chain.ll) ;;
		*) gzip -f "$file" ;;
		esac
	done
}

# Runs one build under callgrind: $1 the run's name, $2 the executable, $3
# REPS, $4 WF_WORKERS, $5 the simulators' options, then the page's arguments.
profile_run() {
	run=$1 executable=$2 reps=$3 workers=$4 options=$5
	shift 5
	started=$(date +%s)
	status=0
	# $options is unquoted on purpose: it is zero or more options.
	WF_WORKERS=$workers valgrind --tool=callgrind --dump-instr=yes --compress-strings=no --compress-pos=no $options \
		--callgrind-out-file="$work/callgrind/$run-A$reps.out" "$executable" A "$reps" "$@" \
		>"$work/callgrind/$run-A$reps.stdout" 2>"$work/callgrind/$run-A$reps.log" || status=$?
	echo "$run A $reps: exit $status in $(($(date +%s) - started)) s: $(cat "$work/callgrind/$run-A$reps.stdout")"
	if [ "$status" -ne 0 ]; then
		cat "$work/callgrind/$run-A$reps.log" >&2
		exit 1
	fi
}

callgrind() {
	page=${1:-ecma262}
	sheets=$(sheets_of "$page")
	mkdir -p "$work/callgrind"
	sims='--cache-sim=yes --branch-sim=yes'
	for reps in 0 1; do
		profile_run base-seq "$work/base/proto_style_seq" "$reps" 1 "$sims" "$data/$page.html" "$ua" $sheets
		profile_run noparam-seq "$work/noparam/proto_style_seq" "$reps" 1 "$sims" "$data/$page.html" "$ua" $sheets
		profile_run twin-seq "$work/twin/proto_style_seq" "$reps" 1 "$sims" "$data/$page.html" "$ua" $sheets
		profile_run base-par "$work/base/proto_style_par" "$reps" 4 "" "$data/$page.html" "$ua" $sheets
		profile_run noparam-par "$work/noparam/proto_style_par" "$reps" 4 "" "$data/$page.html" "$ua" $sheets
	done
	cg=$work/callgrind
	for pair in "seq base-seq noparam-seq" "twin base-seq twin-seq" "par base-par noparam-par"; do
		set -- $pair
		python3 -I "$here/scan-cost.py" compare "$cg/$2-A1.out" "$cg/$2-A0.out" "$cg/$3-A1.out" "$cg/$3-A0.out" --chain "$chain_ere" --result "$cg/$2-A1.stdout" >"$cg/compare-$1.txt"
		echo "== $3 against $2 ($cg/compare-$1.txt)"
		sed -n '1,/^== Top/p' "$cg/compare-$1.txt" | sed '$d'
		sed -n '/^== The matcher chain/,$p' "$cg/compare-$1.txt"
	done
	for run in base-seq noparam-seq base-par noparam-par; do
		callgrind_annotate --threshold=99 "$cg/$run-A1.out" >"$cg/callgrind-annotate-$run-exclusive.txt"
		callgrind_annotate --threshold=99 --inclusive=yes "$cg/$run-A1.out" >"$cg/callgrind-annotate-$run-inclusive.txt"
	done
	for name in base noparam; do
		if [ -f "$work/disasm/$name-proto_style_seq.s" ]; then
			python3 -I "$here/scan-cost.py" annotate "$cg/$name-seq-A1.out" "$work/disasm/$name-proto_style_seq.s" >"$cg/annotate-$name-seq.txt"
			echo "annotated $cg/annotate-$name-seq.txt: $(sed -n 1p "$cg/annotate-$name-seq.txt")"
		fi
	done
	gzip -f "$cg"/*.out
}

witness() {
	out=$work/witness
	mkdir -p "$out"
	"$compiler" --cache "$root/build/whitefoot-cache" --fragments function -o "$out/argument_words" "$here/witness-argument-words.wf"
	"$compiler" --emit-llvm -o "$out/argument_words.ll" "$here/witness-argument-words.wf"
	grep -E '^define .*@wf_(step|test)_with(out)?\(' "$out/argument_words.ll" >"$out/signatures.txt" || :
	cat "$out/signatures.txt"
	status=0
	"$out/argument_words" || status=$?
	echo "witness exit $status (0: both copies count the same matches)"
	if [ "$status" -ne 0 ]; then
		exit 1
	fi
	valgrind --tool=callgrind --dump-instr=yes --compress-strings=no --compress-pos=no \
		--callgrind-out-file="$out/argument_words.out" "$out/argument_words" 2>"$out/callgrind.log"
	python3 -I "$here/scan-cost.py" calls "$out/argument_words.out" '(step|test)_with(out)?([.].*)?$|^wf_main' >"$out/calls.txt"
	cat "$out/calls.txt"
	nm --defined-only "$out/argument_words" | awk '{ print $NF }' | grep -E '(step|test)_with(out)?([.].*)?$' >"$out/symbols.txt" || :
	: >"$out/argument_words.s"
	while read -r symbol; do
		objdump -d --no-show-raw-insn --disassemble="$symbol" "$out/argument_words" | sed -n '/^[0-9a-f]* <.*>:$/,$p' >>"$out/argument_words.s"
	done <"$out/symbols.txt"
	python3 -I "$here/scan-cost.py" annotate "$out/argument_words.out" "$out/argument_words.s" >"$out/annotate.txt"
	summarize_disassembly "$out/argument_words.s"
	gzip -f "$out/argument_words.out" "$out/argument_words.ll"
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
build-par) build_par ;;
witness) witness ;;
disasm) disasm ;;
emit) emit ;;
callgrind)
	shift
	callgrind "$@"
	;;
*)
	echo "usage: scan-param.sh build | check [PAGE...] | time [PAGE...] | build-par | disasm | emit | callgrind [PAGE] | witness" >&2
	exit 2
	;;
esac
