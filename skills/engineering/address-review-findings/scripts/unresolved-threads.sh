#!/usr/bin/env bash
# shellcheck disable=SC2016
# ($vars in the GraphQL strings are GraphQL variables, not shell.)
set -euo pipefail

# Print every unresolved review thread on a PR as one JSON object per line.
# Pages through all threads, so a PR with more than one page of threads loses none.
#
#   unresolved-threads.sh [pr-number]   default: the PR for the current branch
#
# stderr warns when the PR has no real review: no reviews, or only ones that report
# their own failure ("Copilot encountered an error…", rate-limit notices).
# awaitingReviewer is true when you (the authenticated user) already replied last in a
# thread someone else started — reply again only if the reviewer has said more since.
# A thread whose commentCount exceeds its comments array has more than one page of
# comments — open its url.

pr="${1:-$(gh pr view --json number --jq .number)}"
owner_repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
owner="${owner_repo%%/*}"
repo="${owner_repo##*/}"
export ME; ME="$(gh api user --jq .login)"; me="$ME"
[[ -n "$pr" && -n "$owner" && -n "$repo" && -n "$me" ]] || { echo "error: could not resolve owner/repo/PR/user (pr='$pr')" >&2; exit 1; }

# A failed automated review still shows up in `reviews`; it isn't one. Empty-bodied
# reviews are real — they just carry inline comments. Only a short body can be a failure
# stub; a long review that mentions "rate limit" is a real one.
real="$(gh pr view "$pr" --json reviews --jq '[.reviews[]
  | select(.state != "PENDING")
  | select((.body | length) > 300 or (.body | test("unable to review|encountered an error|rate.?limit"; "i") | not))] | length')"
if [[ "$real" == 0 ]]; then
  echo "warning: PR #$pr has no real review — none, or only failed ones; not a clean review, nobody looked" >&2
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
  | {id, isOutdated, path, line, startLine, commentCount: .comments.totalCount,
     awaitingReviewer: ((.comments.nodes | last | .author.login) == env.ME
       and any(.comments.nodes[]; .author.login != env.ME)),
     comments: .comments.nodes}'
