#!/bin/sh
# Print what a completion review covers: the base and head, the changed
# paths by area, the review depth and the checklist groups whose path
# triggers apply. It reads git state only; the reviewer still judges
# comments, examples and material choices.
set -eu
LC_ALL=C
export LC_ALL

main_ref=${1:-main}
git rev-parse --verify --quiet "$main_ref^{commit}" >/dev/null || {
    echo "review scope: $main_ref must name a commit" >&2
    exit 1
}
# A clone that fetches only origin/main leaves its local main behind, and a
# stale base would put already merged work in the review. Use the remote
# branch when it contains the local one.
if git rev-parse --verify --quiet "origin/$main_ref^{commit}" >/dev/null &&
    git merge-base --is-ancestor "$main_ref" "origin/$main_ref"; then
    main_ref=origin/$main_ref
fi
base=$(git merge-base "$main_ref" HEAD)
head=$(git rev-parse --short HEAD)
state=
test -z "$(git status --porcelain --untracked-files=all --ignore-submodules=none)" || state=', plus uncommitted changes'

# One "STATUS<TAB>PATH" line per change; a rename reports its new path.
{
    git diff --name-status -M "$base" | awk -F '\t' '{ print substr($1, 1, 1) "\t" $NF }'
    git ls-files --others --exclude-standard | sed 's/^/A\t/'
} | awk -F '\t' -v base="$(git rev-parse --short "$base")" -v head="$head" -v state="$state" -v ref="$main_ref" '
function area(path) {
    if (path == "whitefoot") return "pin"
    if (path ~ /^src\//) return "code"
    if (path ~ /^tests\//) return "tests"
    if (path ~ /(^|\/)Makefile$|\.mk$/ || path == ".gitmodules" || (path ~ /^\.github\// && path != ".github/pull_request_template.md")) return "gate"
    if (path ~ /^design\//) return "design"
    if (path ~ /^(AGENTS\.md|README\.md|docs\/review-checklist\.md|\.github\/pull_request_template\.md)$/ || path ~ /^(\.agents|\.claude|docs\/skills)\//) return "guidance"
    if (path ~ /^research\//) return "research"
    if (path ~ /\.md$/) return "prose"
    return "other"
}
{
    kind = area($2)
    count[kind]++
    if (count[kind] <= 3) sample[kind] = sample[kind] (count[kind] > 1 ? ", " : "") $2
    total++
    if ($1 == "A") added++
    if ($1 == "D" || $1 == "R") removed++
    if ($2 ~ /\.md$/) markdown++
    if ($2 ~ /^research\/investigations\//) decisions++
}
END {
    printf "review scope\n  base:  %s (merge base with %s)\n  head:  %s%s\n", base, ref, head, state
    if (!total) { print "  no changes against the base"; exit }
    full = count["code"] + count["tests"] + count["pin"] + count["gate"] + count["design"] + count["guidance"] + count["other"]
    printf "  depth: %s\n", full ? "full (mid-sized reviewer; every applicable group)" : "light (small reviewer; groups A, D, M and V, plus R for a material choice)"
    printf "  changed (%d path%s):\n", total, (total == 1 ? "" : "s")
    split("code tests pin gate design guidance research prose other", order, " ")
    for (i = 1; i in order; i++) {
        kind = order[i]
        if (count[kind]) printf "    %-9s %3d  %s%s\n", kind, count[kind], sample[kind], (count[kind] > 3 ? ", ..." : "")
    }
    groups = "A"
    if (added || removed) groups = groups " (" (added ? "A2: " added " added" : "") (added && removed ? "; " : "") (removed ? "A3: " removed " removed or renamed" : "") ")"
    if (markdown) groups = groups ", D"
    if (count["code"] + count["tests"]) groups = groups ", C"
    if (count["tests"] + count["gate"] + count["pin"]) groups = groups ", T"
    if (count["design"] + decisions) groups = groups ", R"
    groups = groups ", M, V"
    printf "  groups: %s\n", groups
    judged = ""
    if (!markdown && count["code"] + count["tests"]) judged = judged "D if comments or examples changed; "
    if (!(count["design"] + decisions)) judged = judged "R if the task made a material choice; "
    if (judged != "") printf "  judge:  %s\n", substr(judged, 1, length(judged) - 2)
}'
