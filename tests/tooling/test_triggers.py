"""Tests for triggers.py, against throwaway repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tooling import triggers
from tooling.authoring_rules import check
from tooling.skill_inventory import inventory

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, env=ENV, check=True,
                   capture_output=True)


def triggers_json(name, *cases):
    return json.dumps({"skills": [name], "triggers": [{"query": q, "should_trigger": t} for q, t in cases]})


class TriggersTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.skill("commit", "Writes commits. Use when committing.",
                   triggers=triggers_json("commit", ("commit this", True), ("open a PR", False)))
        self.skill("pr", "Writes PR bodies. Use when opening a PR.",
                   triggers=triggers_json("pr", ("open a PR", True), ("commit this", False), ("review PR 7", False)))
        self.skill("review", "Reviews docs.", user_invoked=True)

    def skill(self, name, description, triggers=None, user_invoked=False, bucket="engineering"):
        folder = self.repo / "skills" / bucket / name
        (folder / "evals").mkdir(parents=True, exist_ok=True)
        extra = "\ndisable-model-invocation: true" if user_invoked else ""
        (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}{extra}\n---\nBody.\n")
        if triggers is not None:
            (folder / "evals/triggers.json").write_text(triggers)
        return folder

    def skills(self):
        return inventory(self.repo).skills

    def by_name(self, name):
        return next(s for s in self.skills() if s.name == name)

    def test_valid_triggers_have_no_problems(self):
        for name in ("commit", "pr", "review"):
            self.assertEqual(triggers.problems(self.by_name(name)), [], name)

    def test_invalid_triggers(self):
        cases = {
            "{": "isn't valid JSON",
            "[]": 'must be an object with "skills" and "triggers"',
            json.dumps({"skills": ["x"], "triggers": []}): "\"skills\" doesn't list 'commit'",
            json.dumps({"skills": ["commit"], "triggers": [{"query": ""}]}): 'trigger 1 needs a non-empty "query"',
            json.dumps({"skills": ["commit"], "triggers": [{"query": "q", "should_trigger": "yes"}]}):
                'trigger 1 needs "should_trigger" as true or false',
            triggers_json("commit", ("q", True), ("q", False)): "trigger 2 repeats an earlier query",
            triggers_json("commit", ("a", True), ("b", True)): "needs both should_trigger true and false cases",
        }
        for text, fragment in cases.items():
            with self.subTest(fragment):
                (self.by_name("commit").folder / "evals/triggers.json").write_text(text)
                found = triggers.problems(self.by_name("commit"))
                self.assertTrue(any(fragment in p for p in found), found)

    def test_a_user_invoked_skill_cant_have_triggers_and_lint_says_so(self):
        self.skill("review", "Reviews docs.", user_invoked=True,
                   triggers=triggers_json("review", ("review my doc", True), ("commit", False)))
        self.assertIn("skills/engineering/review/evals/triggers.json: triggers.json on a user-invoked skill",
                      " ".join(check(self.repo, self.skills())))

    def test_cases_merge_labels_per_query(self):
        by_query = {c["query"]: c["labels"] for c in triggers.cases(self.skills())}
        self.assertEqual(by_query, {
            "commit this": {"commit": True, "pr": False},
            "open a PR": {"commit": False, "pr": True},
            "review PR 7": {"pr": False},
        })
        first, again = triggers.cases(self.skills()), triggers.cases(self.skills())
        self.assertEqual([c["query"] for c in first], [c["query"] for c in again], "the shuffle is fixed")

    def test_catalogue_lists_model_invoked_published_skills_and_extras(self):
        self.skill("draft", "Unpublished. Use when drafting.", bucket="in-progress")
        extra = Path(tempfile.mkdtemp(dir=self.repo))
        for name, desc in (("tdd", "Tests first. Use when testing."), ("pr", "An installed copy."),
                           ("review", "An installed copy of a user-invoked skill.")):
            (extra / name).mkdir()
            (extra / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n")
        self.assertEqual(triggers.catalogue(self.repo, also=[extra]), [
            {"name": "commit", "description": "Writes commits. Use when committing."},
            {"name": "pr", "description": "Writes PR bodies. Use when opening a PR."},
            {"name": "tdd", "description": "Tests first. Use when testing."},
        ])
        with self.assertRaisesRegex(ValueError, "--also: not a directory"):
            triggers.catalogue(self.repo, also=[extra / "no-such-dir"])

    def test_catalogue_at_a_ref_reads_the_old_descriptions(self):
        git(self.repo, "init", "-q")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "v1")
        self.skill("commit", "Commits, rewritten. Use before every git commit.",
                   triggers=triggers_json("commit", ("commit this", True), ("open a PR", False)))
        self.skill("branch", "New. Use when branching.")
        self.assertEqual([e["description"] for e in triggers.catalogue(self.repo, "HEAD")],
                         ["Writes commits. Use when committing.", "Writes PR bodies. Use when opening a PR."])
        # an installed copy of a skill added since the ref carries the new description: it stays out
        installed = Path(tempfile.mkdtemp(dir=self.repo))
        for name, desc in (("branch", "New. Use when branching."), ("tdd", "Tests first. Use when testing.")):
            (installed / name).mkdir()
            (installed / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n")
        self.assertEqual([e["name"] for e in triggers.catalogue(self.repo, "HEAD", also=[installed])],
                         ["commit", "pr", "tdd"])
        with self.assertRaisesRegex(ValueError, "not a git ref"):
            triggers.catalogue(self.repo, "--output=x")
        with self.assertRaisesRegex(ValueError, "git ls-tree"):
            triggers.catalogue(self.repo, "no-such-ref")

    def prepared(self, baseline=None):
        if baseline:
            git(self.repo, "init", "-q")
            git(self.repo, "add", ".")
            git(self.repo, "commit", "-qm", "v1")
            self.skill("pr", "Writes PR bodies, rewritten. Use before every gh pr create.",
                       triggers=triggers_json("pr", ("open a PR", True), ("commit this", False), ("review PR 7", False)))
        return triggers.prepare(self.repo, self.skills(), baseline=baseline)

    def test_prepare_lays_out_one_task_per_config_and_batch(self):
        iteration, tasks = self.prepared(baseline="HEAD")
        self.assertEqual(iteration, self.repo / ".eval-workspace/_triggers/iteration-1")
        self.assertEqual([(c, t.parent.name) for c, t in tasks], [("with_skill", "batch-1"), ("old_skill", "batch-1")])
        new, old = (t.read_text() for _, t in tasks)
        self.assertIn("rewritten. Use before every gh pr create.", new)
        self.assertIn("Writes PR bodies. Use when opening a PR.", old)
        for text in (new, old):
            self.assertIn('"open a PR"', text)
            self.assertNotIn("should_trigger", text, "a router never sees the labels")
            self.assertNotIn("review**", text, "user-invoked skills aren't in the catalogue")
        self.assertEqual(len(json.loads((iteration / "cases.json").read_text())), 3)
        self.assertEqual(self.prepared()[0].name, "iteration-2")

    def test_prepare_batches_long_case_lists(self):
        many = [(f"commit {i}", i % 2 == 0) for i in range(triggers.BATCH + 1)]
        self.skill("commit", "Writes commits. Use when committing.", triggers=triggers_json("commit", *many))
        _, tasks = triggers.prepare(self.repo, self.skills())
        self.assertEqual([t.parent.name for _, t in tasks], ["batch-1", "batch-2"])

    def test_prepare_refuses_invalid_triggers(self):
        (self.by_name("commit").folder / "evals/triggers.json").write_text("{")
        skills = self.skills()
        with self.assertRaisesRegex(ValueError, "commit: triggers.json isn't valid JSON"):
            triggers.prepare(self.repo, skills)

    def answer(self, iteration, config, picks):
        ids = {c["query"]: c["id"] for c in json.loads((iteration / "cases.json").read_text())}
        (iteration / config / "batch-1/answers.json").write_text(json.dumps({ids[q]: s for q, s in picks.items()}))

    def test_score_compares_the_configs(self):
        iteration, _ = self.prepared(baseline="HEAD")
        self.answer(iteration, "with_skill", {"commit this": ["commit"], "open a PR": ["pr"], "review PR 7": []})
        # the old descriptions miss the PR prompt and load pr on a review; "commit this" has no answer: nothing loads
        self.answer(iteration, "old_skill", {"open a PR": [], "review PR 7": ["pr"]})
        result = triggers.score(iteration)
        self.assertEqual(result["with_skill"]["pass_rate"], 1.0)
        self.assertEqual(result["with_skill"]["misses"], [])
        old = result["old_skill"]
        self.assertEqual((old["passed"], old["total"]), (2, 5))
        self.assertEqual(old["per_skill"]["commit"], {"should_trigger": "0/1", "should_not_trigger": "1/1"})
        self.assertEqual(old["per_skill"]["pr"], {"should_trigger": "0/1", "should_not_trigger": "1/2"})
        self.assertIn({"query": "review PR 7", "skill": "pr", "should_trigger": False, "loaded": ["pr"]}, old["misses"])
        self.assertEqual(result["delta"], {"pass_rate": 0.6})
        self.assertTrue((iteration / "trigger-benchmark.json").exists())

    def test_score_names_a_skill_absent_from_a_catalogue(self):
        iteration, _ = self.prepared()
        self.answer(iteration, "with_skill", {})
        catalogue = iteration / "with_skill/catalogue.json"
        catalogue.write_text(json.dumps([e for e in json.loads(catalogue.read_text()) if e["name"] != "pr"]))
        self.assertEqual(triggers.score(iteration)["with_skill"]["absent"], ["pr"])

    def test_score_refuses_unanswered_or_malformed_batches(self):
        iteration, _ = self.prepared()
        with self.assertRaisesRegex(ValueError, "not answered yet: with_skill/batch-1/answers.json"):
            triggers.score(iteration)
        (iteration / "with_skill/batch-1/answers.json").write_text('{"1": "commit"}')
        with self.assertRaisesRegex(ValueError, "must map message numbers to lists of skill names"):
            triggers.score(iteration)


if __name__ == "__main__":
    unittest.main()
