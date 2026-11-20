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
# line is null on an outdated thread. Pages through every thread.
# Set GH_REPO=[HOST/]owner/repo to target another repo, e.g. a fork with an upstream remote.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

# gh api takes its host from GH_HOST, never from GH_REPO, so carry a host-qualified GH_REPO's over.
[[ "${GH_REPO:-}" == */*/* ]] && export GH_HOST="${GH_REPO%%/*}"

pr="${1:-}"
[[ "$pr" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number, got '$pr'" >&2; exit 1; }

# GH_REPO wins: `gh repo view` ignores it, and in a fork with an upstream remote names the upstream.
owner_repo="${GH_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
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
