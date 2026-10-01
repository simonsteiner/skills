---
name: sync-and-branch
description: >
  Put work on a fresh branch cut from the up-to-date default branch — carrying uncommitted changes along when they're the branch's work — or sync a fork's default branch with its upstream. Use when the user says "commit this to a new branch", "move this to a feature branch", "branch off fresh main", or "sync with upstream".
---

# Sync and Branch

Get the work onto a branch based on the latest default branch, without stashing, committing, or discarding anything on the user's behalf. Worktrees are the harness's job, not this skill's.

---

## Find the default branch

Never assume `main`:

```bash
git remote set-head origin --auto >/dev/null    # only if the next line fails
default="$(git symbolic-ref --short refs/remotes/origin/HEAD)"; default="${default#origin/}"
git fetch --prune origin
```

---

## Cut the branch

Name it `<type>/<kebab-slug>`, the type matching the repo's history (`feat/`, `fix/`, `docs/`, `refactor/`, `chore/`) and the slug describing the outcome — read the uncommitted diff to name it, don't guess from the conversation.

```bash
git switch --no-track -c <name> "origin/$default"
```

- **Uncommitted changes come along** when they apply cleanly to the new base. No stash, no patch files.
- **`--no-track` is not optional.** Without it the branch tracks `origin/$default`: `git status` reports it ahead of `main`, and a bare `git pull` merges the default branch into it.
- **Unpushed commits on the current branch** stay there — say so before switching, so nothing looks abandoned.

**If git refuses the switch** ("local changes would be overwritten"), the work depends on code `origin/$default` doesn't have:

- On a feature branch → it was built on that branch. Stack on it instead — `git switch -c <name>` from the current HEAD — and say plainly that the PR must target `<current-branch>` until that merges.
- On the default branch → origin changed the same files. Stop and report the overlap (`git diff --name-only HEAD "origin/$default"` against `git status --short`); bringing the work across is a merge, and that's the user's call.

Report the branch, the SHA it's based on, and the files that came along. Don't push an empty branch. If the user asked to commit, that's next — call the Skill tool with "conventional-commit".

---

## Sync a fork with upstream

```bash
git remote get-url upstream || git remote add upstream <url>   # ask for the url if missing
git fetch --prune upstream
up="$(git remote set-head upstream --auto >/dev/null; git symbolic-ref --short refs/remotes/upstream/HEAD)"; up="${up#upstream/}"
git log --oneline "upstream/$up..origin/$default"    # what the fork carries on top
```

- **The fork carries nothing of its own** → `git switch "$default" && git merge --ff-only "upstream/$up" && git push origin "$default"`.
- **The fork has its own commits** → merge on a branch, never rebase published history:

  ```bash
  git switch --no-track -c "chore/sync-upstream-$(date +%F)" "origin/$default"
  git merge "upstream/$up"
  ```

  Resolve conflicts keeping the fork's intent, run what the repo runs (upstream may have changed the toolchain), push, and open a PR.

Report how many upstream commits came in, the notable ones, and every conflict and how it was resolved.

---

## Rules of thumb

- `--ff-only` and a refused `git switch` are information, not obstacles. Never route around them with stash, reset, or force.
- One branch per intent. A dirty tree holding two concerns gets carried once; `conventional-commit` splits the commits.
