"""A skill's evals: evals/evals.json, and the workspace one iteration of runs lives in.

The loop follows https://agentskills.io/skill-creation/evaluating-skills: run every eval
with the skill and with a baseline (no skill, or the skill at an older git ref), grade
each run's outputs against the eval's expected behaviour, and aggregate the grades. This
module does the mechanical parts — validating evals.json, laying out an iteration, and
aggregating — so the runs and the grading are all that's left for agents to do.

    .eval-workspace/<skill>/iteration-<N>/
      old_skill/                      the baseline snapshot, when --baseline <ref> is given
      eval-<i>-<slug>/
        <config>/                     with_skill, and without_skill or old_skill
          task.md                     what the executor runs, in a fresh context
          grade.md                    what the grader checks, in another fresh context
          outputs/                    what the executor writes
          timing.json                 {"total_tokens", "duration_ms"}, from the executor
          grading.json                {"assertion_results": [...], "summary": {...}}
      benchmark.json                  written by benchmark()

evals.json (Anthropic's format): {"skills": [<name>], "evals": [{"query", "setup"?,
"expected_behavior": [...], "files"?: [...]}]}.

scripts/eval-skill.py is the command line; tests/tooling/test_evals.py tests it.
"""

import io
import json
import re
import shutil
import statistics
import subprocess
import tarfile

WORKSPACE = ".eval-workspace"


def problems(skill):
    """What's wrong with a skill's evals/evals.json, if it has one."""
    path = skill.folder / "evals/evals.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"evals.json isn't valid JSON: {e}"]
    if not isinstance(data, dict):
        return ["evals.json must be an object with \"skills\" and \"evals\""]
    out = []
    if not isinstance(data.get("skills"), list) or skill.name not in data["skills"]:
        out.append(f'"skills" doesn\'t list {skill.name!r}')
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        return out + ['"evals" must be a non-empty list']
    for i, e in enumerate(evals, 1):
        if not isinstance(e, dict):
            out.append(f"eval {i} isn't an object")
            continue
        if not isinstance(e.get("query"), str) or not e["query"].strip():
            out.append(f'eval {i} has no "query"')
        behaviour = e.get("expected_behavior")
        if not isinstance(behaviour, list) or not behaviour or not all(isinstance(b, str) and b for b in behaviour):
            out.append(f'eval {i} needs "expected_behavior" as a non-empty list of strings')
        if "setup" in e and not isinstance(e["setup"], str):
            out.append(f'eval {i}: "setup" must be a string')
        files = e.get("files", [])
        if not isinstance(files, list) or not all(isinstance(f, str) and f for f in files):
            out.append(f'eval {i}: "files" must be a list of paths')
            continue
        for f in files:
            if not (skill.folder / f).is_file():
                out.append(f"eval {i}: file {f!r} doesn't exist")
    return out


def slug(text, words=5):
    return "-".join(re.findall(r"[a-z0-9]+", text.lower())[:words]) or "eval"


