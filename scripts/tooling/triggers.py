"""Trigger evals: does each model-invoked skill's description load it on the prompts meant for it,
and stay quiet on its neighbours'?

evals/evals.json tests what a skill does once loaded. Whether it loads at all is decided by
its `description`, which the harness puts in front of the model beside every other skill's.
A trigger eval puts the same catalogue in front of a fresh router agent and asks which skills
it would load for each prompt; the prompts and their labels come from each skill's
evals/triggers.json:

    {"skills": ["<name>"], "triggers": [{"query": "<prompt>", "should_trigger": true}, ...]}

A `should_trigger: false` prompt is a near miss: one meant for a neighbour, or one that
shares the skill's words but not its job. The same prompt may carry labels from several
skills. Only model-invoked skills get a triggers.json: a user-invoked one never reaches the
model's catalogue.

One iteration, like evals.py's, lays out tasks for agents and aggregates what they write:

    .eval-workspace/_triggers/iteration-<N>/
      cases.json                    every prompt with its labels; never shown to a router
      <config>/                     with_skill (descriptions in the working tree), and old_skill
                                    (the descriptions at --baseline <ref>)
        catalogue.json              [{"name", "description"}], what the router sees
        batch-<k>/task.md           the router's brief: the catalogue and up to BATCH prompts
        batch-<k>/answers.json      {"<id>": ["<skill>", ...]}, written by the router
      trigger-benchmark.json        written by score()

Both configs see the same prompts, in the same order and batches, so the delta is the
descriptions'. scripts/eval-skill.py is the command line; tests/tooling/test_triggers.py
tests it.
"""

import json
import random
import subprocess
from pathlib import Path

from . import skill_inventory

WORKSPACE = ".eval-workspace"
FOLDER = "_triggers"  # not a valid skill name, so it can't collide with a skill's own folder
FILE = "evals/triggers.json"
BATCH = 15
CATALOGUE = "catalogue.json"
SEED = 0  # a fixed shuffle: reruns and both configs see the same order
# The model each router runs on: on the 70-prompt set Haiku routed as well as Opus, missing only
# prompts Sonnet or Opus missed too. docs/evals.md, "Cost", has the role table.
ROUTER_MODEL = "haiku"


def problems(skill):
    """What's wrong with a skill's evals/triggers.json, if it has one."""
    path = skill.folder / FILE
    if not path.exists():
        return []
    if not skill.model_invoked:
        return ["triggers.json on a user-invoked skill: its description never reaches the model, so nothing triggers it"]
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"triggers.json isn't valid JSON: {e}"]
    if not isinstance(data, dict):
        return ['triggers.json must be an object with "skills" and "triggers"']
    out = []
    if not isinstance(data.get("skills"), list) or skill.name not in data["skills"]:
        out.append(f'"skills" doesn\'t list {skill.name!r}')
    cases = data.get("triggers")
    if not isinstance(cases, list) or not cases:
        return out + ['"triggers" must be a non-empty list']
    out += _case_problems(cases)
    labels = {c.get("should_trigger") for c in cases if isinstance(c, dict)}
    if not out and labels != {True, False}:
        out.append("triggers.json needs both should_trigger true and false cases: a skill that fires on everything passes the first kind alone")
    return out


def _case_problems(cases):
    """What's wrong with the entries of "triggers": a missing query or label, or a repeated query."""
    out, seen = [], set()
    for i, case in enumerate(cases, 1):
        if not isinstance(case, dict) or not isinstance(case.get("query"), str) or not case["query"].strip():
            out.append(f'trigger {i} needs a non-empty "query"')
            continue
        if not isinstance(case.get("should_trigger"), bool):
            out.append(f'trigger {i} needs "should_trigger" as true or false')
        if case["query"] in seen:
            out.append(f"trigger {i} repeats an earlier query")
        seen.add(case["query"])
    return out


