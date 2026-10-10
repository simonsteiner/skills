"""Tests for skill_inventory.py, against throwaway repos.

    python3 -m unittest discover -s scripts
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from skill_inventory import inventory, main


class RepoFixture(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def skill(self, bucket, name, frontmatter=None):
        folder = self.repo / "skills" / bucket / name
        folder.mkdir(parents=True)
        fm = frontmatter if frontmatter is not None else f"name: {name}\ndescription: Does it. Use when asked."
        (folder / "SKILL.md").write_text(f"---\n{fm}\n---\nBody.\n")

    def curate(self, *names):
        (self.repo / "third-party").mkdir()
        manifest = {"agents": [], "sources": [{"repo": "o/r", "skills": [{"name": n} for n in names]}]}
        (self.repo / "third-party/skills.json").write_text(json.dumps(manifest))


class InventoryTest(RepoFixture):
    def test_lists_every_bucket_with_name_from_the_folder(self):
        self.skill("engineering", "a")
        self.skill("deprecated", "b", "name: not-b\ndescription: x")
        inv = inventory(self.repo)
        self.assertEqual(inv.problems, [])
        self.assertEqual([(s.name, s.bucket, s.published, s.active) for s in inv.skills],
                         [("b", "deprecated", False, False), ("a", "engineering", True, True)])

    def test_one_name_in_two_buckets_is_a_problem(self):
        # The live defect from docs/arch-review/2026-10-08-tooling.md (C1): lint kept
        # only the later entry and never checked the published one.
        self.skill("engineering", "pr-body")
        self.skill("personal", "pr-body")
        problems = inventory(self.repo).problems
        self.assertEqual(len(problems), 1)
        self.assertIn("skills/personal/pr-body/SKILL.md: skill name 'pr-body' is also owned by "
                      "skills/engineering/pr-body/SKILL.md", problems[0])

    def test_unknown_bucket_is_a_problem(self):
        self.skill("tools", "a")
        self.assertIn("bucket 'tools'", inventory(self.repo).problems[0])

    def test_curated_name_colliding_with_an_owned_one_is_a_problem(self):
        self.skill("deprecated", "a")
        self.curate("a", "b")
        problems = inventory(self.repo).problems
        self.assertEqual(len(problems), 1)
        self.assertIn("curated skill a from o/r collides", problems[0])

    def test_missing_frontmatter_still_counts_as_a_skill(self):
        self.skill("misc", "a", frontmatter="")
        (self.repo / "skills/misc/a/SKILL.md").write_text("No frontmatter.\n")
        [s] = inventory(self.repo).skills
        self.assertIsNone(s.fields)
        self.assertTrue(s.model_invoked)

    def test_user_invoked(self):
        self.skill("engineering", "a", "name: a\ndescription: x\ndisable-model-invocation: true")
        self.assertFalse(inventory(self.repo).skills[0].model_invoked)


class MainTest(RepoFixture):
    """The command line the shell scripts read with `cut`: name, bucket, folder."""

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv), self.repo)
        return code, out.getvalue().splitlines(), err.getvalue()

    def test_prints_name_bucket_folder_and_active_drops_deprecated(self):
        self.skill("engineering", "a")
        self.skill("deprecated", "b")
        a, b = self.repo / "skills/engineering/a", self.repo / "skills/deprecated/b"
        self.assertEqual(self.run_main(), (0, [f"b\tdeprecated\t{b}", f"a\tengineering\t{a}"], ""))
        self.assertEqual(self.run_main("--active"), (0, [f"a\tengineering\t{a}"], ""))

    def test_problems_exit_1_before_printing_anything(self):
        # Q4: an empty stdout is what stops link-skills.sh before it touches the store.
        self.skill("engineering", "a")
        self.skill("personal", "a")
        code, out, err = self.run_main("--active")
        self.assertEqual((code, out), (1, []))
        self.assertIn("is also owned by", err)

    def test_unknown_flag_exits_2(self):
        self.assertEqual(self.run_main("--bogus")[0], 2)


if __name__ == "__main__":
    unittest.main()
