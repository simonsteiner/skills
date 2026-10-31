#!/usr/bin/env bash
set -euo pipefail

# Print the repos a PR of this checkout can live on, one per line, each ready to use as
# GH_REPO or --repo (owner/repo on github.com, host/owner/repo elsewhere):
#
#   pick-repo.sh
#   acme/web        gh's default repo: the upstream in a fork checkout
#   me/web          origin's repo, when it differs
#
# With GH_HOST naming another host, a github.com repo is printed as github.com/owner/repo,
# since gh resolves a bare owner/repo on GH_HOST. A GH_REPO already set is printed alone. One line → every PR lives there. Two lines →
# look each PR up on both. Origin's repo is read from `git remote get-url origin`
# without handing the raw URL to gh: an SSH host alias is resolved with `ssh -G`,
# GitHub's ssh.github.com maps to github.com, and a github.com origin needs no gh call.
# Another host is asked through `gh repo view`, with GH_ENTERPRISE_TOKEN kept only for
# GH_HOST, since gh sends that token to any host but github.com. Exits 1 when neither
# repo can be read.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

if [[ -n "${GH_REPO:-}" ]]; then printf '%s\n' "$GH_REPO"; exit 0; fi

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
[[ -z "$default" ]] || printf '%s\n' "$default"
[[ -z "$origin" || "$(lower "$origin")" == "$(lower "$default")" ]] || printf '%s\n' "$origin"
