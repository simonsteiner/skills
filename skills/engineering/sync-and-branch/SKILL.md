---
name: sync-and-branch
description: >
  Fast-forward the default branch to origin and cut a fresh feature branch from it, in place or as a new git worktree when the current tree is dirty. Use when the user wants to start a new feature, task, or piece of work, asks for a new branch or a worktree, or says to sync with main first — and before starting work that would otherwise land on a stale base.
---

# Sync and Branch

Bring the default branch up to date and start the new work on top of it. Nothing here stashes, commits, or discards anything on the user's behalf.

A dirty worktree isn't a dead end: switching in place would disturb the work, so **branch into a new git worktree instead** (Step 6) and leave it exactly where it is. In-place is the default when the tree is clean.

---

## Step 1 — Preflight

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
git stash list
git worktree list   # what already exists, and which branches are spoken for
```

**`git status --porcelain` non-empty picks the route, it doesn't stop the run.** Uncommitted work would follow you onto the new branch or block the switch, so take Step 6 instead of Steps 3–5 and say why. Never stash or commit it to clear the way.

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
- Check the name is free, locally and on the remote:

```bash
git rev-parse --verify --quiet <name>              # non-empty = taken locally
git ls-remote --exit-code --heads origin <name>    # exit 0 = taken on origin
```

If the user didn't describe the work, ask for one line about it before naming — a branch name is the first commit message.

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

## Step 6 — The worktree route (dirty tree)

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

- **`--no-track` is not optional.** Without it the new branch is created tracking `origin/$default`, so `git status` reports it as ahead of `main` and a bare `git pull` pulls the default branch into the feature branch.
- `<slug>` is the branch name with `/` flattened — `feat/add-foo` → `feat-add-foo`. A path is not a ref; nested directories from a branch name are noise.
- The branch must not already exist: `git worktree add -b` fails outright if it does, and git refuses to check out one branch in two worktrees at once. Step 4's availability check is what prevents this.

Report the **absolute path** of the new worktree and the fact that the shell doesn't move: the session stays in the original directory, and the user has to `cd` there. An agent continuing the work has to change directory too, or it will edit the wrong checkout.

When the work is done: `git worktree remove <path>` — which deletes the directory but keeps the branch, so a merged branch still needs its own cleanup. `git worktree list` shows what exists; `git worktree prune` clears records of directories deleted by hand.

---

## Rules of thumb

- Branch beside the work rather than tidying it away. Stashing someone's uncommitted work to unblock yourself is how work gets lost; a worktree needs no one's tree to be clean.
- A failed `--ff-only` is information, not an obstacle to route around.
- One branch per intent. If the user describes two unrelated things, ask which one this branch is for.
- Already on an up-to-date default branch with a clean tree? Steps 1–3 are near-instant — still run them, that's how you know.