def snapshot(repo, skill, ref, dest):
    """Extract the skill's folder as it was at git `ref` into `dest`."""
    rel = skill.folder.relative_to(repo).as_posix()
    archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", ref, rel],
                             capture_output=True, check=False)
    if archive.returncode != 0:
        raise ValueError(f"can't read {rel} at {ref!r}: {archive.stderr.decode().strip()}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(dest, filter="data")
    return dest / rel


TASK = """\
Execute this task in a fresh context, as a user's agent would.

- Skill: {skill}
- Task, as the user typed it: {query}
- Setup to build first, in a throwaway directory you create: {setup}
- Input files: {files}
- Save to {outputs}/: your final reply to the user as reply.md, plus any files the task produced.
- When done, write {timing} as {{"total_tokens": <int>, "duration_ms": <int>}}.

Write nothing in the skills repo except the output paths above, and never touch other sessions' files or any real GitHub repo.
"""

GRADE = """\
Grade one eval run, in a fresh context. Read everything in {outputs}/.

For each expected behaviour below, decide PASS or FAIL with concrete evidence quoted or
referenced from the outputs. No benefit of the doubt: a label without the substance fails.

{assertions}

Write {grading} as:
{{"assertion_results": [{{"text": "<behaviour>", "passed": true, "evidence": "<quote or reference>"}}],
 "summary": {{"passed": <int>, "failed": <int>, "total": <int>, "pass_rate": <float>}}}}
"""


def prepare(repo, skill, baseline=None, root=None):
    """Lay out the next iteration for `skill`; return (iteration dir, [(eval, config, task.md)])."""
    found = problems(skill)
    if found:
        raise ValueError("; ".join(found))
    evals = json.loads((skill.folder / "evals/evals.json").read_text())["evals"]
    base = (root or repo / WORKSPACE) / skill.name
    n = 1 + max((int(p.name.split("-")[1]) for p in base.glob("iteration-*") if p.name.split("-")[1].isdigit()), default=0)
    iteration = base / f"iteration-{n}"
    iteration.mkdir(parents=True)

    configs = {"with_skill": str(skill.folder)}
    if baseline:
        try:
            configs["old_skill"] = str(snapshot(repo, skill, baseline, iteration / "old_skill"))
        except ValueError:
            shutil.rmtree(iteration)  # a failed iteration would still take the next number
            raise
    else:
        configs["without_skill"] = "none — work without any skill"

    runs = []
    for i, e in enumerate(evals, 1):
        eval_dir = iteration / f"eval-{i}-{slug(e['query'])}"
        for config, skill_path in configs.items():
            run = eval_dir / config
            (run / "outputs").mkdir(parents=True)
            files = ", ".join(str(skill.folder / f) for f in e.get("files", [])) or "none"
            (run / "task.md").write_text(TASK.format(
                skill=skill_path, query=e["query"], setup=e.get("setup", "none"), files=files,
                outputs=run / "outputs", timing=run / "timing.json"))
            (run / "grade.md").write_text(GRADE.format(
                outputs=run / "outputs", grading=run / "grading.json",
                assertions="\n".join(f"- {b}" for b in e["expected_behavior"])))
            runs.append((eval_dir.name, config, run / "task.md"))
    return iteration, runs


def _stats(values):
    return {"mean": round(statistics.fmean(values), 4),
            "stddev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0}


def _read_json(path, iteration, fields):
    """`path` parsed as an object whose `fields` (dotted) are numbers when present; ValueError names the file."""
    where = path.relative_to(iteration)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"{where} isn't valid JSON: {e}") from None
    for field in fields:
        value, keys = data, field.split(".")
        while keys and isinstance(value, dict):
            value = value.get(keys.pop(0))
        if keys and value is not None:
            msg = f"{field} sits under something that isn't an object"
        elif value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            msg = f"{field} must be a number, not {value!r}"
        else:
            continue
        raise ValueError(f"{where}: {msg}")
    return data


def benchmark(iteration):
    """Aggregate every run's grading.json and timing.json into benchmark.json.

    Returns the benchmark, or raises ValueError naming every run that isn't graded yet.
    """
    runs = sorted(p for p in iteration.glob("eval-*/*") if (p / "task.md").exists())
    missing = [str(r.relative_to(iteration)) for r in runs if not (r / "grading.json").exists()]
    if not runs or missing:
        raise ValueError("not graded yet: " + (", ".join(missing) or "no runs in " + str(iteration)))

    by_config = {}
    for run in runs:
        grading = _read_json(run / "grading.json", iteration, ["summary.pass_rate"])
        results = grading.get("assertion_results") or []
        rate = (grading.get("summary") or {}).get("pass_rate")
        if rate is None:
            rate = sum(r.get("passed") is True for r in results) / len(results) if results else 0.0
        timing_path = run / "timing.json"
        timing = _read_json(timing_path, iteration, ["duration_ms", "total_tokens"]) if timing_path.exists() else {}
        row = by_config.setdefault(run.name, {"pass_rate": [], "time_seconds": [], "tokens": []})
        row["pass_rate"].append(rate)
        if "duration_ms" in timing:
            row["time_seconds"].append(timing["duration_ms"] / 1000)
        if "total_tokens" in timing:
            row["tokens"].append(timing["total_tokens"])

    summary = {c: {k: _stats(v) for k, v in m.items() if v} for c, m in by_config.items()}
    baseline = next((c for c in ("old_skill", "without_skill") if c in summary), None)
    if "with_skill" in summary and baseline:
        summary["delta"] = {k: round(summary["with_skill"][k]["mean"] - summary[baseline][k]["mean"], 4)
                            for k in summary["with_skill"] if k in summary[baseline]}
    result = {"run_summary": summary}
    (iteration / "benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
