---
name: review-prs
compatibility: Requires git, jq, and an authenticated gh CLI.
description: >
  Reviews GitHub pull requests that have no real review yet or changed a lot since the last one — one PR, several, or a stack — posts the findings as inline comments, then fixes them and resolves the threads. Also reviews a local diff since a fixed point (commit, branch, tag) against the repo's standards and the originating spec. Use when the user wants open PRs or a branch code-reviewed, says nothing has reviewed their PRs, asks to "review since" a ref, or wants findings commented and fixed in one pass. Does not work through a reviewer's existing comments (address-review-findings) or scan for architecture candidates (arch-review).
---

# Review PRs

Review what nobody has looked at, leave the findings where the author will see them, then fix what's real. Two modes share one review:

- **PR mode** (default) — GitHub PRs: find, review, comment, fix, resolve.
- **Local mode** — a fixed point is given ("review since `main`", or another skill passes one) and no PR is involved: review `git diff <fixed-point>...HEAD`, fix directly, skip Steps 1 and 3.

**Run hands-off** and report at the end. What keeps that safe: comments only go on lines the diff touches, only findings verified against the code are posted, and a thread resolves only when a fix landed for it. `gh` must be authenticated (`gh auth status`).

## Gotchas

- A review that only reports its own failure ("Copilot encountered an error and was unable to review…", a rate-limit notice) is **not a review**. An empty approval isn't failed, so it counts as one. Most PRs in a flaky-bot repo carry one.
- GitHub rejects the **whole** review if one inline comment's line is outside the diff (HTTP 422). Validate lines before posting.
- The review posts under the user's account, so it can only be a plain `COMMENT`; a PR's author can't request changes on their own PR.
- A stack layer's diff is against its **base branch**, not the default branch — otherwise every layer repeats the ones below it.
- The main checkout may be switched by another session mid-run, so never switch it: read a PR from `gh pr diff`, `git show origin/<head>:<path>`, or a worktree you created (Step 2).
- Shell variables don't survive between tool calls. Write a path `mktemp` printed into every later command literally, never `$wt`: an empty `$wt` makes `cd "$wt"` a silent no-op in the main checkout.
- Delete only exact paths you created (a worktree and the `mktemp -d` folder around it, `mktemp` scratch files). Never by pattern — not `/tmp/tmp.*`, not a loop over `git worktree list` matching a prefix: parallel reviewers and other sessions keep theirs there.
- A fresh worktree has no gitignored inputs (`.env`, `node_modules`, data) and a running dev server serves the main checkout. Install or copy what a check needs, never symlink it in, or name the check as not run. Never `git stash` to compare before and after: the stash is shared by every worktree.
- Don't pipe `git` or `gh` into `| tail` or `| head`. It hides the exit status; a failed fetch or worktree add looks like success.
- When a PR under review changes this skill, the installed skill may be a link into that repo, so its text and scripts change as fixes land mid-run. Read this skill's files at the start and run its scripts from a copy, using the path it prints: `d="$(mktemp -d)" && cp -r <skill-dir>/scripts "$d" && echo "$d/scripts"`. address-review-findings, which Step 4 hands off to, copies its own scripts the same way.
- A command a guard or sandbox refuses stays refused. Don't re-run it through a script file or another wrapper; split it as the error asks, or skip it and say so in the report.

---

## Step 1 — Find what needs a review (PR mode)

```bash
gh pr list --state open --limit 100 --json number,title,author,headRefName,baseRefName,headRefOid,isDraft,reviews
gh api repos/{owner}/{repo}/pulls/<n>/comments --paginate --jq 'length'   # per PR: inline comments
```

A PR **needs a review** when either holds:

- **No real review** — `reviews` has no real one (see Gotchas) and there are no inline comments.
- **Enough changed since the last real one** — compare the newest real review's `commit.oid` to the head: `gh api repos/{owner}/{repo}/compare/<reviewed-oid>...<headRefOid> --jq '[.files[] | {filename, additions, deletions}]'`. About 30+ changed lines of code (not docs, lockfiles, formatting), or a new file, counts. Typo fixes and no-op rebases don't.

The set is one PR or many. A PR whose `baseRefName` is another open PR's `headRefName` is **stacked** on it: order each stack base first. Independent PRs have no order. PRs named (`#12 #15`) or "the stack" override the filter. Skip drafts unless asked. Nothing needs a review → say so and stop.

