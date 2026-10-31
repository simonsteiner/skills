#!/usr/bin/env bash
set -euo pipefail

# Record the commits that fixed a review's findings in that review's own summary, so
# the PR shows what was reviewed and what was fixed, and the next run can tell fix
# commits from new work:
#
#   note-fixes.sh <pr-number> <review-id> <sha>...
#
# The review must be a review-prs summary (its body has a "Range: " line). The script
# adds or extends one "Fixed: <sha> <sha> …" line after it; a second fix round adds its
# commits to the same line. Short or full hex SHAs; duplicates are dropped.
# The review id is the number after "pullrequestreview-" in post-review.sh's URL.
# Prints the review URL.
# Set GH_REPO=owner/repo to target another repo, e.g. a fork with an upstream remote.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

pr="${1:-}" review="${2:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }
[[ "$review" =~ ^[0-9]+$ ]] || { echo "error: expected a review id, got '$review'" >&2; exit 1; }
shift 2
(( $# > 0 )) || { echo "error: no commits given — nothing to record" >&2; exit 1; }
for sha in "$@"; do
  [[ "$sha" =~ ^[0-9a-f]{7,40}$ ]] || { echo "error: not a commit SHA: '$sha'" >&2; exit 1; }
done

url="repos/{owner}/{repo}/pulls/$pr/reviews/$review"
body="$(gh api "$url" --jq .body)"
grep -q '^Range: ' <<<"$body" \
  || { echo "error: review $review has no \"Range: \" line — not a review-prs summary, nothing changed" >&2; exit 1; }

# The new body: drop any old "Fixed:" line, then put the merged list right after "Range:".
new="$(jq -rn --arg body "$body" --args '
  ($body | split("\n")) as $lines
  | ([$lines[] | select(startswith("Fixed: ")) | ltrimstr("Fixed: ") | split(" ")[] | select(. != "")] + $ARGS.positional) as $all
  | (reduce $all[] as $s ([]; if index([$s]) then . else . + [$s] end)) as $shas
  | [$lines[] | select(startswith("Fixed: ") | not)
     | if startswith("Range: ") then ., "Fixed: \($shas | join(" "))" else . end]
  | join("\n")' "$@")"

jq -n --arg b "$new" '{body: $b}' | gh api -X PUT "$url" --input - --jq .html_url
