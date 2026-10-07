#!/usr/bin/env bash
set -euo pipefail

# Post one COMMENT review on a PR, pinned to its current head. The payload comes
# from stdin so it needs no temp file or shell quoting:
#
#   post-review.sh <pr-number> <<'JSON'
#   {"body": "2 findings (1 Bug, 1 Test). ...",
#    "comments": [{"path": "src/export.ts", "line": 40, "side": "RIGHT", "body": "**Bug** — ..."}]}
#   JSON
#
# Nothing is sent until the payload is valid JSON with a non-empty body and every
# comment's line sits inside a hunk of `gh pr diff`. Comments outside the diff
# are listed and the script exits 2: move them into the body and run it again.
# Prints the review URL and its state. Never leaves a PENDING review behind.

pr="${1:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }

payload="$(cat)"
[[ -n "${payload//[[:space:]]/}" ]] || { echo "error: empty payload on stdin — nothing posted" >&2; exit 1; }
jq -e '(.body | type == "string" and length > 0) and ((.comments // []) | type == "array")' \
  <<<"$payload" >/dev/null 2>&1 \
  || { echo "error: payload must be JSON with a non-empty \"body\" and an optional \"comments\" array — nothing posted" >&2; exit 1; }

# New-file line ranges of every hunk, one "path<TAB>first<TAB>last" per line.
# A "+++ " line is a path only in a file header; inside a hunk it is an added line.
hunks="$(gh pr diff "$pr" | awk '
  /^diff --git / { header = 1; next }
  header && /^\+\+\+ / { path = substr($0, 7); next }
  /^@@ / {
    header = 0
    split($3, r, ","); start = substr(r[1], 2); count = (r[2] == "" ? 1 : r[2])
    if (count > 0) printf "%s\t%d\t%d\n", path, start, start + count - 1
  }')"

outside="$(jq -r --arg hunks "$hunks" '
  ($hunks | split("\n") | map(select(length > 0) | split("\t") | {path: .[0], first: (.[1] | tonumber), last: (.[2] | tonumber)})) as $h
  | (.comments // [])[]
  | . as $c
  | (.start_line // .line) as $from
  | select(([$h[] | select(.path == $c.path and .first <= $from and $c.line <= .last)] | length) == 0)
  | "\($c.path):\($from)\(if $c.start_line then "-\($c.line)" else "" end)"
' <<<"$payload")"
if [[ -n "$outside" ]]; then
  echo "error: these comments are outside the diff — move them into the body, nothing posted:" >&2
  echo "$outside" >&2
  exit 2
fi

head="$(gh pr view "$pr" --json headRefOid --jq .headRefOid)"
body="$(jq --arg c "$head" '. + {commit_id: $c, event: "COMMENT"}' <<<"$payload")"

if ! gh api "repos/{owner}/{repo}/pulls/$pr/reviews" --input - --jq '.html_url + " " + .state' <<<"$body"; then
  # A rejected post can still leave an empty draft; drop it so it can't be submitted later.
  me="$(gh api user --jq .login)"
  gh api "repos/{owner}/{repo}/pulls/$pr/reviews" --paginate \
    --jq ".[] | select(.state == \"PENDING\" and .user.login == \"$me\") | .id" \
    | while read -r id; do gh api -X DELETE "repos/{owner}/{repo}/pulls/$pr/reviews/$id" >/dev/null; echo "deleted pending review $id" >&2; done
  exit 1
fi
