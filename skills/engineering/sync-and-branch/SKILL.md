---
name: sync-and-branch
description: >
  Fast-forward the default branch to origin and cut a fresh feature branch from it — in place, carrying uncommitted work onto the new branch, or as a new git worktree beside unrelated work. Also syncs a fork's default branch with its upstream remote. Use when the user wants to start a new feature, task, or piece of work, asks for a new branch or a worktree, says "commit this to a new branch" or "move this to a feature branch", says to sync with main or "sync with upstream" — and before starting work that would otherwise land on a stale base.
---

# Sync and Branch

Bring the default branch up to date and put the work on a fresh branch on top of it. Nothing here stashes, commits, or discards anything on the user's behalf.

A dirty worktree picks the route, it doesn't stop the run. Ask one question of it: **is the uncommitted work the new branch's work?**

| Tree | Uncommitted work | Route |
|------|------------------|-------|
| clean | — | **in place** — Steps 3 and 5 |
| dirty | belongs on the new branch | **carry** — Step 6 |
| dirty | unrelated to the new branch | **worktree** — Step 7 |

"Commit this to a new branch", "move this to a feature branch", or a branch asked for right after the session made the edits all mean *carry*. When it's unclear whose changes they are or what they're for, take the worktree route — it touches nothing.

A fork syncing with the repo it was forked from is its own flow: Step 8.

---

## Step 1 — Preflight

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
git stash list
git worktree list   # what already exists, and which branches are spoken for
git remote -v       # an `upstream` remote means a fork
```

Never stash or commit the uncommitted work to clear the way — pick the route from the table above and say which one and why.

Stop and report — do not "clean up" — if:

- **The current branch has work that exists nowhere else.** Check it, minding that a branch may have no upstream at all:

```bash
# with an upstream: what hasn't been pushed
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null && git log '@{u}..HEAD' --oneline
# without one: what isn't on the default branch yet. origin/HEAD resolves on its own,
# so this works before step 2 has picked the branch apart
git log origin/HEAD..HEAD --oneline
```

`git log @{u}..HEAD` fails with *no upstream configured* on a fresh branch — that's expected, fall through to the second form rather than treating it as an error.

Leaving unpushed commits behind isn't fatal — they stay on their branch — but say so explicitly before moving, so nothing is abandoned by surprise.

---

## Step 2 — Find the default branch

Never assume `main`. Note the ref is remote-qualified — strip the remote before using it as a local branch name, or `git switch` detaches HEAD instead of switching.

```bash
git remote set-head origin --auto                          # only if the ref below is unset
default="$(git symbolic-ref --short refs/remotes/origin/HEAD)"   # -> origin/main
default="${default#origin/}"                                     # -> main
```

Carry `$default` into the next steps.

---

## Step 3 — Sync it

```bash
git fetch --prune origin
git switch "$default"
git merge --ff-only "origin/$default"
```

`--ff-only` is the point: it updates the branch or it fails. If it fails, the local default has diverged from origin — commits were made directly on it. **Stop and report**; resetting or merging it is the user's call, not a step in a branch-creation flow.

---

## Step 4 — Name the branch

- Prefix with the change type, matching the types this repo already uses in its history (`git log --oneline -20`): `feat/`, `fix/`, `docs/`, `refactor/`, `chore/`.
- Slug is kebab-case, describing the outcome, roughly ≤ 40 characters: `feat/curate-third-party-skills`, not `feat/changes` or `feat/simon-wip`.
- Include a ticket ID only if the repo's history shows them.
- On the carry route, name it after what the uncommitted diff actually does — read it, don't guess from the conversation.
- Check the name is free, locally and on the remote:

```bash
git rev-parse --verify --quiet <name>              # non-empty = taken locally
git ls-remote --exit-code --heads origin <name>    # exit 0 = taken on origin
```

If the user didn't describe the work and there's no diff to read, ask for one line about it before naming — a branch name is the first commit message.

---

## Step 5 — Create it and report

```bash
git switch -c <name>
```

Then tell the user:

- the new branch and the SHA it's based on,
- **what the sync pulled in** — `git log <old-sha>..HEAD --oneline` on the default branch. If someone else's work just landed, that's the most useful thing you can say.

Do not push and do not set an upstream. The first `git push -u origin <name>` belongs to the first real commit, not to an empty branch.

---

## Step 6 — The carry route (dirty tree, the work is the branch)

The uncommitted changes move onto the new branch, which starts from the fresh default branch. Steps 1, 2 and 4 still apply. Steps 3 and 5 are replaced by:

```bash
git fetch --prune origin

# Fast-forward the local default branch without checking it out. This fails if the
# default branch is checked out in any worktree, including this one; that's harmless —
# the new branch is cut from origin/$default either way.
git fetch origin "$default:$default"

