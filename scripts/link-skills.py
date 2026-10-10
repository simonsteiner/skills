#!/usr/bin/env python3
"""Dev-mode skill linker — the local equivalent of `npx skills add <repo>`.

Links every owned skill outside deprecated/ into ~/.agents/skills and ~/.claude/skills,
so edits in this repo are live without reinstalling; dev_links.py has the layout. Use it
on the machine where you develop the skills; everywhere else, and once a skill is
committed, install the published version with `npx skills add <repo>`. For a given
skill, pick one: dev-link OR skills.sh, not both.

    scripts/link-skills.py          link every owned skill, prune links to removed ones
    scripts/link-skills.py --check  report owned skills that aren't linked, and dead links
"""

import sys
from pathlib import Path

from tooling import dev_links
from tooling.skill_inventory import REPO, inventory
from tooling.third_party import Home

USAGE = """\
Usage: scripts/link-skills.py [--check]

  (no args)  link every owned skill, prune links to skills that are gone
  --check    report owned skills that aren't linked, and dead links"""


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(USAGE)
        return 0
    if argv not in ([], ["--check"]):
        problem = f"expected at most one argument, got: {' '.join(argv)}" if len(argv) > 1 else f"unknown argument '{argv[0]}'"
        print(f"error: {problem}\n{USAGE}", file=sys.stderr)
        return 2

    inv = inventory()
    if inv.problems:
        print("\n".join(inv.problems), file=sys.stderr)
        return 1
    skills = [s for s in inv.skills if s.active]
    home = Home(Path.home())

    if argv:
        found = dev_links.check(skills, home, REPO, sys.argv[0])
        for f in found:
            print(f)
        return 1 if any(f.fails for f in found) else 0

    try:
        dev_links.link(skills, home, REPO)
    except dev_links.LinkError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
