#!/usr/bin/env bash
set -euo pipefail

# Upload local images or videos to GitHub as user attachments and print one
# Markdown line per file, in order, ready to paste into a PR, issue or comment.
#
#   upload.sh [--repo OWNER/REPO] <file>...   default repo: the current one, as gh resolves it
#
# Images print as ![name](url); videos print as a bare URL, which GitHub renders
# as a player (![]() would not). Accepted: png jpg jpeg gif webp svg mov mp4 webm.
# Uses the endpoint the web UI's drag-and-drop uses, through `gh api`, so it needs
# push access to the repo: a 404 means no access, so pass --repo with your fork.
# An upload stays private until a body that GitHub can show references its URL.
# Exits 1 when a file is missing, unsupported, or rejected, 2 on bad usage.

repo=
files=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"; exit 0 ;;  # the comment above
    --repo) [[ $# -ge 2 ]] || { echo "error: --repo needs OWNER/REPO" >&2; exit 2; }; repo="$2"; shift ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *) files+=("$1") ;;
  esac
  shift
done
[[ ${#files[@]} -gt 0 ]] || { echo "error: no files given (upload.sh --help)" >&2; exit 2; }

mime_of() {
  case "$(tr '[:upper:]' '[:lower:]' <<<"${1##*.}")" in
    png) echo image/png ;;
    jpg|jpeg) echo image/jpeg ;;
    gif) echo image/gif ;;
    webp) echo image/webp ;;
    svg) echo image/svg+xml ;;
    mov) echo video/quicktime ;;
    mp4) echo video/mp4 ;;
    webm) echo video/webm ;;
    *) return 1 ;;
  esac
}

# Check every file before uploading any, so a typo in the last one leaves nothing half-done.
for f in "${files[@]}"; do
  [[ -f "$f" ]] || { echo "error: no such file: $f" >&2; exit 1; }
  mime_of "$f" >/dev/null || { echo "error: unsupported type: $f (png jpg jpeg gif webp svg mov mp4 webm)" >&2; exit 1; }
done

target="${repo:-"{owner}/{repo}"}"  # gh fills the placeholders from the current repo
repo_id="$(gh api "repos/$target" --jq .id)" \
  || { echo "error: could not look up the repository${repo:+ $repo}" >&2; exit 1; }

for f in "${files[@]}"; do
  name="$(basename "$f")"
  mime="$(mime_of "$f")"
  query="name=$(jq -rn --arg v "$name" '$v|@uri')&content_type=$(jq -rn --arg v "$mime" '$v|@uri')&repository_id=$repo_id"
  url="$(gh api -X POST "https://uploads.github.com/user-attachments/assets?$query" \
    -H "Content-Type: application/octet-stream" --input "$f" --jq .url)" \
    || { echo "error: upload failed: $f" >&2; exit 1; }
  [[ -n "$url" ]] || { echo "error: no URL in the response for $f" >&2; exit 1; }
  if [[ "$mime" == video/* ]]; then echo "$url"; else echo "![${name}](${url})"; fi
done
