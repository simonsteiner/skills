#!/usr/bin/env bash
set -euo pipefail

# Print a remote's default branch name ("main", not "origin/main"). Never assumes one.
#
#   default-branch.sh [remote]   default remote: origin
#
# Reads refs/remotes/<remote>/HEAD. Only when that's missing, or names a branch the
# remote no longer has, asks the remote (`git remote set-head <remote> --auto`) and
# reads it again. Exits 1 with an error when the remote is unknown or has no HEAD,
# 2 on bad usage.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi
[[ $# -le 1 ]] || { echo "error: expected at most one remote, got $#" >&2; exit 2; }
remote="${1:-origin}"
git remote get-url "$remote" >/dev/null 2>&1 || { echo "error: no remote '$remote' (git remote -v lists them)" >&2; exit 1; }

remote_head() {
  local ref
  ref="$(git symbolic-ref --quiet --short "refs/remotes/$remote/HEAD")" || return 1
  git rev-parse --verify --quiet "refs/remotes/$ref" >/dev/null || return 1
  echo "${ref#"$remote"/}"
}

remote_head && exit 0
git remote set-head "$remote" --auto >/dev/null 2>&1 \
  || { echo "error: could not ask '$remote' for its default branch (git remote set-head $remote --auto failed)" >&2; exit 1; }
remote_head || { echo "error: '$remote' reports no default branch" >&2; exit 1; }
