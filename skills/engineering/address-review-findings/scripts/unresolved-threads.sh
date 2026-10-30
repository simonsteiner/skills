#!/usr/bin/env bash
# shellcheck disable=SC2016
# ($vars in the GraphQL strings are GraphQL variables, not shell.)
set -euo pipefail

# Print every unresolved review thread on a PR as one JSON object per line.
# Pages through all threads, so a PR with more than one page of threads loses none.
#
#   unresolved-threads.sh [pr-number]   default: the PR for the current branch
#
# Set GH_REPO=owner/repo to target another repo, e.g. a fork whose checkout has an
# upstream remote and no `gh repo set-default`.
#
# stderr warns when the PR has no real review: no reviews, only ones that report their
# own failure ("Copilot encountered an error…", rate-limit notices), only bots'
# (CodeRabbit, Copilot) — their threads are still listed — or only thread replies.
# awaitingReviewer is true when you (the authenticated user) already replied last in a
# thread someone else started — reply again only if the reviewer has said more since.
# A thread whose commentCount exceeds its comments array has more than one page of
# comments — open its url.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

pr="${1:-$(gh pr view --json number --jq .number)}"
# GH_REPO ([HOST/]OWNER/REPO) wins: `gh pr` honours it but `gh repo view` doesn't, and in
# a fork with an upstream remote the latter names the upstream.
owner_repo="${GH_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
repo="${owner_repo##*/}"
owner="${owner_repo%/*}"
owner="${owner##*/}"
export ME; ME="$(gh api user --jq .login)"
[[ -n "$pr" && -n "$owner" && -n "$repo" && -n "$ME" ]] || { echo "error: could not resolve owner/repo/PR/user (pr='$pr')" >&2; exit 1; }

# What counts as a real review. A failed automated review still shows up in `reviews`;
# it isn't one: only a short body can be a failure stub, so a long review that mentions
# "rate limit" is real. A bot's review (REST `user.type` "Bot": CodeRabbit, Copilot) is
# input, not a review. And every thread reply files an empty COMMENTED review of its own,
# so an empty-bodied comment review is real only when it carries an inline comment that
# isn't a reply; an empty approval or change request is real as it is.
reviews="$(gh api "repos/$owner/$repo/pulls/$pr/reviews?per_page=100" --paginate \
  --jq '.[] | select(.state != "PENDING") | {id, state, body: (.body // ""), login: .user.login, bot: (.user.type == "Bot")}')"
opened="$(gh api "repos/$owner/$repo/pulls/$pr/comments?per_page=100" --paginate \
  --jq '.[] | select(.in_reply_to_id == null) | .pull_request_review_id')"
real="$(jq -s --argjson opened "[${opened//$'\n'/,}]" '[.[]
  | select((.body | length) > 300 or (.body | test("unable to review|encountered an error|rate.?limit"; "i") | not))
  | select(.body != "" or .state == "APPROVED" or .state == "CHANGES_REQUESTED" or (.id as $id | any($opened[]; . == $id)))]' <<<"$reviews")"
human="$(jq '[.[] | select(.bot | not)] | length' <<<"$real")"
bots="$(jq -r '[.[] | select(.bot) | .login] | unique | join(", ")' <<<"$real")"
if [[ "$human" == 0 && -n "$bots" ]]; then
  echo "warning: PR #$pr has no real review — only bot reviews ($bots); their threads are listed, but no person or review-prs run has reviewed it" >&2
elif [[ "$human" == 0 ]]; then
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
