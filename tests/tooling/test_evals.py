"""Tests for evals.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tooling import evals
from tooling.skill_inventory import inventory

EVALS = {"skills": ["a"], "evals": [
    {"query": "Review PR 7, please", "setup": "One PR.", "expected_behavior": ["Posts one review", "Fixes the bug"]},
    {"query": "review since main", "expected_behavior": ["Runs in local mode"]},
]}


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                   capture_output=True)


class EvalsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.folder = self.repo / "skills/engineering/a"
        (self.folder / "evals").mkdir(parents=True)
        self.write_skill("Version one.\n")
        self.write_evals(EVALS)

    def write_skill(self, body):
        (self.folder / "SKILL.md").write_text(f"---\nname: a\ndescription: Does it. Use when asked.\n---\n{body}")

    def write_evals(self, data):
        (self.folder / "evals/evals.json").write_text(data if isinstance(data, str) else json.dumps(data))

    def skill(self):
        return inventory(self.repo).skills[0]

    def test_valid_evals_have_no_problems(self):
        self.assertEqual(evals.problems(self.skill()), [])

    def test_invalid_evals(self):
        self.write_evals("{")
        self.assertIn("isn't valid JSON", evals.problems(self.skill())[0])
        self.write_evals({"skills": ["b"], "evals": [{"query": "", "expected_behavior": []}, 3,
                                                       {"query": "q", "expected_behavior": ["x"], "files": ["gone.csv"]}]})
        self.assertEqual(evals.problems(self.skill()), [
            "\"skills\" doesn't list 'a'", 'eval 1 has no "query"',
            'eval 1 needs "expected_behavior" as a non-empty list of strings', "eval 2 isn't an object",
            "eval 3: file 'gone.csv' doesn't exist"])

    def test_prepare_without_baseline(self):
        iteration, runs = evals.prepare(self.repo, self.skill())
        self.assertEqual(iteration, self.repo / ".eval-workspace/a/iteration-1")
        self.assertEqual([(e, c) for e, c, _ in runs], [
            ("eval-1-review-pr-7-please", "with_skill"), ("eval-1-review-pr-7-please", "without_skill"),
            ("eval-2-review-since-main", "with_skill"), ("eval-2-review-since-main", "without_skill")])
        task = runs[0][2].read_text()
        self.assertIn(f"- Skill: {self.folder}", task)
        self.assertIn("Review PR 7, please", task)
        self.assertIn("One PR.", task)
        self.assertIn("without any skill", runs[1][2].read_text())
        self.assertIn("- Posts one review\n- Fixes the bug", runs[0][2].with_name("grade.md").read_text())
        self.assertTrue((runs[0][2].parent / "outputs").is_dir())
        self.assertEqual(evals.prepare(self.repo, self.skill())[0].name, "iteration-2")

    def test_prepare_with_baseline_snapshots_the_old_skill(self):
        git(self.repo, "init", "-q")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "v1")
        self.write_skill("Version two.\n")
        iteration, runs = evals.prepare(self.repo, self.skill(), baseline="HEAD")
        old = iteration / "old_skill/skills/engineering/a"
        self.assertEqual((old / "SKILL.md").read_text().splitlines()[-1], "Version one.")
        self.assertEqual({c for _, c, _ in runs}, {"with_skill", "old_skill"})
        self.assertIn(f"- Skill: {old}", next(t for _, c, t in runs if c == "old_skill").read_text())

    def test_prepare_rejects_a_bad_ref_and_invalid_evals(self):
        git(self.repo, "init", "-q")
        with self.assertRaisesRegex(ValueError, "can't read"):
            evals.prepare(self.repo, self.skill(), baseline="nope")
        self.write_evals({"skills": ["a"], "evals": []})
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            evals.prepare(self.repo, self.skill())

    def test_benchmark(self):
        iteration, runs = evals.prepare(self.repo, self.skill())
        with self.assertRaisesRegex(ValueError, "not graded yet: eval-1-review-pr-7-please/with_skill"):
            evals.benchmark(iteration)
        rates = {"with_skill": [1.0, 0.5], "without_skill": [0.5, 0.0]}
        for i, (_, config, task) in enumerate(runs):
            rate = rates[config][i // 2]
            (task.parent / "grading.json").write_text(json.dumps({"summary": {"pass_rate": rate}}))
            (task.parent / "timing.json").write_text(json.dumps({"total_tokens": 1000 * (i + 1), "duration_ms": 2000}))
        result = evals.benchmark(iteration)["run_summary"]
        self.assertEqual(result["with_skill"]["pass_rate"], {"mean": 0.75, "stddev": 0.3536})
        self.assertEqual(result["delta"], {"pass_rate": 0.5, "time_seconds": 0.0, "tokens": -1000.0})
        self.assertTrue((iteration / "benchmark.json").exists())

    def test_pass_rate_is_computed_when_the_summary_is_missing(self):
        iteration, runs = evals.prepare(self.repo, self.skill())
        for _, _, task in runs:
            (task.parent / "grading.json").write_text(json.dumps(
                {"assertion_results": [{"passed": True}, {"passed": False}, {"passed": True}, {"passed": True}]}))
        self.assertEqual(evals.benchmark(iteration)["run_summary"]["with_skill"]["pass_rate"]["mean"], 0.75)


if __name__ == "__main__":
    unittest.main()
