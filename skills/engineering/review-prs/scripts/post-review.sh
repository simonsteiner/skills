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

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

pr="${1:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }

payload="$(cat)"
[[ -n "${payload//[[:space:]]/}" ]] || { echo "error: empty payload on stdin — nothing posted" >&2; exit 1; }
jq -e '(.body | type == "string" and length > 0) and ((.comments // []) | type == "array")' \
  <<<"$payload" >/dev/null 2>&1 \
  || { echo "error: payload must be JSON with a non-empty \"body\" and an optional \"comments\" array — nothing posted" >&2; exit 1; }

# Line ranges of every hunk, one "<side> path first last hunk" per line, fields split
# by \037 (a path may hold a tab): LEFT for old-file lines, RIGHT for new-file lines.
# A path holding a newline breaks its record in two; jq drops the pieces, so a comment
# on such a file reads as outside the diff.
# A "+++ " line is a path only in a file header; inside a hunk it is an added line.
# Git ends a path holding a space with a tab, and C-quotes one with a tab, quote,
# backslash or non-ASCII byte ("b/\303\274.ts"); LC_ALL=C keeps \ooo a single byte.
hunks="$(gh pr diff "$pr" | LC_ALL=C awk '
  function path(s,   out, c, i) {
    sub(/\t$/, "", s)
    if (s == "/dev/null") return ""
    if (substr(s, 1, 1) == "\"") {
      s = substr(s, 2, length(s) - 2); out = ""
      for (i = 1; i <= length(s); i++) {
        c = substr(s, i, 1)
        if (c != "\\") { out = out c; continue }
        c = substr(s, ++i, 1)
        if (c ~ /[0-7]/) { out = out sprintf("%c", (c * 64) + (substr(s, i + 1, 1) * 8) + substr(s, i + 2, 1)); i += 2 }
        else out = out (c in esc ? esc[c] : c)
      }
      s = out
    }
    return substr(s, 3)
  }
  BEGIN { esc["a"] = "\a"; esc["b"] = "\b"; esc["f"] = "\f"; esc["n"] = "\n"; esc["r"] = "\r"; esc["t"] = "\t"; esc["v"] = "\v" }
  function side(name, p, range,   r, first, count) {
    split(range, r, ","); first = substr(r[1], 2); count = (r[2] == "" ? 1 : r[2])
    if (p != "" && count > 0) printf "%s\037%s\037%d\037%d\037%d\n", name, p, first, first + count - 1, hunk
  }
  /^diff --git / { header = 1; next }
  header && /^--- / { old = path(substr($0, 5)); next }
  header && /^\+\+\+ / { new = path(substr($0, 5)); next }
  # GitHub names a file by its new path on both sides: the old lines of a renamed
  # file go under the new name, and a deleted file keeps its old one.
  /^@@ / {
    header = 0; hunk++; p = (new != "" ? new : old)
    side("LEFT", old != "" ? p : "", $2); side("RIGHT", new != "" ? p : "", $3)
  }')"

# A comment fits when each end sits inside its side's lines of one hunk: `line` on
# `side` (default RIGHT), and `start_line` on `start_side` (default: `side`).
outside="$(jq -r --arg hunks "$hunks" '
  ($hunks | split("\n") | map(split("\u001f") | select(length == 5)
    | {side: .[0], path: .[1], first: (.[2] | tonumber), last: (.[3] | tonumber), hunk: .[4]})) as $h
  | def hunks($path; $side; $n): [$h[] | select(.side == $side and .path == $path and .first <= $n and $n <= .last) | .hunk];
  (.comments // [])[]
  | (.side // "RIGHT") as $side
  | (.start_line // .line) as $from
  | select([hunks(.path; .start_side // $side; $from)[] as $a | hunks(.path; $side; .line)[] | select(. == $a)] | length == 0)
  | "\(.path):\($from)\(if .start_line then "-\(.line)" else "" end)"
' <<<"$payload")"
if [[ -n "$outside" ]]; then
  echo "error: these comments are outside the diff — move them into the body, nothing posted:" >&2
  echo "$outside" >&2
  exit 2
fi

# GitHub allows one pending review per user per PR. Note the user's existing
# drafts so a failed post only ever deletes the one it created.
# The login reaches the filter as env.ME, not spliced into its text; gh's --jq takes no --arg.
export ME; ME="$(gh api user --jq .login)"
pending_ids() {
  gh api "repos/{owner}/{repo}/pulls/$pr/reviews" --paginate \
    --jq '.[] | select(.state == "PENDING" and .user.login == env.ME) | .id'
}
existing="$(pending_ids)"
if [[ -n "$existing" ]]; then
  echo "error: you already have a pending draft review on PR $pr (id $existing) — submit or discard it first, nothing posted" >&2
  exit 1
fi

head="$(gh pr view "$pr" --json headRefOid --jq .headRefOid)"
body="$(jq --arg c "$head" '. + {commit_id: $c, event: "COMMENT"}' <<<"$payload")"

if ! gh api "repos/{owner}/{repo}/pulls/$pr/reviews" --input - --jq '.html_url + " " + .state' <<<"$body"; then
  # A rejected post can still leave an empty draft; drop it so it can't be submitted later.
  # There was none before the post, so any pending review now is the one it created.
  pending_ids | while read -r id; do gh api -X DELETE "repos/{owner}/{repo}/pulls/$pr/reviews/$id" >/dev/null; echo "deleted pending review $id" >&2; done
  exit 1
fi
