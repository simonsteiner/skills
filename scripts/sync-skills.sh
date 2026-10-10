#!/usr/bin/env bash
set -euo pipefail

# Dev-machine convenience: link the owned skills, then sync the curated third-party
# ones. Run it after pulling, and after adding, moving or removing a skill. All the
# work happens in the two scripts it calls; --check is passed through to both.
#
#   ./scripts/sync-skills.sh          scripts/link-skills.sh, then scripts/sync-third-party.py
#   ./scripts/sync-skills.sh --check  both scripts' --check
#
# Only for the machine where you develop the skills — everywhere else, owned skills
# come from `npx skills add` and only sync-third-party.py applies. Run it from a plain
# terminal, and restart your agents afterwards: they read their skill list at startup.

REPO="$(cd "$(dirname "$0")/.." && pwd)"

case "${1-}" in
  "" | --check) ;;
  *)
    echo "Usage: scripts/sync-skills.sh [--check]" >&2
    exit 2
    ;;
esac

status=0
echo "==> owned skills"
"$REPO/scripts/link-skills.sh" "$@" || status=1
echo
echo "==> third-party skills"
"$REPO/scripts/sync-third-party.py" "$@" || status=1
exit "$status"
