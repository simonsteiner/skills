#!/usr/bin/env python3
"""Install and upgrade the third-party skills curated in third-party/skills.json.

These skills are NOT part of this repo — nothing is forked, copied, or vendored. The
manifest records which upstream skills are worth having and why; this script hands that
list to the skills.sh CLI, which fetches them from their own repos into the global store
(~/.agents/skills) and wires them into each agent's skill dir.

    scripts/sync-third-party.py          install everything in the manifest, at latest
    scripts/sync-third-party.py --check  compare the manifest against what's installed
    scripts/sync-third-party.py --list   print the curated list and the reason for each

`skills add` re-fetches a skill that's already installed, so a plain sync IS the upgrade
path — there is no separate update step to remember. What that also means: **there is no
version pinning.** Every sync moves each skill to whatever is on its upstream default
branch today. If you ever need a reproducible pinned version, curation is the wrong tool
and you'd have to vendor the skill instead.

Run this from a plain terminal, not from inside a coding-agent session. The CLI detects
the agent it's running under and installs non-interactively to that agent alone, so a
sync started inside Claude Code updates the store and Claude Code and silently leaves
every other agent in the manifest on its old copy.

Skills this repo owns (skills/**) are installed a different way — with
`npx skills add simonsteiner/skills`, or scripts/link-skills.py while developing. The two
sets must never overlap; scripts/tooling/skill_inventory.py enforces that.
"""

import sys
from pathlib import Path

from tooling import third_party
from tooling.skill_inventory import inventory

USAGE = """\
Usage: scripts/sync-third-party.py [--check | --list]

  (no args)  install every skill in third-party/skills.json, at latest, then link
             universal agents; a failing source doesn't stop the rest
  --check    compare the manifest against what's actually installed; exits 1 on
             missing, conflict, archived and drift, and only reports uncurated,
             unmanaged and note
  --list     print the curated list and the reason for each skill"""


def main(argv):
    modes = {(): "sync", ("--check",): "check", ("--list",): "list"}
    if tuple(argv) in (("-h",), ("--help",)):
        print(USAGE)
        return 0
    if tuple(argv) not in modes:
        problem = f"expected at most one argument, got: {' '.join(argv)}" if len(argv) > 1 else f"unknown argument '{argv[0]}'"
        print(f"error: {problem}\n{USAGE}", file=sys.stderr)
        return 2
    mode = modes[tuple(argv)]

    manifest = third_party.load()
    if manifest is None:
        print(f"error: no manifest at {third_party.REPO / 'third-party/skills.json'}", file=sys.stderr)
        return 1
    inv = inventory()
    if inv.problems:
        print("\n".join(inv.problems), file=sys.stderr)
        print("error: the owned skills are unusable as they stand; fix the problems above first.", file=sys.stderr)
        return 1
    home = third_party.Home(Path.home())
    # With no --agent the CLI would pick agents itself, and no universal links get made.
    agentless = [s.repo for s in manifest.sources if s.skills and not s.agents]
    if agentless and mode != "list":
        print(f"error: no agents for {', '.join(agentless)} — set `agents` on the source or at the top level "
              "of third-party/skills.json", file=sys.stderr)
        return 1

    if mode == "list":
        print("\n".join(third_party.listing(manifest)))
        return 0

    if mode == "check":
        if not home.lock.exists():
            print(f"error: no skills.sh lock file at {home.lock} — nothing installed yet. Run without --check.",
                  file=sys.stderr)
            return 1
        findings = third_party.check(manifest, home, [s.name for s in inv.skills])
        for f in findings:
            print(f)
        return 1 if any(f.fails for f in findings) else 0

    failed = third_party.sync(manifest, home)
    print()
    if failed:
        print("Failed:\n" + "\n".join(f"  {f}" for f in failed), file=sys.stderr)
        return 1
    print(f"Synced. Verify with: {sys.argv[0]} --check")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
