#!/usr/bin/env bash
# shellcheck disable=SC2016
# ($vars in the GraphQL strings are GraphQL variables, not shell.)
set -euo pipefail

# Reply in a review thread, and optionally resolve it. The reply body comes from
# stdin so it needs no shell quoting.
#
#   reply-resolve.sh <thread-id> [--resolve] <<'BODY'
#   Fixed in abc1234: ...
#   BODY
#
# Prints the reply URL, then "resolved" when --resolve was given.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

thread="${1:-}"
resolve="${2:-}"
[[ "$thread" == PRRT_* ]] || { echo "error: expected a review thread id (PRRT_…), got '$thread'" >&2; exit 1; }
[[ -z "$resolve" || "$resolve" == --resolve ]] || { echo "error: unknown option '$resolve'" >&2; exit 1; }

body="$(cat)"
[[ -n "${body//[[:space:]]/}" ]] || { echo "error: empty reply body on stdin — a resolve without a reply is never allowed" >&2; exit 1; }

gh api graphql -f threadId="$thread" -f body="$body" -f query='
mutation($threadId:ID!, $body:String!) {
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId, body:$body}) {
    comment { url }
  }
}' --jq '.data.addPullRequestReviewThreadReply.comment.url'

if [[ "$resolve" == --resolve ]]; then
  gh api graphql -f threadId="$thread" -f query='
mutation($threadId:ID!) {
  resolveReviewThread(input:{threadId:$threadId}) { thread { isResolved } }
}' --jq 'if .data.resolveReviewThread.thread.isResolved then "resolved" else error("thread did not resolve") end'
fi
