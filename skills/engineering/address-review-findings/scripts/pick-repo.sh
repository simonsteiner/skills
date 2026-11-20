#!/usr/bin/env bash
set -euo pipefail

# Print the repos a PR of this checkout can live on, one per line, each ready to use as
# GH_REPO or --repo (owner/repo on github.com, host/owner/repo elsewhere):
#
#   pick-repo.sh
#   acme/web        gh's default repo: the upstream in a fork checkout
#   me/web          origin's repo, when it differs
#
# Given PRs, print the repo each one lives on instead, one "<n><TAB><repo>" line per PR:
#
#   pick-repo.sh 12 15              PRs by number
#   pick-repo.sh --head feat/x      the open PR whose head is that branch, from origin's owner
#   pick-repo.sh --head feat/x 12   a number on both repos goes to the one whose head is feat/x
#
# A number found on one repo goes there. Found on both, it goes to the one whose head
# branch is --head (default: the checkout's branch); when that matches neither or both,
# the PR is ambiguous. Ambiguous and missing PRs go to stderr with their candidate URLs,
# after the resolved lines on stdout; the exit is then 3 (ambiguous) or 4 (not found).
#
# With GH_HOST naming another host, a github.com repo is printed as github.com/owner/repo,
# since gh resolves a bare owner/repo on GH_HOST. A GH_REPO already set is the only repo:
# printed alone, or with each PR number unchecked. Origin's repo is read from
# `git remote get-url origin` without handing the raw URL to gh: an SSH host alias is
# resolved with `ssh -G`, GitHub's ssh.github.com maps to github.com, and a github.com
# origin needs no gh call. Another host is asked through `gh repo view`, with
# GH_ENTERPRISE_TOKEN kept only for GH_HOST, since gh sends that token to any host but
# github.com. --head counts only PRs whose head repo belongs to origin's owner, when
# origin is known: another fork's PR from a same-named branch isn't this checkout's.
# Exits 1 when neither repo can be read or a gh lookup fails for any reason but a missing
# PR, 2 on bad usage.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