def cases(skills):
    """[{"id", "query", "labels": {skill: bool}}] across every skill's triggers.json, shuffled with SEED."""
    by_query = {}
    for skill in skills:
        path = skill.folder / FILE
        if not path.exists():
            continue
        for case in json.loads(path.read_text())["triggers"]:
            by_query.setdefault(case["query"], {})[skill.name] = case["should_trigger"]
    queries = sorted(by_query)
    random.Random(SEED).shuffle(queries)
    return [{"id": str(i), "query": q, "labels": by_query[q]} for i, q in enumerate(queries, 1)]


def _entry(name, text):
    """(name, description) when `text` is a model-invoked SKILL.md with a string description, else None."""
    fields, _, error = skill_inventory.frontmatter(text)
    if error or not fields or fields.get("disable-model-invocation") is True:
        return None
    desc = fields.get("description")
    return (name, " ".join(desc.split())) if isinstance(desc, str) else None


def catalogue(repo, ref=None, also=()):
    """[{"name", "description"}] for the model-invoked published skills, in the working tree or at git `ref`.

    `also` adds the model-invoked skills in each other directory (<dir>/<name>/SKILL.md, e.g. the
    installed curated skills) that the owned set doesn't already name, so neighbours outside
    the repo compete too. At a `ref`, `also` never supplies a skill owned in the working tree: an
    installed copy carries its working-tree description, not the ref's, so a skill added since
    the ref stays out of that catalogue.
    """
    owned_now = set()
    if ref is None:
        found = [(s.name, s.skill_md.read_text()) for s in skill_inventory.inventory(repo).skills if s.published]
    else:
        owned_now = {s.name for s in skill_inventory.inventory(repo).skills}
        if ref.startswith("-"):  # git would read it as an option
            raise ValueError(f"not a git ref: {ref!r}")
        found = [(rel.split("/")[2], _git(repo, "show", f"{ref}:{rel}"))
                 for rel in _git(repo, "ls-tree", "-r", "--name-only", ref, "--", "skills").splitlines()
                 if len(rel.split("/")) == 4 and rel.endswith("/SKILL.md")
                 and rel.split("/")[1] in skill_inventory.PUBLISHED]
    for folder in also:
        path = Path(folder).expanduser()
        if not path.is_dir():  # a typo would otherwise drop every neighbour without a word
            raise ValueError(f"--also: not a directory: {folder}")
        found += [(f.parent.name, f.read_text()) for f in sorted(path.glob("*/SKILL.md"))
                  if f.parent.name not in owned_now]
    entries, seen = {}, set()
    for name, text in found:  # owned skills first: an installed copy of one, even a user-invoked one, never stands in
        if name not in seen and (entry := _entry(name, text)):
            entries[name] = entry[1]
        seen.add(name)
    return [{"name": n, "description": d} for n, d in sorted(entries.items())]


def _git(repo, *args):
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if run.returncode != 0:
        raise ValueError(f"git {' '.join(args)}: {run.stderr.strip()}")
    return run.stdout


TASK = """\
Route user messages to skills, in a fresh context, the way a coding agent decides which skills
to load at the start of a turn.

The session has these skills. The harness shows you only each one's name and description; a
skill is loaded by calling the Skill tool with its name.

{catalogue}

For each message below, list every skill you would load before acting on it (none, one or
several) as the agent in a real session with exactly these skills would. A skill whose
description says to use it for this kind of request should be loaded even when you could do the
work unaided. Judge each message on its own: they come from different sessions, in a repo with
uncommitted work, and nothing else was said before it.

{messages}

Write {answers} as a JSON object mapping each message number to the skill names you would load,
e.g. {{"1": ["skill-a"], "2": []}}. Read no other file and write nothing else.
"""


