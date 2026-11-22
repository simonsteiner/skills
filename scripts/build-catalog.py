#!/usr/bin/env -S uv run --locked --no-build python3
"""Render the skill catalogs: README.md, each bucket README and plugin.json from the skills,
third-party/README.md from third-party/skills.json.

The lists of skills in those files are generated (tooling/catalog.py has the format), so a
skill is added, moved, renamed or re-described by editing the skill or its skills.json entry
and running this; lefthook runs it on commit, and lint-skills.py fails while it's stale.

    scripts/build-catalog.py          rewrite whatever is out of date, list what changed
    scripts/build-catalog.py --check  list what's out of date and exit 1, change nothing
"""

import sys

from tooling import catalog
from tooling.skill_inventory import REPO, inventory

USAGE = """\
Usage: scripts/build-catalog.py [--check]

  (no args)  rewrite the skill catalogs: README.md, skills/*/README.md and
             .claude-plugin/plugin.json from each SKILL.md, third-party/README.md
             from third-party/skills.json
  --check    report what's out of date and exit 1, without writing"""


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(USAGE)
        return 0
    if argv not in ([], ["--check"]):
        problem = f"expected at most one argument, got: {' '.join(argv)}" if len(argv) > 1 else f"unknown argument '{argv[0]}'"
        print(f"error: {problem}\n{USAGE}", file=sys.stderr)
        return 2

    inv = inventory()
    problems = inv.problems + catalog.problems(inv.skills, REPO)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    if argv:
        found = catalog.stale(inv.skills, REPO)
        print("\n".join(found) or "ok")
        return 1 if found else 0

    for path in catalog.write(inv.skills, REPO):
        print(f"wrote {path.relative_to(REPO).as_posix()}")
    # What render() can't fill: a README.md or plugin.json that's missing or has no block.
    left = catalog.stale(inv.skills, REPO)
    if left:
        print("\n".join(left), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
