#!/usr/bin/env bash
set -euo pipefail

# Print a remote's default branch name ("main", not "origin/main"). Never assumes one.
#
#   default-branch.sh [--refresh] [remote]   default remote: origin
#
# Reads refs/remotes/<remote>/HEAD. Only when that's missing, or names a branch the
# remote no longer has, asks the remote (`git remote set-head <remote> --auto`) and
# reads it again. --refresh always asks first: a fetch never moves an existing remote
# HEAD, so a default switched upstream (old branch kept) is otherwise missed.
# Exits 1 with an error when the remote is unknown or has no HEAD, 2 on bad usage.

refresh=
args=()
for arg in "$@"; do
  case "$arg" in
    -h|--help) sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"; exit 0 ;;  # the comment above
    --refresh) refresh=1 ;;
    -*) echo "error: unknown option $arg" >&2; exit 2 ;;
    *) args+=("$arg") ;;
  esac
done
[[ ${#args[@]} -le 1 ]] || { echo "error: expected at most one remote, got ${#args[@]}" >&2; exit 2; }
remote="${args[0]:-origin}"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repository" >&2; exit 1; }
git remote get-url "$remote" >/dev/null 2>&1 || { echo "error: no remote '$remote' (git remote -v lists them)" >&2; exit 1; }

remote_head() {
  local ref
  ref="$(git symbolic-ref --quiet "refs/remotes/$remote/HEAD")" || return 1
  git rev-parse --verify --quiet "$ref" >/dev/null || return 1
  echo "${ref#"refs/remotes/$remote/"}"
}

[[ -z "$refresh" ]] && remote_head && exit 0
git remote set-head "$remote" --auto >/dev/null \
  || { echo "error: could not ask '$remote' for its default branch (git remote set-head $remote --auto failed)" >&2; exit 1; }
remote_head || { echo "error: '$remote' reports no default branch" >&2; exit 1; }
