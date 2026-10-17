#!/usr/bin/env bash
set -euo pipefail

# Download GitHub attachments (screenshots, recordings, files) so they can be
# opened locally. Works on private repos: requests go through `gh api`.
#
#   download.sh [-o DIR] <url>...      the given attachment URLs
#   ... | download.sh [-o DIR]         every attachment URL found in the text on stdin
#
# Saves into DIR (default: a new temp folder) as NN-<name>, adding an extension
# from the file's type when the URL has none, and prints "<path><TAB><url>" per
# file in order. Only GitHub attachment URLs are fetched (user-attachments/assets,
# user-attachments/files, <owner>/<repo>/assets, user-images.githubusercontent.com),
# so the gh token never goes anywhere else. A failed download doesn't stop the rest.
# Exits 1 when any download failed or a URL isn't an attachment, 2 on bad usage.

ATTACHMENT='https://(github\.com/user-attachments/(assets|files)/[^][()<>"'"'"'[:space:]]+|github\.com/[[:alnum:]_.-]+/[[:alnum:]_.-]+/assets/[0-9]+/[[:alnum:]-]+|user-images\.githubusercontent\.com/[^][()<>"'"'"'[:space:]]+)'

dir=
urls=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) sed -n '/^# [A-Z]/,/^$/{/^$/q;s/^# \{0,1\}//p;}' "$0"; exit 0 ;;  # the comment above
    -o) [[ $# -ge 2 ]] || { echo "error: -o needs a folder" >&2; exit 2; }; dir="$2"; shift ;;
    -*) echo "error: unknown option $1" >&2; exit 2 ;;
    *) urls+=("$1") ;;
  esac
  shift
done

if [[ ${#urls[@]} -eq 0 ]]; then
  [[ ! -t 0 ]] || { echo "error: no URLs given and nothing on stdin (download.sh --help)" >&2; exit 2; }
  while IFS= read -r u; do urls+=("$u"); done < <(grep -oE "$ATTACHMENT" | sed -E 's/[.,;:!?]+$//' | awk '!seen[$0]++')
  [[ ${#urls[@]} -gt 0 ]] || { echo "no attachment URLs in the input" >&2; exit 0; }
fi
for u in "${urls[@]}"; do
  [[ "$u" =~ ^${ATTACHMENT}$ ]] || { echo "error: not a GitHub attachment URL: $u" >&2; exit 1; }
done

if [[ -n "$dir" ]]; then mkdir -p "$dir"; else dir="$(mktemp -d "${TMPDIR:-/tmp}/gh-media.XXXXXX")"; fi

ext_of() {
  command -v file >/dev/null || return 0
  case "$(file -b --mime-type "$1")" in
    image/png) echo png ;; image/jpeg) echo jpg ;; image/gif) echo gif ;; image/webp) echo webp ;;
    image/svg+xml) echo svg ;; video/mp4) echo mp4 ;; video/quicktime) echo mov ;; video/webm) echo webm ;;
    application/pdf) echo pdf ;; application/zip) echo zip ;; text/plain) echo txt ;;
  esac
}

failed=0
n=0
for u in "${urls[@]}"; do
  n=$((n + 1))
  name="${u%%\?*}"; name="${name##*/}"
  path="$(printf '%s/%02d-%s' "$dir" "$n" "$name")"
  if ! gh api "$u" >"$path"; then
    rm -f "$path"; echo "error: download failed: $u" >&2; failed=1; continue
  fi
  if [[ "$name" != *.* ]] && ext="$(ext_of "$path")" && [[ -n "$ext" ]]; then
    mv "$path" "$path.$ext"; path="$path.$ext"
  fi
  printf '%s\t%s\n' "$path" "$u"
done
exit "$failed"
