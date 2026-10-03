#!/usr/bin/env bash
# shellcheck disable=SC2016
# ($vars in the GraphQL strings are GraphQL variables, not shell.)
set -euo pipefail

# Print every unresolved review thread on a PR as one JSON object per line.
# Pages through all threads, so a PR with more than one page of threads loses none.
#
#   unresolved-threads.sh [pr-number]   default: the PR for the current branch
#
# stderr warns when the PR has no reviews at all. A thread whose commentCount
# exceeds its comments array has more than one page of comments — open its url.

pr="${1:-$(gh pr view --json number --jq .number)}"
owner="$(gh repo view --json owner --jq .owner.login)"
repo="$(gh repo view --json name --jq .name)"
[[ -n "$pr" && -n "$owner" && -n "$repo" ]] || { echo "error: could not resolve owner/repo/PR (pr='$pr')" >&2; exit 1; }

reviews="$(gh pr view "$pr" --json reviews --jq '.reviews | length')"
if [[ "$reviews" == 0 ]]; then
  echo "warning: PR #$pr has no reviews at all — not a clean review, nobody looked" >&2
fi

# 100 is GitHub's maximum page size for both connections.
gh api graphql --paginate -f owner="$owner" -f repo="$repo" -F number="$pr" -f query='
query($owner:String!, $repo:String!, $number:Int!, $endCursor:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      reviewThreads(first:100, after:$endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line startLine
          comments(first:100) {
            totalCount
            nodes { databaseId author { login } body url originalLine diffHunk }
          }
        }
      }
    }
  }
}' --jq '.data.repository.pullRequest.reviewThreads.nodes[]
  | select(.isResolved | not)
  | {id, isOutdated, path, line, startLine, commentCount: .comments.totalCount, comments: .comments.nodes}'