def prepare(repo, skills, baseline=None, also=(), root=None):
    """Lay out the next trigger iteration; return (iteration dir, [(config, task.md)])."""
    found = [f"{s.name}: {p}" for s in skills for p in problems(s)]
    if found:
        raise ValueError("; ".join(found))
    all_cases = cases(skills)
    if not all_cases:
        raise ValueError(f"no skill has an {FILE}")
    configs = {"with_skill": catalogue(repo, also=also)}
    if baseline:
        configs["old_skill"] = catalogue(repo, baseline, also=also)

    base = (root or repo / WORKSPACE) / FOLDER
    n = 1 + max((int(p.name.split("-")[1]) for p in base.glob("iteration-*") if p.name.split("-")[1].isdigit()), default=0)
    iteration = base / f"iteration-{n}"
    iteration.mkdir(parents=True)
    (iteration / "cases.json").write_text(json.dumps(all_cases, indent=2) + "\n")

    tasks = []
    for config, entries in configs.items():
        (iteration / config).mkdir()
        (iteration / config / CATALOGUE).write_text(json.dumps(entries, indent=2) + "\n")
        listing = "\n".join(f"- **{e['name']}**: {e['description']}" for e in entries)
        for k in range(0, len(all_cases), BATCH):
            batch = iteration / config / f"batch-{k // BATCH + 1}"
            batch.mkdir()
            messages = "\n".join(f"{c['id']}. {json.dumps(c['query'], ensure_ascii=False)}" for c in all_cases[k:k + BATCH])
            (batch / "task.md").write_text(TASK.format(catalogue=listing, messages=messages, answers=batch / "answers.json"))
            tasks.append((config, batch / "task.md"))
    return iteration, tasks


def task_line(config, task):
    """The JSON line printed for one router task; the coordinating agent spawns the router on its "model"."""
    return {"config": config, "task": str(task), "model": ROUTER_MODEL}


def _answers(config_dir, iteration):
    """Every batch's answers.json merged into {id: set(skills)}; ValueError names a missing or bad one."""
    merged, missing = {}, []
    for batch in sorted(config_dir.glob("batch-*")):
        path = batch / "answers.json"
        where = path.relative_to(iteration)
        if not path.exists():
            missing.append(str(where))
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"{where} isn't valid JSON: {e}") from None
        if not isinstance(data, dict) or not all(isinstance(v, list) and all(isinstance(x, str) for x in v)
                                                 for v in data.values()):
            raise ValueError(f"{where} must map message numbers to lists of skill names")
        merged.update({str(k): set(v) for k, v in data.items()})
    if missing:
        raise ValueError("not answered yet: " + ", ".join(missing))
    return merged


def _score_config(config_dir, iteration, all_cases):
    """One config's pass rate, per-skill counts, absent skills and misses."""
    answers = _answers(config_dir, iteration)
    listed = {e["name"] for e in json.loads((config_dir / CATALOGUE).read_text())}
    per_skill, misses = {}, []
    for case in all_cases:
        picked = answers.get(case["id"], set())
        for skill, should in sorted(case["labels"].items()):
            row = per_skill.setdefault(skill, {"should_trigger": [0, 0], "should_not_trigger": [0, 0]})
            cell = row["should_trigger" if should else "should_not_trigger"]
            ok = (skill in picked) == should
            cell[0] += ok
            cell[1] += 1
            if not ok:
                misses.append({"query": case["query"], "skill": skill, "should_trigger": should, "loaded": sorted(picked)})
    passed = sum(c[0] for r in per_skill.values() for c in r.values())
    total = sum(c[1] for r in per_skill.values() for c in r.values())
    return {
        "pass_rate": round(passed / total, 4) if total else 0.0,
        "passed": passed, "total": total,
        "per_skill": {s: {k: f"{c[0]}/{c[1]}" for k, c in r.items()} for s, r in per_skill.items()},
        "absent": sorted(s for s in per_skill if s not in listed),
        "misses": misses,
    }


def score(iteration):
    """Score every config's answers against cases.json; write and return trigger-benchmark.json.

    A prompt with no answer counts as loading nothing. A skill missing from a config's
    catalogue (new since the baseline, or user-invoked there) can't load, and is listed under
    "absent" so its misses read as such.
    """
    all_cases = json.loads((iteration / "cases.json").read_text())
    configs = sorted(p for p in iteration.iterdir() if (p / CATALOGUE).exists())
    if not configs:
        raise ValueError(f"no configs in {iteration}")
    result = {c.name: _score_config(c, iteration, all_cases) for c in configs}
    if "with_skill" in result and "old_skill" in result:
        result["delta"] = {"pass_rate": round(result["with_skill"]["pass_rate"] - result["old_skill"]["pass_rate"], 4)}
    (iteration / "trigger-benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
