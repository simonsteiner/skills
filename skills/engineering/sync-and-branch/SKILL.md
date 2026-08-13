---
name: sync-and-branch
description: >
  Fast-forward the default branch to origin and cut a fresh feature branch from it. Use when the user wants to start a new feature, task, or piece of work, asks for a new branch, or says to sync with main first — and before starting work that would otherwise land on a stale base.
---

# Sync and Branch

Bring the default branch up to date and start the new work on top of it. **Refuses to run on a dirty worktree** — nothing here stashes, commits, or discards anything on the user's behalf.

---

## Step 1 — Preflight

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
git stash list
```

Stop and report — do not "clean up" — if:

- **`git status --porcelain` is non-empty.** Uncommitted work would follow you onto the new branch or block the switch. List what's dirty and ask the user to commit, stash, or discard it themselves.
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

## Rules of thumb

- Refuse rather than tidy. Stashing someone's uncommitted work to unblock yourself is how work gets lost.
- A failed `--ff-only` is information, not an obstacle to route around.
- One branch per intent. If the user describes two unrelated things, ask which one this branch is for.
- Already on an up-to-date default branch with a clean tree? Steps 1–3 are near-instant — still run them, that's how you know.
