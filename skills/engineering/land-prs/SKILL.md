---
name: land-prs
description: >
  Merge GitHub pull requests — one, several, or a stack in order — retargeting each next PR before its base branch is deleted, waiting for checks, and carrying the merged base into the next PR, then sync the default branch, clean up merged branches and worktrees, and deploy when asked. Use when the user says "merge the PR(s)", "merge the stack in order", "merge and deploy", "merge and publish", "land these", "clean merged branches", or reports a PR merged and asks to fix the next one's conflicts.
---

# Land PRs

Merge what's ready, in the right order, and leave the repo tidy behind it. Merging is the user's call — this skill runs only when they asked to merge, and it never merges a PR that isn't ready to go: an open review thread, a red check, or a conflict stops that PR, and in a stack, everything above it.

Getting a stack wrong is expensive and quiet: delete a base branch before the PR above it is retargeted and GitHub **closes** that PR instead of moving it. Reopening means re-pushing the branch and retargeting it by hand. The order of operations below exists to prevent exactly that.

---

## Step 1 — Which PRs, in which order

No PR named → the one for the current branch. "The PRs", "the stack", a list → map them:

```bash
gh pr list --state open --author @me --json number,title,headRefName,baseRefName,isDraft,url
default="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)"
```

Order the set bottom-up: a PR whose base is `$default` comes first, then the PR whose base is its head branch, and so on. Two PRs on the same base are independent — order by number. Say the order before merging anything.

---

## Step 2 — Is each one ready

Check every PR in the set up front, so a blocker at the top of the stack is known before the bottom merges:

```bash
gh pr view <n> --json isDraft,mergeable,mergeStateStatus,reviewDecision,baseRefName
gh pr checks <n>
```

Unresolved review threads need GraphQL; use the query from the `address-review-findings` skill's Step 1, and count `isResolved: false`.

A PR is ready when it's not a draft, has no unresolved threads, isn't `CHANGES_REQUESTED`, and its checks are green or still running. Otherwise:

- **Unresolved threads, and the user asked to address them too** ("address findings and merge") → call the Skill tool with "address-review-findings" for that PR first, then re-check.
- **Anything else** → that PR and everything stacked on it stay unmerged. Merge what's below it, then report the blocker.

---

## Step 3 — Pick the merge method

Use what the repo already does. Read the default branch's first-parent history:

```bash
git fetch --prune origin
git log --first-parent -15 --format=%s "origin/$default"
gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed,deleteBranchOnMerge
```

`Merge pull request #…` subjects → `--merge`. Subjects ending in `(#123)` → `--squash`. Use the one the history shows and the repo allows; if history is mixed, prefer `--squash` when allowed. The user naming a method wins.

---

## Step 4 — Merge, bottom-up

For each PR, in order:

1. **Wait for checks:** `gh pr checks <n> --watch --fail-fast`. Red → stop here (Step 2's rule). A repo with no CI reports *no checks* and exits non-zero — that's not a failure; carry on.
2. **Retarget the next PR first.** If another PR in the set has this PR's head as its base:

   ```bash
   gh pr edit <next> --base "$default"
   ```

   Do this **before** the merge below, every time — even when the repo auto-deletes merged branches. It's the step that keeps the next PR open.
3. **Merge:**

   ```bash
   gh pr merge <n> --<method> --delete-branch
   gh pr view <n> --json state,mergeCommit --jq '.state + " " + .mergeCommit.oid'   # MERGED <sha>
   ```

   `--delete-branch` also deletes the local branch and switches off it if it was checked out — a dirty tree makes that fail, so land from a clean checkout (`git status --porcelain` empty) or a worktree.
4. **Carry the merge into the next PR.** With `--merge`, the next PR already contains this one's commits and usually needs nothing. With `--squash` or `--rebase`, the default branch now holds a *copy* of those commits, and the next PR still holds the originals — bring the default branch in:

   ```bash
   gh pr checkout <next>
   git merge --no-edit "origin/$default"    # after a fresh git fetch origin
   ```

   Conflicts here are almost always the same change arriving twice. Where a hunk is identical on both sides, take either. Where the next PR changed lines the merged PR also changed, keep the next PR's version — it was written on top of them. Anything else is a real conflict: resolve it keeping both intents, run what the repo runs, and say what you resolved. Then commit and push, and go back to 1 for the next PR — its checks re-run on the push.

   Merge, don't rebase: rebasing the next branch rewrites history under its reviewers.

---

## Step 5 — Tidy up

```bash
git fetch --prune origin
git switch "$default" && git merge --ff-only "origin/$default"   # or: git fetch origin "$default:$default" if the tree is dirty
```

Then remove what the merged PRs leave behind:

- **Worktrees** on a merged branch: `git worktree list`, then `git worktree remove <path>` — only when it's clean. A dirty one stays; report it.
- **Local branches** whose PR is merged. A squash-merged branch never looks merged to `git branch -d`, so decide from GitHub instead: delete with `git branch -D <b>` only when `gh pr view <b> --json state,headRefOid` says `MERGED` **and** the local tip equals `headRefOid` (or is an ancestor of it). A local tip with commits beyond the PR head is unlanded work — leave it and say so.

"Clean merged branches" on its own is this step alone, applied to every local branch with a merged PR.

---

## Step 6 — Deploy, when asked

Only when the user asked ("merge and deploy", "publish"). Never invent a deploy command — find the one the repo documents:

- A workflow that deploys on push to the default branch (`.github/workflows/*` with `on: push` to it): the merge already triggered it. Watch it: `gh run list --branch "$default" --limit 5`, then `gh run watch <id> --exit-status`.
- Otherwise the documented command — `CLAUDE.md`/`AGENTS.md`, the README's deploy section, a `deploy` script in `package.json`, a `Makefile` target. Run it from the freshly synced default branch.
- Nothing documented → ask how this repo deploys. Don't guess.

Then verify the deploy did what it should — the URL responds, the version shows, the data is there — not just that the command exited 0.

---

## Step 7 — Report

- Each PR: number, title, merged as `<sha>` — or not merged, and the blocker.
- Conflicts resolved while carrying merges up the stack, and how.
- Branches and worktrees removed; anything left because it held unlanded work.
- Deploy: what ran, and how it was verified.

---

## Rules of thumb

- Retarget before you delete. Always, for every PR stacked on the one you're merging.
- One red PR stops the stack above it, not the PRs below it.
- `gh pr merge` succeeding isn't proof — check `state` is `MERGED`.
- Never force-push, and never merge with `--admin` to skip a failing check. A check that's wrong is a finding to report.