git switch --no-track -c <name> "origin/$default"
```

- `git switch` carries uncommitted changes along when they apply cleanly to the new base, and refuses — touching nothing — when they don't. No stash, no patch files.
- **`--no-track` is not optional.** Starting from `origin/$default` would otherwise make the new branch track it, so `git status` reports it as ahead of `main` and a bare `git pull` pulls the default branch into the feature branch.

**If the switch refuses**, the work is built on something `origin/$default` doesn't have — usually the unmerged branch it was written on. Stack it there instead:

```bash
git switch -c <name>    # from the current HEAD, changes come along
```

Say plainly that the branch is **stacked on `<current-branch>`**, and that its PR should target that branch until it merges. Don't try to make the changes fit the default branch — that's rewriting the work, not branching it.

If the current branch *is* the default branch, there's nothing to stack on: origin changed the same files the work touches. Don't branch from the stale local default. Stop and report the overlapping files (`git diff --name-only HEAD "origin/$default"` against `git status --short`) — bringing the work across is a merge, and that's the user's call.

Report the branch, its base (`origin/$default` at `<sha>`, or the branch it's stacked on), and the files that came along (`git status --short`).

If the user asked to commit, the commit comes next — run the `conventional-commit` skill for it. This skill only moves the work; it never commits it.

---

## Step 7 — The worktree route (dirty tree, unrelated work)

A worktree is a second checkout of the same repository in another directory. The dirty tree stays exactly as it is, on its own branch, while the new branch gets a clean directory of its own.

Steps 1, 2 and 4 still apply — preflight, resolve `$default`, name the branch. Steps 3 and 5 are replaced by:

```bash
git fetch --prune origin

# Fast-forward the local default branch without checking it out. This fails if the
# default branch is checked out in any worktree; that's harmless here — skip it, since
# the new branch is cut from origin/$default either way.
git fetch origin "$default:$default"

repo="$(basename "$(git rev-parse --show-toplevel)")"
path="../$repo.worktrees/<slug>"
git worktree add --no-track "$path" -b <name> "origin/$default"
```

- `--no-track`, for the same reason as on the carry route.
- `<slug>` is the branch name with `/` flattened — `feat/add-foo` → `feat-add-foo`. A path is not a ref; nested directories from a branch name are noise.
- The branch must not already exist: `git worktree add -b` fails outright if it does, and git refuses to check out one branch in two worktrees at once. Step 4's availability check is what prevents this.

Report the **absolute path** of the new worktree and the fact that the shell doesn't move: the session stays in the original directory, and the user has to `cd` there. An agent continuing the work has to change directory too, or it will edit the wrong checkout.

When the work is done: `git worktree remove <path>` — which deletes the directory but keeps the branch, so a merged branch still needs its own cleanup. `git worktree list` shows what exists; `git worktree prune` clears records of directories deleted by hand.

---

## Step 8 — Sync a fork with upstream

"Sync with upstream" in a fork means: bring the fork's default branch up to date with the original repo's, and publish that to `origin`.

```bash
git remote get-url upstream    # missing? ask for the original repo's URL, then:
                               # git remote add upstream <url>
git fetch --prune upstream
up="$(git symbolic-ref --short refs/remotes/upstream/HEAD 2>/dev/null || { git remote set-head upstream --auto >/dev/null; git symbolic-ref --short refs/remotes/upstream/HEAD; })"
up="${up#upstream/}"           # upstream's default can differ from the fork's

git log --oneline "$default..upstream/$up" | wc -l    # what's new upstream
git log --oneline "upstream/$up..origin/$default"     # what the fork carries on top
```

Run Step 1's preflight first; a dirty tree takes this through a worktree (Step 7's commands, with the sync branch below as `<name>`) rather than switching in place.

- **The fork carries nothing of its own** → fast-forward and publish:

  ```bash
  git switch "$default"
  git merge --ff-only "upstream/$up"
  git push origin "$default"
  ```

- **The fork has its own commits on `$default`** → merge, never rebase; the fork's history is already published. Do it on a branch so the result gets checked before it lands:

  ```bash
  git switch --no-track -c "chore/sync-upstream-$(date +%F)" "origin/$default"
  git merge "upstream/$up"
  ```

  Resolve conflicts keeping the fork's intent, run what the repo runs (install, type check, tests — upstream may have changed the toolchain), commit the merge, and push the branch. Open a PR when the user works through PRs; otherwise report and let them merge.

Report how many upstream commits came in, the notable ones by subject, which conflicts were resolved and how, and anything upstream changed that the fork's own code relies on.

---

## Rules of thumb

- Branch beside the work rather than tidying it away. Stashing someone's uncommitted work to unblock yourself is how work gets lost; `git switch` and worktrees need no one's tree to be clean.
- A failed `--ff-only` is information, not an obstacle to route around.
- A refused `git switch` on the carry route is information too: the work depends on something the base doesn't have. Stack, don't force.
- One branch per intent. If the user describes two unrelated things, ask which one this branch is for — or, when the dirty tree already holds both, carry it once and let `conventional-commit` split the commits.
- Already on an up-to-date default branch with a clean tree? Steps 1–3 are near-instant — still run them, that's how you know.
