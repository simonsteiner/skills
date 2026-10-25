#!/usr/bin/env bash
set -euo pipefail

# List what other tools already reported on a PR's current head: the annotations
# its check runs carry (linters, type checkers, CodeQL, Codacy, any CI step with a
# problem matcher), one JSON object per line:
#
#   outside-findings.sh <pr-number>
#   {"source":"lint","path":"src/a.ts","line":12,"end_line":12,"level":"warning","title":"no-unused-vars","message":"..."}
#
# Annotations on unchanged lines come through too; filter them against the diff.
# Tools that report only through their own service (SonarQube) don't appear here.
# Prints nothing when no check run has annotations.
# Set GH_REPO=owner/repo to target another repo, e.g. a fork with an upstream remote.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

pr="${1:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }

head="$(gh pr view "$pr" --json headRefOid --jq .headRefOid)"
runs="$(gh api "repos/{owner}/{repo}/commits/$head/check-runs?per_page=100" --paginate \
  --jq '.check_runs[] | select(.output.annotations_count > 0) | [.id, .name] | @tsv')"

# Annotations on the path ".github" are the runner's own notices (a deprecated
# action, a Node version), not findings in the code.
while IFS=$'\t' read -r id name; do
  [[ -n "$id" ]] || continue
  out="$(gh api "repos/{owner}/{repo}/check-runs/$id/annotations?per_page=100" --paginate \
    --jq '.[] | select(.path != ".github") | {path, line: .start_line, end_line, level: .annotation_level, title, message}')"
  [[ -n "$out" ]] && jq -c --arg s "$name" '{source: $s} + .' <<<"$out"
done <<<"$runs"
exit 0