head="" prs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --head) [[ $# -ge 2 && -n "$2" ]] || { echo "error: --head needs a branch" >&2; exit 2; }; head="$2"; shift ;;
    *) [[ "$1" =~ ^[0-9]+$ ]] || { echo "error: expected a PR number or --head, got '$1'" >&2; exit 2; }; prs+=("$1") ;;
  esac
  shift
done
lookup=false
[[ ${#prs[@]} -eq 0 && -z "$head" ]] || lookup=true

lower() { local s="$1"; tr "[:upper:]" "[:lower:]" <<<"$s"; }
# owner/repo on github.com, host/owner/repo elsewhere, from a repo's web URL. A bare
# owner/repo resolves on GH_HOST, so github.com is spelled out when GH_HOST names another host.
from_url() {
  local url="$1" host repo
  [[ "$url" =~ ^https?://([^/]+)/([^/]+/[^/]+)$ ]] || return 1
  host="$(lower "${BASH_REMATCH[1]}")" repo="${BASH_REMATCH[2]}"
  if [[ "$host" == github.com && "$(lower "${GH_HOST:-github.com}")" == github.com ]]; then
    printf '%s\n' "$repo"
  else
    printf '%s/%s\n' "$host" "$repo"
  fi
}

# The repos a PR can live on: GH_REPO alone, else gh's default and origin's.
read_repos() {
  if [[ -n "${GH_REPO:-}" ]]; then repos=("$GH_REPO"); return; fi
  local default url host path scheme real probe
  default="$(gh repo view --json url --jq .url 2>/dev/null)" && default="$(from_url "$default")" || default=""

  origin=""
  if url="$(git remote get-url origin 2>/dev/null)"; then
    # Same parsing as review-prs' forge.sh: scheme://[user@]host[:port]/path, or scp-style [user@]host:path.
    host="" path="" scheme=""
    if [[ "$url" =~ ^([a-zA-Z][a-zA-Z0-9+.-]*)://([^/@]*@)?([^/:]+)(:[0-9]*)?(/.*)?$ ]]; then
      scheme="${BASH_REMATCH[1]}" host="${BASH_REMATCH[3]}" path="${BASH_REMATCH[5]#/}"
    elif [[ "$url" =~ ^([^/@:]*@)?([^/:]+):(.*)$ ]]; then
      scheme=ssh host="${BASH_REMATCH[2]}" path="${BASH_REMATCH[3]#/}"
    fi
    host="$(lower "$host")" path="${path%/}" path="${path%.git}"
    if [[ "$(lower "$scheme")" == ssh ]] \
       && real="$(ssh -G "$host" 2>/dev/null | awk '$1 == "hostname" && !n++ { print $2 }')" \
       && [[ -n "$real" ]]; then
      host="$(lower "$real")"
    fi
    [[ "$host" == ssh.github.com || "$host" == www.github.com ]] && host=github.com
    if [[ "$host" == github.com && "$path" =~ ^[^/]+/[^/]+$ ]]; then
      origin="$(from_url "https://github.com/$path")"
    elif [[ -n "$host" && "$path" =~ ^[^/]+/[^/]+$ ]]; then
      probe=(-u GH_REPO)
      [[ "$host" == "$(lower "${GH_HOST:-}")" ]] || probe+=(-u GH_ENTERPRISE_TOKEN -u GITHUB_ENTERPRISE_TOKEN)
      origin="$(env "${probe[@]}" gh repo view "https://$host/$path" --json url --jq .url 2>/dev/null)" \
        && origin="$(from_url "$origin")" || origin=""
    fi
  fi

  [[ -n "$default" || -n "$origin" ]] || { echo "error: could not read gh's default repo or origin's" >&2; exit 1; }
  repos=()
  [[ -z "$default" ]] || repos+=("$default")
  [[ -z "$origin" || "$(lower "$origin")" == "$(lower "$default")" ]] || repos+=("$origin")
}

repos=() origin=""
read_repos
$lookup || { printf '%s\n' "${repos[@]}"; exit 0; }

status=0
# Report a PR that couldn't be placed; an ambiguous one (3) outranks a missing one (4).
miss() { echo "$2" >&2; [[ $status -eq 3 ]] || status="$1"; }

if [[ ${#prs[@]} -eq 0 ]]; then
  found=() owner=""
  [[ -z "$origin" ]] || owner="$(lower "$(awk -F/ '{ print $(NF-1) }' <<<"$origin")")"
  for r in "${repos[@]}"; do
    out="$(gh pr list --head "$head" --state open --repo "$r" --json number,url,headRepositoryOwner \
      --jq '.[] | [.number, .url, (.headRepositoryOwner.login // "")] | @tsv')"
    while IFS=$'\t' read -r n url o; do
      [[ -n "$n" ]] || continue
      [[ -z "$owner" || "$(lower "$o")" == "$owner" ]] || continue  # another fork's branch of that name
      found+=("$n"$'\t'"$r"$'\t'"$url")
    done <<<"$out"
  done
  case ${#found[@]} in
    0) miss 4 "error: no open PR for branch $head on ${repos[*]}" ;;
    1) cut -f1,2 <<<"${found[0]}" ;;
    *) miss 3 "error: several open PRs for branch $head: $(printf '%s\n' "${found[@]}" | cut -f3 | paste -sd ' ')" ;;
  esac
  exit "$status"
fi

if [[ ${#repos[@]} -eq 1 ]]; then
  for n in "${prs[@]}"; do printf '%s\t%s\n' "$n" "${repos[0]}"; done
  exit 0
fi

[[ -n "$head" ]] || head="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
errors="$(mktemp)"
trap 'rm -f "$errors"' EXIT
for n in "${prs[@]}"; do
  hits=() matches=()
  for r in "${repos[@]}"; do
    if ! info="$(gh pr view "$n" --repo "$r" --json url,headRefName --jq '[.url, .headRefName] | @tsv' 2>"$errors")"; then
      # Only a missing PR means "not on this repo"; a network, auth or rate-limit failure
      # would otherwise send the PR to the other repo, or report it as not found.
      grep -q "Could not resolve to a PullRequest" "$errors" && continue
      echo "error: could not look up PR #$n on $r: $(cat "$errors")" >&2
      exit 1
    fi
    [[ -n "$info" ]] || continue
    hits+=("$r"$'\t'"$info")
    [[ -n "$head" && "${info#*$'\t'}" == "$head" ]] && matches+=("$r")
  done
  if [[ ${#hits[@]} -eq 1 ]]; then
    printf '%s\t%s\n' "$n" "${hits[0]%%$'\t'*}"
  elif [[ ${#hits[@]} -eq 0 ]]; then
    miss 4 "error: PR #$n not found on ${repos[*]}"
  elif [[ ${#matches[@]} -eq 1 ]]; then
    printf '%s\t%s\n' "$n" "${matches[0]}"
  else
    miss 3 "error: PR #$n is on both repos and its head branch doesn't single one out: $(printf '%s\n' "${hits[@]}" | cut -f2 | paste -sd ' ')"
  fi
done
exit "$status"
