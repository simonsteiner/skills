#!/usr/bin/env python3
"""Run one iteration of a skill's evals: prepare the runs, then aggregate their grades.

The runs and the grading are agent work: each task.md and grade.md is meant for a fresh
sub-agent, so no run inherits this session's context. docs/evals.md has the loop;
tooling/evals.py has the workspace layout.

    scripts/eval-skill.py prepare <skill> [--baseline <git-ref>]
        lay out .eval-workspace/<skill>/iteration-<N>/ and print one JSON line per run:
        {"eval", "config", "task", "grade"}. Without --baseline the baseline is no skill;
        with it, the skill as it was at that ref (old_skill).
    scripts/eval-skill.py benchmark <iteration-dir>
        write benchmark.json from every run's grading.json and timing.json and print it

Exit 1 on an unknown skill, invalid evals.json, a bad ref, or runs not graded yet;
2 on bad usage.
"""

import json
import sys
from pathlib import Path

from tooling import evals
from tooling.skill_inventory import REPO, inventory

USAGE = """\
Usage: scripts/eval-skill.py prepare <skill> [--baseline <git-ref>]
       scripts/eval-skill.py benchmark <iteration-dir>"""


def main(argv):
    if argv in ([], ["-h"], ["--help"]):
        print(__doc__.strip() if argv else USAGE, file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    cmd, args = argv[0], argv[1:]
    try:
        if cmd == "prepare" and len(args) in (1, 3) and (len(args) == 1 or args[1] == "--baseline"):
            skills = {s.name: s for s in inventory().skills}
            if args[0] not in skills:
                print(f"error: no owned skill {args[0]!r}; known: {', '.join(sorted(skills))}", file=sys.stderr)
                return 1
            iteration, runs = evals.prepare(REPO, skills[args[0]], baseline=args[2] if len(args) == 3 else None)
            for name, config, task in runs:
                print(json.dumps({"eval": name, "config": config, "task": str(task),
                                  "grade": str(task.with_name("grade.md"))}))
            print(f"prepared {iteration}", file=sys.stderr)
            return 0
        if cmd == "benchmark" and len(args) == 1:
            print(json.dumps(evals.benchmark(Path(args[0])), indent=2))
            return 0
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
