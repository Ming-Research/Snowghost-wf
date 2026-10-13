#!/bin/sh
set -eu
driver=$1
output=$2
fixture=research/investigations/incremental-layout/scripts/checkpoint-case.html
"$driver" nodes 0 "$fixture" renderer/style/ua.css > "$output.nodes"
parent=$(awk '$1 == "E" && $4 == "section" { print $2 }' "$output.nodes")
created=$(awk '$1 == "N" { print $2 }' "$output.nodes")
test -n "$parent"
test -n "$created"
printf 'B %s - Neutral context after the counter setter.\nB %s - Counter reader in the new context.\n' "$parent" "$created" > "$output"
