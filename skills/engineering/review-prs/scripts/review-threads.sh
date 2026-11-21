#!/usr/bin/env bash
# shellcheck disable=SC2016
# ($vars in the GraphQL string are GraphQL variables, not shell.)
set -euo pipefail

# List every inline review thread on a PR, resolved or not, one JSON object per line,
# with the thread's first comment:
#
#   review-threads.sh <pr-number>
#   {"id":"PRRT_…","resolved":false,"outdated":false,"path":"src/a.ts","line":12,"author":"coderabbitai","bot":true,"body":"…","url":"…"}
#
# The REST comments list can't say whether a thread is resolved; GraphQL can. bot is
# true when the thread's opener is a GitHub App or bot account (CodeRabbit, Copilot).
# line is null on an outdated or file-level thread. Pages through every thread.
# Set GH_REPO=[HOST/]owner/repo to target another repo, e.g. a fork with an upstream remote.
# Without GH_REPO, the checkout's repo and its host, GitHub Enterprise included.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

pr="${1:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }

# Twin: this repo-and-host resolution is duplicated on purpose in
# address-review-findings/scripts/unresolved-threads.sh, so each skill stays self-contained. Change both together.
#
# GH_REPO wins: `gh repo view` ignores it, and in a fork with an upstream remote names the upstream.
# gh api takes its host from GH_HOST, never from GH_REPO or the checkout, so pass the host on: a
# host-qualified GH_REPO's, else (no GH_REPO and no GH_HOST) the checkout's, or a GitHub Enterprise
# checkout would query github.com. An explicit GH_HOST is preserved.
if [[ -n "${GH_REPO:-}" ]]; then
  owner_repo="$GH_REPO"
  if [[ "$GH_REPO" == */*/* ]]; then export GH_HOST="${GH_REPO%%/*}"; fi
else
  url="$(gh repo view --json url --jq .url)"  # https://HOST/OWNER/REPO
  url="${url#*://}"
  owner_repo="${url#*/}"
  [[ -n "${GH_HOST:-}" ]] || export GH_HOST="${url%%/*}"
fi

repo="${owner_repo##*/}"
owner="${owner_repo%/*}"
owner="${owner##*/}"
[[ -n "$owner" && -n "$repo" ]] || { echo "error: could not resolve owner/repo" >&2; exit 1; }

# 100 is GitHub's maximum page size.
gh api graphql --paginate -f owner="$owner" -f repo="$repo" -F number="$pr" -f query='
query($owner:String!, $repo:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100, after:$endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line
          comments(first:1) { nodes { author { __typename login } body url } }
        }
      }
    }
  }
}' --jq '.data.repository.pullRequest.reviewThreads.nodes[]
  | (.comments.nodes[0] // {}) as $c
  | {id, resolved: .isResolved, outdated: .isOutdated, path, line,
     author: $c.author.login, bot: ($c.author.__typename == "Bot"), body: $c.body, url: $c.url}'
