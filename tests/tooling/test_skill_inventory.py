"""Tests for skill_inventory.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from tooling.skill_inventory import inventory


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

    def test_trailing_comment_is_not_part_of_the_value(self):
        # S1 in docs/arch-review/2026-10-08-tooling.md: this read as "true # x", so model-invoked.
        self.skill("engineering", "a", "name: a\ndescription: 'x # y'\ndisable-model-invocation: true # x")
        [s] = inventory(self.repo).skills
        self.assertFalse(s.model_invoked)
        self.assertEqual(s.fields["description"], "x # y")

    def test_a_quoted_value_ends_at_its_own_quote(self):
        self.skill("engineering", "a", 'name: a\ndescription: x\ndisable-model-invocation: "true" # "x"')
        self.assertFalse(inventory(self.repo).skills[0].model_invoked)


if __name__ == "__main__":
    unittest.main()
