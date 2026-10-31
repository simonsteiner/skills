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
# comment's line sits inside a hunk GitHub shows for the PR, read from its files
# API (so PRs too big for `gh pr diff` work). Comments outside the diff, or on a
# file GitHub shows no diff for, are listed and the script exits 2: move them
# into the body and run it again.
# Prints the review URL and its state. Never leaves a PENDING review behind.
# Set GH_REPO=[HOST/]owner/repo to target another repo, e.g. a fork with an upstream remote.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

# gh api takes its host from GH_HOST, never from GH_REPO, so carry a host-qualified GH_REPO's over.
[[ "${GH_REPO:-}" == */*/* ]] && export GH_HOST="${GH_REPO%%/*}"

pr="${1:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }

payload="$(cat)"
[[ -n "${payload//[[:space:]]/}" ]] || { echo "error: empty payload on stdin — nothing posted" >&2; exit 1; }
jq -e '(.body | type == "string" and length > 0) and ((.comments // []) | type == "array")' \
  <<<"$payload" >/dev/null 2>&1 \
  || { echo "error: payload must be JSON with a non-empty \"body\" and an optional \"comments\" array — nothing posted" >&2; exit 1; }

# The PR's files as GitHub lists them, one JSON object per line: the REST files
# endpoint, not `gh pr diff`, which GitHub refuses (HTTP 406) past 300 files or
# 20,000 lines. Its paths are raw names, so no quoting to undo. A file GitHub shows
# no diff for (too large, generated, binary, a pure rename) comes without a `patch`,
# so it has no hunks and comments on it read as outside the diff.
# The endpoint lists at most 3000 files; a file past that reads as outside too.
# The list goes to a file, never argv: a big diff overflows the argument limit.
files="$(mktemp)"
trap 'rm -f "$files"' EXIT
gh api "repos/{owner}/{repo}/pulls/$pr/files?per_page=100" --paginate \
  --jq '.[] | {filename, patch}' >"$files"
listed="$(jq -s length "$files")"

# A comment fits when each end sits inside its side's lines of one hunk: `line` on
# `side` (default RIGHT, new-file lines), and `start_line` on `start_side` (default:
# `side`); LEFT is old-file lines. GitHub names a file by its new path on both sides:
# the old lines of a renamed file go under the new name, a deleted file keeps its old one.
outside="$(jq -r --slurpfile files "$files" '
  [$files[] | .filename as $path | (.patch // "") | split("\n")
    | map(capture("^@@ -(?<l>[0-9]+)(,(?<lc>[0-9]+))? \\+(?<r>[0-9]+)(,(?<rc>[0-9]+))? @@")) | to_entries[]
    | "\($path)\u0000\(.key)" as $hunk | .value
    | ({side: "LEFT", first: (.l | tonumber), count: (.lc // "1" | tonumber)},
       {side: "RIGHT", first: (.r | tonumber), count: (.rc // "1" | tonumber)})
    | select(.count > 0) | {side, path: $path, first, last: (.first + .count - 1), hunk: $hunk}] as $h
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
  if (( listed >= 3000 )); then
    echo "note: GitHub lists only the first 3000 files of a PR; a comment on a later file can't be checked, so it reads as outside" >&2
  fi
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
