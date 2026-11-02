#!/usr/bin/env bash
set -euo pipefail

# Push a PR's fix round once, after its last commit, and only when the round is what
# you think it is. Run it from the PR's worktree:
#
#   push-once.sh <start> <commits> <branch> [<remote>]
#
# <start> is the PR's head before your work (its headRefOid). <commits> is how many
# commits you made on the PR's branch since: a carry-up merge counts as one, and the
# lower layer's commits it brings in don't (git rev-list --first-parent). <branch> is
# the PR's head branch. <remote> defaults to origin; a fork's PR passes the fork's URL.
#
# Refuses, before pushing anything, when the repo is bare, the tree has uncommitted
# changes to tracked files, <start> isn't an ancestor of HEAD, or the count differs.
# A rejected push exits 3: the branch moved, so merge it, run the checks again, and
# rerun with <commits> one higher for that merge.
# Prints the pushed commit.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

die() { echo "error: $*" >&2; exit 1; }

(( $# == 3 || $# == 4 )) || die "expected <start> <commits> <branch> [<remote>], got $# arguments"
start="$1" commits="$2" branch="$3" remote="${4:-origin}"
[[ "$commits" =~ ^[1-9][0-9]*$ ]] || die "expected a commit count of 1 or more, got '$commits' — with nothing committed there's nothing to push"
[[ -n "$branch" && "$branch" != -* ]] || die "expected a branch name, got '$branch'"

[[ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" == true ]] \
  || die "not inside a work tree (a bare repo, or the wrong directory) — run this from the PR's worktree"
[[ -z "$(git status --porcelain --untracked-files=no)" ]] \
  || die "uncommitted changes to tracked files — commit them as part of the round, or they'd be left out of the push"
start_oid="$(git rev-parse --verify --quiet "$start^{commit}")" \
  || die "'$start' isn't a commit here — fetch the PR's head first"
git merge-base --is-ancestor "$start_oid" HEAD \
  || die "$start isn't an ancestor of HEAD — this worktree isn't on the PR's branch"

made="$(git rev-list --count --first-parent "$start_oid..HEAD")"
if [[ "$made" != "$commits" ]]; then
  echo "error: expected $commits commit(s) since $start, found $made — nothing pushed:" >&2
  git log --first-parent --format='  %h %s' "$start_oid..HEAD" >&2
  exit 1
fi

if ! git push --quiet "$remote" "HEAD:refs/heads/$branch"; then
  echo "error: push to $remote $branch failed. If it was rejected, the branch moved: merge it, run the checks again, and rerun with $((commits + 1)) commits." >&2
  exit 3
fi
git rev-parse HEAD
