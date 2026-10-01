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
#
#   ./scripts/link-skills.sh          link every owned skill, prune links to removed ones
#   ./scripts/link-skills.sh --check  report owned skills that aren't linked, and dead links

REPO="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_STORE="$HOME/.agents/skills"
CLAUDE_DIR="$HOME/.claude/skills"

usage() {
  cat <<'EOF'
Usage: scripts/link-skills.sh [--check]

  (no args)  link every owned skill, prune links to skills that are gone
  --check    report owned skills that aren't linked, and dead links
EOF
}

mode="link"
case "${1-}" in
  "") ;;
  --check) mode=check ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    echo "error: unknown argument '$1'" >&2
    usage >&2
    exit 2
    ;;
esac

# Every owned skill directory: each SKILL.md outside deprecated/.
owned_skills() {
  find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0 |
    xargs -0 -n1 dirname
}

# Store links into this repo whose skill is gone — deleted, renamed, or moved to
# deprecated/. Linking only ever adds, so these would otherwise linger.
dead_links() {
  local link target
  for link in "$AGENTS_STORE"/*; do
    [ -L "$link" ] || continue
    target="$(readlink "$link")"
    case "$target" in
      "$REPO"/skills/*) [ -f "$target/SKILL.md" ] && [[ "$target" != */deprecated/* ]] || echo "$link" ;;
    esac
  done
}

if [ "$mode" = check ]; then
  status=0
  while IFS= read -r src; do
    name="$(basename "$src")"
    if [ "$(readlink -f "$CLAUDE_DIR/$name" 2>/dev/null)" = "$src" ]; then
      echo "ok        $name"
    else
      echo "missing   $name (not linked into $CLAUDE_DIR — run $0)"
      status=1
    fi
  done < <(owned_skills)
  while IFS= read -r link; do
    echo "dead      $(basename "$link") ($link -> $(readlink "$link") — run $0)"
    status=1
  done < <(dead_links)
  exit "$status"
fi

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

while IFS= read -r src; do
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
done < <(owned_skills)

while IFS= read -r link; do
  name="$(basename "$link")"
  rm "$link"
  # Only remove Claude Code's entry if it's the relative link into the store.
  if [ "$(readlink "$CLAUDE_DIR/$name" 2>/dev/null)" = "../../.agents/skills/$name" ]; then
    rm "$CLAUDE_DIR/$name"
  fi
  echo "pruned $name"
done < <(dead_links)
