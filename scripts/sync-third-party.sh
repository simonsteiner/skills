#!/usr/bin/env bash
set -euo pipefail

# Installs and upgrades the third-party skills curated in third-party/skills.json.
#
# These skills are NOT part of this repo — nothing is forked, copied, or vendored.
# The manifest records which upstream skills are worth having and why; this script
# hands that list to the skills.sh CLI, which fetches them from their own repos into
# the global store (~/.agents/skills) and wires them into each agent's skill dir.
#
#   ./scripts/sync-third-party.sh          install everything in the manifest, at latest
#   ./scripts/sync-third-party.sh --check  compare the manifest against what's installed
#   ./scripts/sync-third-party.sh --list   print the curated list and the reason for each
#
# `skills add` re-fetches a skill that's already installed, so a plain sync IS the
# upgrade path — there is no separate update step to remember. What that also means:
# **there is no version pinning.** Every sync moves each skill to whatever is on its
# upstream default branch today. If you ever need a reproducible pinned version,
# curation is the wrong tool and you'd have to vendor the skill instead.
#
# Skills this repo owns (skills/**) are installed a different way — with
# `npx skills add simonsteiner/skills`, or scripts/link-skills.sh while developing.
# The two sets must never overlap; the collision guard below enforces that.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO/third-party/skills.json"
LOCK="$HOME/.agents/.skill-lock.json"

usage() {
  cat <<'EOF'
Usage: scripts/sync-third-party.sh [--check | --list]

  (no args)  install every skill in third-party/skills.json, at latest
  --check    compare the manifest against what's actually installed
  --list     print the curated list and the reason for each skill
EOF
}

mode=sync
case "${1-}" in
  "") ;;
  --check) mode=check ;;
  --list) mode=list ;;
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

[ -f "$MANIFEST" ] || {
  echo "error: no manifest at $MANIFEST" >&2
  exit 1
}

# Read the manifest through node (already a hard dependency — the CLI runs under npx).
manifest() { node -e "$1" "$MANIFEST"; }

agents="$(manifest 'process.stdout.write(require(process.argv[1]).agents.join(","))')"
# One line per source: "<repo><TAB><comma-separated skill names>"
sources="$(manifest '
  for (const s of require(process.argv[1]).sources)
    console.log([s.repo, s.skills.map((k) => k.name).join(",")].join("\t"));
')"
# One line per skill: "<name><TAB><repo>"
skills="$(manifest '
  for (const s of require(process.argv[1]).sources)
    for (const k of s.skills) console.log([k.name, s.repo].join("\t"));
')"

# A curated skill and an owned skill would fight over the same name in the global
# store, and whichever synced last would silently win. Refuse instead.
while IFS= read -r -d '' skill_md; do
  own="$(basename "$(dirname "$skill_md")")"
  if awk -F'\t' -v n="$own" '$1 == n { found = 1 } END { exit !found }' <<<"$skills"; then
    echo "error: '$own' is curated in third-party/skills.json but this repo also owns skills/**/$own." >&2
    echo "Rename one of them, or drop it from the manifest — they cannot both be installed." >&2
    exit 1
  fi
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -print0)

case "$mode" in
list)
  manifest '
    for (const s of require(process.argv[1]).sources) {
      console.log(`\n${s.repo} — ${s.why}`);
      for (const k of s.skills) console.log(`  ${k.name.padEnd(30)} ${k.why}`);
    }
  '
  ;;

check)
  # The manifest is the source of truth; report anything installed that drifts from it.
  if [ ! -f "$LOCK" ]; then
    echo "error: no skills.sh lock file at $LOCK — nothing installed yet. Run without --check." >&2
    exit 1
  fi
  status=0
  while IFS=$'\t' read -r name repo; do
    installed="$(node -e '
      const s = require(process.argv[1]).skills[process.argv[2]];
      process.stdout.write(s ? s.source : "");
    ' "$LOCK" "$name")"
    if [ -z "$installed" ]; then
      echo "missing  $name (from $repo)"
      status=1
    elif [ "$installed" != "$repo" ]; then
      echo "conflict $name installed from $installed, manifest says $repo"
      status=1
    else
      echo "ok       $name"
    fi
  done <<<"$skills"

  # Global skills installed from a remote source but absent from the manifest: either
  # curate them deliberately or remove them with `npx skills remove -g`.
  node -e '
    const lock = require(process.argv[1]).skills;
    const curated = new Set(process.argv[2].split("\n").filter(Boolean).map((l) => l.split("\t")[0]));
    for (const [name, s] of Object.entries(lock))
      if (s.source && s.sourceType === "github" && !curated.has(name))
        console.log(`uncurated ${name} (installed from ${s.source})`);
  ' "$LOCK" "$skills"
  exit "$status"
  ;;

sync)
  while IFS=$'\t' read -r repo names; do
    echo "==> $repo: $names"
    npx --yes skills@latest add "$repo" --global --yes --agent "$agents" --skill "$names"
  done <<<"$sources"
  echo
  echo "Synced. Verify with: $0 --check"
  ;;
esac
