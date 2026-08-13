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
# Run this from a plain terminal, not from inside a coding-agent session. The CLI
# detects the agent it's running under and installs non-interactively to that agent
# alone, so a sync started inside Claude Code updates the store and Claude Code and
# silently leaves every other agent in the manifest on its old copy.
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

# One line per source: "<repo><TAB><skill names><TAB><agents>". A source may override
# the top-level agent list — curate a skill only into the agents that should carry it.
sources="$(manifest '
  const m = require(process.argv[1]);
  for (const s of m.sources)
    console.log([s.repo, s.skills.map((k) => k.name).join(","), (s.agents ?? m.agents).join(",")].join("\t"));
')"
# One line per skill: "<name><TAB><repo>"
skills="$(manifest '
  for (const s of require(process.argv[1]).sources)
    for (const k of s.skills) console.log([k.name, s.repo].join("\t"));
')"

# The store the CLI installs into, and the per-agent directories it wires up. Used only
# to report drift — installs go through the CLI, which owns the real agent-to-path map,
# so an agent missing from this list just goes unreported, never uninstalled.
STORE="$HOME/.agents/skills"
AGENT_DIRS=(
  "$HOME/.claude/skills"             # claude-code
  "$HOME/.copilot/skills"            # github-copilot
  "$HOME/.gemini/skills"             # gemini-cli
  "$HOME/.gemini/antigravity/skills" # antigravity
)

# A curated skill and an owned skill would fight over the same name in the global
# store, and whichever synced last would silently win. Refuse instead.
owned=""
while IFS= read -r -d '' skill_md; do
  own="$(basename "$(dirname "$skill_md")")"
  owned="${owned:+$owned,}$own"
  if awk -F'\t' -v n="$own" '$1 == n { found = 1 } END { exit !found }' <<<"$skills"; then
    echo "error: '$own' is curated in third-party/skills.json but this repo also owns skills/**/$own." >&2
    echo "Rename one of them, or drop it from the manifest — they cannot both be installed." >&2
    exit 1
  fi
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -print0)

case "$mode" in
list)
  # shellcheck disable=SC2016  # ${...} here is a JS template literal — the shell must not expand it
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
  # shellcheck disable=SC2016  # ${...} here is a JS template literal — the shell must not expand it
  node -e '
    const lock = require(process.argv[1]).skills;
    const curated = new Set(process.argv[2].split("\n").filter(Boolean).map((l) => l.split("\t")[0]));
    for (const [name, s] of Object.entries(lock))
      if (s.source && s.sourceType === "github" && !curated.has(name))
        console.log(`uncurated ${name} (installed from ${s.source})`);
  ' "$LOCK" "$skills"

  # Skills sitting in an agent's directory that nothing manages: absent from the lock
  # file, uncurated, and not owned here. That's how another channel's install shows up
  # — a Claude Code plugin marketplace, or a hand copy — as a frozen snapshot with no
  # upgrade path. See docs/adr/0003.
  # shellcheck disable=SC2016  # ${...} here is a JS template literal — the shell must not expand it
  node -e '
    const fs = require("fs");
    const [lockPath, curatedTsv, ownedCsv, store, ...dirs] = process.argv.slice(1);
    const curated = curatedTsv.split("\n").filter(Boolean).map((l) => l.split("\t")[0]);
    const known = new Set([
      ...Object.keys(require(lockPath).skills),
      ...curated,
      ...ownedCsv.split(",").filter(Boolean),
    ]);
    const skillMd = (dir, name) => `${dir}/${name}/SKILL.md`;

    const unmanaged = new Map();
    for (const dir of [store, ...dirs]) {
      if (!fs.existsSync(dir)) continue;
      for (const name of fs.readdirSync(dir)) {
        if (known.has(name) || !fs.existsSync(skillMd(dir, name))) continue;
        if (!unmanaged.has(name)) unmanaged.set(name, []);
        unmanaged.get(name).push(dir);
      }
    }
    for (const [name, where] of unmanaged)
      console.log(`unmanaged ${name} (in ${where.length}: ${where.join(", ")})`);

    // A curated skill can hold different content in two places at once: the CLI wires
    // some agents up with a symlink into the store and others with a copy, and it does
    // not always refresh both. Either side can be the old one, so report the drift and
    // name the older file rather than assuming the store is the truth.
    for (const dir of dirs) {
      for (const name of curated) {
        const [there, here] = [skillMd(dir, name), skillMd(store, name)];
        if (!fs.existsSync(there) || !fs.existsSync(here)) continue;
        if (fs.readFileSync(there, "utf8") === fs.readFileSync(here, "utf8")) continue;
        const older = fs.statSync(there).mtimeMs < fs.statSync(here).mtimeMs ? there : here;
        console.log(`drift     ${name} (${dir} vs the store — older copy: ${older})`);
      }
    }
  ' "$LOCK" "$skills" "$owned" "$STORE" "${AGENT_DIRS[@]}"
  exit "$status"
  ;;

sync)
  while IFS=$'\t' read -r repo names srcagents; do
    echo "==> $repo: $names"
    # One --skill / --agent flag per value. The CLI reads a comma-separated list as a
    # single name and fails the whole install with "No matching skills found".
    flags=()
    IFS=, read -ra parts <<<"$names"
    for p in "${parts[@]}"; do flags+=(--skill "$p"); done
    IFS=, read -ra parts <<<"$srcagents"
    for p in "${parts[@]}"; do flags+=(--agent "$p"); done
    # </dev/null or the CLI drains the loop's stdin and every source after the first
    # is silently skipped.
    npx --yes skills@latest add "$repo" --global --yes "${flags[@]}" </dev/null
  done <<<"$sources"
  echo
  echo "Synced. Verify with: $0 --check"
  ;;
esac
