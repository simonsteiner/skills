# GitHub

The commands review-prs runs when `forge.sh` prints `github <owner>/<repo>`: `origin` is on `github.com`, or on another host `gh` accepts (GitHub Enterprise, an SSH host alias).

## Contents

- Setup
- List PRs
- Read a PR
- Outside findings
- Post the review
- Record fixes
- Fix and resolve
- Ready to merge

## Setup

`gh` must be authenticated (`gh auth status`). The bundled scripts are [scripts/post-review.sh](../scripts/post-review.sh), [scripts/outside-findings.sh](../scripts/outside-findings.sh) and [scripts/note-fixes.sh](../scripts/note-fixes.sh).

In a fork checkout with an `upstream` remote, bare `gh pr …` and `repos/{owner}/{repo}` resolve to the upstream repo, so `gh pr view <n>` fails or reads someone else's PR. If `gh repo view --json nameWithOwner` isn't the repo the PRs live on, prefix every `gh` command and script call with `GH_REPO=<owner>/<repo>` (shell variables don't survive between tool calls).

## List PRs

```bash
gh pr list --state open --limit 100 --json number,title,author,createdAt,headRefName,baseRefName,headRefOid,isDraft
gh pr list --head <branch> --state open --json number   # the open PR for one branch
# per PR: its reviews, and the review each inline thread was opened in
gh api repos/{owner}/{repo}/pulls/<n>/reviews --paginate \
  --jq '.[] | select(.state != "PENDING") | {id, state, commit_id, body, login: .user.login, bot: (.user.type == "Bot")}'
gh api repos/{owner}/{repo}/pulls/<n>/comments --paginate \
  --jq '.[] | select(.in_reply_to_id == null) | {review: .pull_request_review_id, bot: (.user.type == "Bot")}'
```

`--limit 100` is the listing cap from SKILL.md Step 1, not a page size; `gh` returns the newest first.

**Real review.** A review by a bot (`bot` above: REST `user.type` `Bot`, so CodeRabbit and Copilot whatever their login) never counts, and neither does a failure stub. Every thread reply also files an empty `COMMENTED` review of its own, so an empty-bodied comment review counts only when it opened an inline thread (its `id` is some comment's `review`); an empty approval or change request counts as it is. A human inline comment that opened a thread counts as a review too.

**Changed since the last real review** — the reviewed commit against the head. Fetch first, so both exist locally even for a fork's PR or a push since the last fetch: `git fetch --quiet origin "pull/<n>/head"`; a reviewed commit still missing after that (a force-push dropped it) → use the `compare` call below instead of `git log`. That's the head of the `Range: <base>..<head>` line in the newest review whose body has one (a review-prs summary); with none, the newest real review's `commit_id`. A summary's `Fixed:` line lists the commits that answered it: count lines only from the other commits, with `git log --format=%H <reviewed-oid>..<headRefOid>` and `git show --numstat <sha>` per commit.

```bash
gh api repos/{owner}/{repo}/compare/<reviewed-oid>...<headRefOid> --jq '[.files[] | {filename, additions, deletions}]'
```

A PR whose `baseRefName` is another open PR's `headRefName` is stacked on it.

## Read a PR

```bash
git fetch --prune origin
gh pr view <n> --json title,body,url,baseRefName,headRefName,headRefOid,closingIssuesReferences
gh pr diff <n>
git fetch --quiet origin "pull/<n>/head"   # brings a fork's head too; origin/<headRefName> has only same-repo PRs
tmp="$(mktemp -d)"; git worktree add --quiet --detach "$tmp/pr-<n>" <headRefOid> && echo "$tmp/pr-<n>"
gh pr checks <n>
```

The spec is the body and `closingIssuesReferences` (`gh issue view <m>`). Screenshots or recordings in either (`github.com/user-attachments/…`): call the Skill tool with "download-media", passing `-o <worktree path>/.scratch/media`, and check them against the diff.

## Outside findings

- **Check-run annotations** — `<skill-dir>/scripts/outside-findings.sh <n>` prints one JSON object per annotation on the PR's head (linters, type checkers, CodeQL, any CI step with a problem matcher).
- **Bot review threads** — inline comments and review bodies from bots:

  ```bash
  gh api repos/{owner}/{repo}/pulls/<n>/comments --paginate \
    --jq '.[] | select(.user.type == "Bot" and .in_reply_to_id == null) | {id, user: .user.login, path, line, side, body}'
  gh api repos/{owner}/{repo}/pulls/<n>/reviews --paginate \
    --jq '.[] | select(.user.type == "Bot") | {user: .user.login, commit_id, body}'
  gh pr view <n> --comments   # CodeRabbit's walkthrough and summary
  ```

  The REST list includes resolved threads and doesn't mark them. Tell them apart with address-review-findings' `scripts/unresolved-threads.sh <n>`: a confirmed finding in a resolved thread is posted as your own comment, since the fix step reads only unresolved threads.
- **Sonar** — the PR's key for `pullRequest` is its number.

## Post the review

GitHub rejects the **whole** review if one inline comment's line is outside the diff (HTTP 422), and a review under the user's own account can only be a plain `COMMENT`: a PR's author can't request changes on their own PR. So post through [scripts/post-review.sh](../scripts/post-review.sh), payload on stdin, run from the repo under review. It pins the review to the PR's current head as a `COMMENT`, checks every comment's `path` and `line` sits inside a hunk before sending anything (new-file numbers; `"side": "LEFT"` with old-file numbers for a deleted line; `start_line` + `line` for a range, both in one hunk), refuses while you already have a draft review on the PR, and deletes the empty draft a failed post leaves behind.

```bash
<skill-dir>/scripts/post-review.sh <n> <<'JSON'
{
  "body": "2 findings (1 Bug, 1 Test). Spec: matches #41. Tests and lint pass.",
  "comments": [
    {"path": "src/export.ts", "line": 40, "side": "RIGHT", "body": "**Bug** — `rows` is undefined when the query returns nothing, so this throws on an empty export. Default it to `[]`."}
  ]
}
JSON
```

Exit 2 lists the comments outside the diff: move them into the body and post again. Keep the URL it prints: its number after `pullrequestreview-` is the review id that *Record fixes* needs.

## Record fixes

The review id is the number after `pullrequestreview-` in `post-review.sh`'s URL:

```bash
<skill-dir>/scripts/note-fixes.sh <n> <review-id> <sha>...
```

It adds the fix commits to a `Fixed:` line after the summary's `Range:` line, merging with any earlier round.

## Fix and resolve

Once the review is posted, remove its worktree (`git worktree remove --force <path> && rmdir <its parent>`): address-review-findings makes its own.

Call the Skill tool with "address-review-findings" for each PR that got comments or has bot threads you confirmed or disputed. It reads the unresolved threads — yours and the bots' — fixes, replies to a disputed one and leaves it open, commits, pushes, replies with the commit, resolves, and carries fixes up a stack. Afterwards record the fix commits in your summary (*Record fixes*). A fix that changed what the PR describes → the "pr-body" skill for the body, `gh pr edit <n> --title` for the title.

## Ready to merge

```bash
gh pr view <n> --json mergeable,mergeStateStatus,baseRefName
gh pr checks <n>            # pending → `gh pr checks <n> --watch` in the background
```
