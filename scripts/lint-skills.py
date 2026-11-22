#!/usr/bin/env -S uv run --locked --no-build python3
"""Check every owned skill against the rules this repo follows; CI and lefthook run it.

- tooling/authoring_rules.py: the Agent Skills spec and best-practice guides, per skill
  (tooling/script_rules.py: the rules for its bundled scripts)
- tooling/published_rules.py: the AGENTS.md listing rules (the skill catalog that
  build-catalog.py renders is up to date, no unpublished skill in README.md, a reason
  for every curated and archived skill)
- tooling/skill_inventory.py: known buckets, unique names, and no curated skill sharing
  a name with an owned one

    scripts/lint-skills.py                             exit 1 and list every problem, or print "ok"
    uv run --locked --no-build python3 scripts/lint-skills.py   same, explicit uv invocation

uv finds the project from the current directory, so a run from outside the repo (or under a
Python without ruamel.yaml) re-executes itself through `uv run --project <repo>`.
"""

import importlib.util
import os
import sys
from pathlib import Path

if importlib.util.find_spec("ruamel") is None and not os.environ.get("LINT_SKILLS_REEXEC"):
    repo = Path(__file__).resolve().parent.parent
    os.environ["LINT_SKILLS_REEXEC"] = "1"
    cmd = ["uv", "run", "--locked", "--no-build", "--project", str(repo), "python3", str(Path(__file__).resolve())]
    try:
        os.execvp("uv", cmd)  # the script takes no arguments
    except FileNotFoundError:
        sys.exit("lint-skills.py needs ruamel.yaml: install uv, or run it inside the repo's environment")

from tooling import authoring_rules, published_rules
from tooling.skill_inventory import REPO, inventory

inv = inventory()
problems = inv.problems + authoring_rules.check(REPO, inv.skills) + published_rules.check(REPO, inv.skills)

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("ok")
