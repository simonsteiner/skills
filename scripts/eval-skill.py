#!/usr/bin/env python3
"""Run one iteration of a skill's evals, or of every skill's trigger evals.

The runs, the grading and the routing are agent work: each task.md and grade.md is meant
for a fresh sub-agent, so no run inherits this session's context. docs/evals.md has the
loop; tooling/evals.py and tooling/triggers.py have the workspace layouts.

    scripts/eval-skill.py prepare <skill> [--baseline <git-ref>]
        lay out .eval-workspace/<skill>/iteration-<N>/ and print one JSON line per run:
        {"eval", "config", "task", "grade", "timing"}, "timing" being where to record the
        run's tokens and time. Without --baseline the baseline is no skill;
        with it, the skill as it was at that ref (old_skill).
    scripts/eval-skill.py benchmark <iteration-dir>
        write benchmark.json from every run's grading.json and timing.json and print it
    scripts/eval-skill.py triggers [--baseline <git-ref>] [--also <skills-dir>]...
        lay out .eval-workspace/_triggers/iteration-<N>/ from every skill's
        evals/triggers.json and print one JSON line per router task: {"config", "task",
        "model"}, where "model" is the model to spawn that router on.
        with_skill routes against the descriptions in the working tree; --baseline adds
        old_skill, the descriptions at that ref. --also adds the model-invoked skills in
        another directory (e.g. ~/.agents/skills) to both catalogues as neighbours.
        Reads frontmatter, so run it through `uv run --locked --no-build python3`.
    scripts/eval-skill.py triggers-score <iteration-dir>
        write trigger-benchmark.json from every router's answers.json and print it

Exit 1 on an unknown skill, invalid evals.json or triggers.json, a bad ref, or runs not
graded or answered yet; 2 on bad usage.
"""

import json
import sys
from pathlib import Path

from tooling import evals, triggers
from tooling.skill_inventory import REPO, inventory

USAGE = """\
Usage: scripts/eval-skill.py prepare <skill> [--baseline <git-ref>]
       scripts/eval-skill.py benchmark <iteration-dir>
       scripts/eval-skill.py triggers [--baseline <git-ref>] [--also <skills-dir>]...
       scripts/eval-skill.py triggers-score <iteration-dir>"""


def main(argv):
    if argv in ([], ["-h"], ["--help"]):
        print(__doc__.strip() if argv else USAGE, file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    try:
        code = _run(argv[0], argv[1:])
    except (ValueError, RuntimeError) as e:  # RuntimeError: ruamel.yaml missing outside uv
        print(f"error: {e}", file=sys.stderr)
        return 1
    if code is None:
        print(USAGE, file=sys.stderr)
        return 2
    return code


def _run(cmd, args):
    """Run one subcommand; None when `cmd` and `args` aren't a valid call."""
    if cmd == "prepare" and len(args) in (1, 3) and (len(args) == 1 or args[1] == "--baseline"):
        return prepare(args[0], args[2] if len(args) == 3 else None)
    if cmd == "triggers" and (opts := _options(args, {"--baseline", "--also"})) is not None:
        return prepare_triggers(opts.get("--baseline", [None])[-1], opts.get("--also", []))
    scorers = {"benchmark": evals.benchmark, "triggers-score": triggers.score}
    if cmd in scorers and len(args) == 1:
        print(json.dumps(scorers[cmd](Path(args[0])), indent=2))
        return 0
    return None


def _options(args, names):
    """`args` as {flag: [values]} when it's only `names` flags each followed by a value, else None."""
    if len(args) % 2 or any(flag not in names for flag in args[::2]):
        return None
    opts = {}
    for flag, value in zip(args[::2], args[1::2]):
        opts.setdefault(flag, []).append(value)
    return opts if len(opts.get("--baseline", [])) <= 1 else None


def prepare_triggers(baseline, also):
    """Lay out the next trigger iteration and print one JSON line per router task."""
    iteration, tasks = triggers.prepare(REPO, inventory().skills, baseline=baseline, also=also)
    for config, task in tasks:
        print(json.dumps(triggers.task_line(config, task)))
    print(f"prepared {iteration}", file=sys.stderr)
    return 0


def prepare(skill, baseline):
    """Lay out the next iteration of `skill`'s evals and print one JSON line per run."""
    skills = {s.name: s for s in inventory().skills}
    if skill not in skills:
        print(f"error: no owned skill {skill!r}; known: {', '.join(sorted(skills))}", file=sys.stderr)
        return 1
    iteration, runs = evals.prepare(REPO, skills[skill], baseline=baseline)
    for name, config, task in runs:
        print(json.dumps({"eval": name, "config": config, "task": str(task),
                          "grade": str(task.with_name("grade.md")), "timing": str(task.with_name("timing.json"))}))
    print(f"prepared {iteration}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
