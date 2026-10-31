#!/usr/bin/env bash
set -euo pipefail

# Name the forge the current repo's PRs live on, read from `git remote get-url origin`
# only — never GH_REPO or another remote such as `upstream` — as one line whose fields
# are separated by tabs, since an Azure DevOps project or repo name can hold spaces:
#
#   forge.sh
#   github	<owner>/<repo>
#   azure-devops	<org>	<project>	<repo>      (URL-decoded: %20 → space)
#   unsupported	<host>
#
# Azure DevOps hosts are checked first (dev.azure.com, ssh.dev.azure.com with v3/
# paths, *.visualstudio.com), then github.com, then any other host `gh repo view
# <origin URL>` accepts (GitHub Enterprise). An SSH host alias is first resolved to its
# real host with `ssh -G`. GH_ENTERPRISE_TOKEN reaches that probe only when the host is
# GH_HOST. An unsupported host still exits 0. Exits 1 with a message
# when there is no `origin` remote.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

url="$(git remote get-url origin 2>/dev/null)" \
  || { echo "error: no 'origin' remote here (or not a git repo) — can't tell the forge" >&2; exit 1; }

# Split into host and path: scheme://[user@]host[:port]/path, or scp-style [user@]host:path.
if [[ "$url" =~ ^([a-zA-Z][a-zA-Z0-9+.-]*)://([^/@]*@)?([^/:]+)(:[0-9]*)?(/.*)?$ ]]; then
  scheme="${BASH_REMATCH[1]}" host="${BASH_REMATCH[3]}" path="${BASH_REMATCH[5]#/}"
elif [[ "$url" =~ ^([^/@:]*@)?([^/:]+):(.*)$ ]]; then
  scheme=ssh host="${BASH_REMATCH[2]}" path="${BASH_REMATCH[3]#/}"
else
  printf 'unsupported\t%s\n' "$url"; exit 0
fi
lower() { tr "[:upper:]" "[:lower:]" <<<"$1"; }
host="$(lower "$host")" path="${path%/}"

# An SSH host alias (`Host github-work` with `HostName github.com` in ~/.ssh/config) names
# its real host only to ssh: gh reads a URL's host literally. So ask ssh for the real one.
if [[ "$(lower "$scheme")" == ssh ]] \
   && real="$(ssh -G "$host" 2>/dev/null | awk '$1 == "hostname" && !n++ { print $2 }')" \
   && [[ -n "$real" && "$(lower "$real")" != "$host" ]]; then
  host="$(lower "$real")"
  [[ "$host" == ssh.github.com ]] && host=github.com   # GitHub's SSH-over-port-443 endpoint
  url="https://$host/$path"
fi

decode() { local s="${1//\\/\\\\}"; printf '%b' "${s//%/\\x}"; }
ado() {
  local org="$1" project="$2" repo="$3"
  printf 'azure-devops\t%s\t%s\t%s\n' "$(decode "$org")" "$(decode "$project")" "$(decode "$repo")"; exit 0
}
IFS=/ read -r -a parts <<<"$path"

case "$host" in
  ssh.dev.azure.com | vs-ssh.visualstudio.com)        # v3/<org>/<project>/<repo>
    [[ "${parts[0]:-}" == v3 && ${#parts[@]} -eq 4 ]] && ado "${parts[1]}" "${parts[2]}" "${parts[3]}" ;;
  dev.azure.com)                                      # <org>/[<project>/]_git/<repo>
    (( ${#parts[@]} == 4 )) && [[ "${parts[2]}" == _git ]] && ado "${parts[0]}" "${parts[1]}" "${parts[3]}"
    # No project in the URL: the project has the repo's name.
    (( ${#parts[@]} == 3 )) && [[ "${parts[1]}" == _git ]] && ado "${parts[0]}" "${parts[2]}" "${parts[2]}" ;;
  *.visualstudio.com)                                 # [DefaultCollection/][<project>/]_git/<repo>
    org="${host%.visualstudio.com}"
    [[ "${parts[0]:-}" == DefaultCollection ]] && parts=("${parts[@]:1}")
    (( ${#parts[@]} == 3 )) && [[ "${parts[1]}" == _git ]] && ado "$org" "${parts[0]}" "${parts[2]}"
    (( ${#parts[@]} == 2 )) && [[ "${parts[0]}" == _git ]] && ado "$org" "${parts[1]}" "${parts[1]}" ;;
  github.com | www.github.com)
    if (( ${#parts[@]} == 2 )); then printf 'github\t%s/%s\n' "${parts[0]}" "${parts[1]%.git}"; exit 0; fi ;;
  *)
    # GitHub Enterprise, or an SSH host alias for it: ask gh. The URL argument wins over GH_REPO anyway.
    # gh sends GH_ENTERPRISE_TOKEN to any host but github.com, so keep it for GH_HOST, the host
    # it's set up for, and never hand it to whatever host a clone's origin names.
    probe=(-u GH_REPO)
    [[ "$host" == "$(lower "${GH_HOST:-}")" ]] || probe+=(-u GH_ENTERPRISE_TOKEN -u GITHUB_ENTERPRISE_TOKEN)
    if repo="$(env "${probe[@]}" gh repo view "$url" --json nameWithOwner --jq .nameWithOwner 2>/dev/null)" \
       && [[ "$repo" == */* ]]; then
      printf 'github\t%s\n' "$repo"; exit 0
    fi ;;
esac
printf 'unsupported\t%s\n' "$host"
