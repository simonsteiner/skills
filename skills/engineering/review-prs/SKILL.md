---
name: review-prs
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

Per PR (stacks bottom-up, independent PRs one at a time): `gh pr checkout <n>` (tree must be clean), then read its diff against its base:

```bash
gh pr view <n> --json title,body,baseRefName,closingIssuesReferences
gh pr diff <n>
```

Local mode: pin `git diff <fixed-point>...HEAD`, confirm the ref resolves and the diff isn't empty before anything else.

Read the changed files whole, run what the repo runs (a failure the diff caused is a finding), then read [LENSES.md](LENSES.md) and review on three axes: **Correctness**, **Standards**, **Spec**. On a re-review, review only `<reviewed-oid>..HEAD` and read the existing threads first so you don't repeat one.

Spec source, first match: the PR's linked issues and body → a path the user gave → a file under `docs/`, `specs/` or `.scratch/` matching the branch. None found → skip the Spec axis and say so in the summary.

**Verify before you keep a finding.** Open the code and name the input or state that triggers it. Drop what you can't ground, and style opinions the repo doesn't enforce. Zero findings is a result — say what you checked. In a stack, a finding goes on the **lowest PR that introduces it**.

## Step 3 — Comment (PR mode)

One review per PR, with a summary and inline comments. Each comment is one finding: bold severity (**Bug**, **Security**, **Test**, **Standards**, **Spec**, **Smell**, **Nit**), the problem, the trigger, the fix.

1. For every comment, confirm its `path` and `line` sit inside a hunk of `gh pr diff <n>` (new-file line numbers; use `start_line` + `line` for a range). Code outside the diff goes in the summary instead.
2. Post, pinned to the PR's current head so comments land on what you reviewed:

```bash
gh pr view <n> --json headRefOid --jq .headRefOid
gh api repos/{owner}/{repo}/pulls/<n>/reviews --input - <<'JSON'
{
  "commit_id": "<headRefOid>",
  "event": "COMMENT",
  "body": "2 findings (1 Bug, 1 Test). Spec: matches #41. Tests and lint pass.",
  "comments": [
    {"path": "src/export.ts", "line": 40, "side": "RIGHT", "body": "**Bug** — `rows` is undefined when the query returns nothing, so this throws on an empty export. Default it to `[]`."}
  ]
}
JSON
```

3. On a 422, move the findings the error names into the summary body and post once more.

No findings → still post the summary, so the PR stops reading as unreviewed. Comments are public and can't be unsent; post only what you'd stand behind.

## Step 4 — Fix and resolve

**PR mode:** call the Skill tool with "address-review-findings" for each PR that got comments (stacks bottom-up). It reads the threads just posted, fixes, commits, pushes, replies with the commit, resolves, and carries fixes up a stack. Expect the verdict **fix** nearly every time; if re-reading shows a finding was wrong, reply saying so and resolve it.

**Local mode:** fix each real finding, run the repo's checks, then call the Skill tool with "conventional-commit" to commit.

## Step 5 — Report

Per PR: link, findings by severity, what was fixed (commit), what's still open and why. Then a **ready to merge** verdict per PR and per stack: open threads, `gh pr checks <n>`, conflicts, a layer still based on an unmerged branch. Name every PR skipped because its review was recent enough. Local mode: findings per axis, fixed or not, checks run.

Merging is not part of this skill. Don't rewrite history on a branch under review — fixes are new commits.
