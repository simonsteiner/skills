#!/usr/bin/env bash
set -euo pipefail

# List the open issues a public SonarCloud project reports on one pull request, every
# page of them, one JSON object per line:
#
#   sonar-issues.sh <project-key> <pr-key>
#   {"rule":"java:S2259","severity":"MAJOR","type":"BUG","path":"src/A.java","line":12,"message":"..."}
#
# The project key is in sonar-project.properties or the CI config; the PR key is the
# forge's PR number or id. Pages hold 500 issues, the most the API allows, and the API
# stops at 10000.
# For a private project or a SonarQube server, use the SonarQube MCP tool or the sonar
# CLI instead. Prints nothing when the PR has no open issue; exits 1 when a request fails.

if [[ "${1:-}" == -h || "${1:-}" == --help ]]; then
  sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"  # the comment above
  exit 0
fi

key="${1:-}" pr="${2:-}"
[[ -n "$key" && -n "$pr" ]] || { echo "error: expected <project-key> <pr-key>" >&2; exit 1; }

page=1 seen=0
while :; do
  out="$(curl -fsS --get "https://sonarcloud.io/api/issues/search" \
    --data-urlencode "componentKeys=$key" --data-urlencode "pullRequest=$pr" \
    --data "resolved=false" --data "ps=500" --data "p=$page")" \
    || { echo "error: SonarCloud request failed (page $page) — a private project needs the MCP tool or the sonar CLI" >&2; exit 1; }
  jq -c '.issues[] | {rule, severity, type, path: (.component | sub("^[^:]*:"; "")), line, message}' <<<"$out"
  count="$(jq '.issues | length' <<<"$out")" total="$(jq '.paging.total // .total // 0' <<<"$out")"
  seen=$((seen + count))
  (( count > 0 && seen < total )) || break
  (( seen < 10000 )) || { echo "note: SonarCloud pages no further than 10000 issues; $total are open" >&2; break; }
  page=$((page + 1))
done
