#!/usr/bin/env python3
"""Check every owned skill against the rules this repo follows; CI and lefthook run it.

- tooling/authoring_rules.py: the Agent Skills spec and best-practice guides, per skill
- tooling/published_rules.py: the AGENTS.md listing rules (README.md, bucket READMEs,
  plugin.json, a reason for every curated and archived skill)
- tooling/skill_inventory.py: known buckets, unique names, and no curated skill sharing
  a name with an owned one

    scripts/lint-skills.py      exit 1 and list every problem, or print "ok"
"""

import sys

from tooling import authoring_rules, published_rules
from tooling.skill_inventory import REPO, inventory

inv = inventory()
problems = inv.problems + authoring_rules.check(REPO, inv.skills) + published_rules.check(REPO, inv.skills)

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("ok")