## Step 2 — Review each PR

Per PR (stacks bottom-up, independent PRs one at a time), read its diff against its base, and check out its head in a worktree of its own for reading whole files and running checks:

```bash
git fetch --prune origin
gh pr view <n> --json title,body,baseRefName,headRefName,headRefOid,closingIssuesReferences
gh pr diff <n>
git fetch --quiet origin "pull/<n>/head"   # brings a fork's head too; origin/<headRefName> has only same-repo PRs
tmp="$(mktemp -d)"; git worktree add --quiet --detach "$tmp/pr-<n>" <headRefOid> && echo "$tmp/pr-<n>"
```

Work in the printed path until the review is posted, then `git worktree remove --force <path> && rmdir <its parent>`. Fixes happen in Step 4, on the branch itself.

Local mode: pin `git diff <fixed-point>...HEAD`, confirm the ref resolves and the diff isn't empty before anything else.

Read the changed files whole, run the repo's checks — tests, lint, type check, what CI runs (a failure the diff caused is a finding) — then read [LENSES.md](LENSES.md) and review on three axes: **Correctness**, **Standards**, **Spec**. On a re-review, review only `<reviewed-oid>..HEAD` and read the existing threads first so you don't repeat one.

Don't regenerate committed artifacts or re-run data pipelines to check outputs; a claim only a re-run could verify goes in the summary as not checked.

Several PRs may be reviewed in parallel by sub-agents. Create each one's worktree yourself and pass the path; tell it to return findings only, edit nothing, delete nothing — including its worktree, which you remove — and keep any scratch files inside that worktree. Verifying, posting and fixing stay with you.

Spec source, first match: the PR's linked issues and body → a path the user gave → a file under `docs/`, `specs/` or `.scratch/` matching the branch. None found → skip the Spec axis and say so in the summary.

**Verify before you keep a finding.** Open the code and name the input or state that triggers it. Drop what you can't ground, and style opinions the repo doesn't enforce. Zero findings is a result — say what you checked. In a stack, a finding goes on the **lowest PR that introduces it**.

## Step 3 — Comment (PR mode)

One review per PR, with a summary and inline comments. Each comment is one finding: bold severity (**Bug**, **Security**, **Test**, **Standards**, **Spec**, **Smell**, **Nit**), the problem, the trigger, the fix.

Post with [scripts/post-review.sh](scripts/post-review.sh), the payload on stdin — run it from the repo under review by its path in this skill's directory (`<skill-dir>/scripts/post-review.sh`). It pins the review to the PR's current head as a `COMMENT`, checks every comment's `path` and `line` sits inside a hunk before sending anything (new-file numbers; `"side": "LEFT"` with old-file numbers for a deleted line; `start_line` + `line` for a range, both in one hunk), refuses while you already have a draft review on the PR, and deletes the empty draft a failed post leaves behind.

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

Exit 2 lists the comments outside the diff: move them into the body and post again. Post one PR at a time, after the payload is final.

No findings → still post the summary, so the PR stops reading as unreviewed. Comments are public and can't be unsent; post only what you'd stand behind.

## Step 4 — Fix and resolve

**PR mode:** call the Skill tool with "address-review-findings" for each PR that got comments. It reads the threads just posted, fixes, commits, pushes, replies with the commit, resolves, and carries fixes up a stack. A stack is fixed one layer at a time, bottom-up, each layer's fixes carried up before the next starts — never in parallel; independent PRs may run in parallel. Expect the verdict **fix** nearly every time; if re-reading shows a finding was wrong, reply saying so and resolve it.

**Local mode:** fix each real finding, run the repo's checks, then call the Skill tool with "conventional-commit" to commit.

## Step 5 — Report

Per PR: link, findings by severity, what was fixed (commit), what's still open and why. Include address-review-findings' per-thread lines; they are the record of what each fix answered. Then a **ready to merge** verdict per PR and per stack: open threads, conflicts, a layer still based on an unmerged branch, and CI from `gh pr checks <n>` run now — never a CI status you didn't just read. Before reporting, `git worktree list` shows none of the worktrees you created, and the scripts copy's folder is deleted. Name every PR skipped because its review was recent enough. Local mode: findings per axis, fixed or not, checks run.

Merging is not part of this skill. Don't rewrite history on a branch under review — fixes are new commits.
