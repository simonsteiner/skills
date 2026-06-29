#!/usr/bin/env bash
set -euo pipefail

# Dev-mode skill linker — the local equivalent of `npx skills add <repo>`, for when
# you're actively developing skills in THIS repo and want live edits without
# reinstalling after every change.
#
# It mirrors the layout skills.sh produces, so a dev link and a skills.sh install
# are interchangeable (never additive — you won't get a skill linked twice):
#
#   ~/.agents/skills/<name>            canonical store. skills.sh copies skills here;
#                                      this script symlinks them straight to the repo
#                                      so edits are live.
#   ~/.claude/skills/<name>            per-agent entry for Claude Code, a relative
#     -> ../../.agents/skills/<name>   symlink into the store — exactly as skills.sh
#                                      creates it.
#
# Use this on the machine where you develop the skills. Everywhere else — and once a
# skill is committed — install the published version with `npx skills add <repo>`.
# For a given skill, pick one: dev-link OR skills.sh, not both.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_STORE="$HOME/.agents/skills"
CLAUDE_DIR="$HOME/.claude/skills"

# If a destination is itself a symlink that resolves into this repo, the per-skill
# links would be written back into the working copy. Detect and bail.
for d in "$AGENTS_STORE" "$CLAUDE_DIR"; do
  if [ -L "$d" ]; then
    resolved="$(readlink -f "$d")"
    case "$resolved" in
      "$REPO" | "$REPO"/*)
        echo "error: $d is a symlink into this repo ($resolved)." >&2
        echo "Remove it (rm \"$d\") and re-run; the script will recreate it as a real dir." >&2
        exit 1
        ;;
    esac
  fi
done

mkdir -p "$AGENTS_STORE" "$CLAUDE_DIR"

while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"

  # Canonical store entry -> live symlink into the repo. Replace a real dir left by
  # a prior `npx skills add` so the dev link takes over.
  store="$AGENTS_STORE/$name"
  if [ -e "$store" ] && [ ! -L "$store" ]; then
    rm -rf "$store"
  fi
  ln -sfn "$src" "$store"

  # Per-agent entry for Claude Code: relative symlink into the store, like skills.sh.
  claude="$CLAUDE_DIR/$name"
  if [ -e "$claude" ] && [ ! -L "$claude" ]; then
    rm -rf "$claude"
  fi
  ln -sfn "../../.agents/skills/$name" "$claude"

  echo "dev-linked $name -> $src"
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0)
