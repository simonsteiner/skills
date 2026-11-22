"""A throwaway repo of skills for the lint-rule tests (not a test module itself)."""

import tempfile
import unittest
from pathlib import Path

from tooling.authoring_rules import check
from tooling.skill_inventory import inventory

GOOD = "name: {name}\ndescription: Does it. Use when asked."


class SkillRepoTest(unittest.TestCase):
    """A throwaway repo to write skills into, and the lint problems check() finds in it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)

    def skill(self, name="a", frontmatter=GOOD, body="Body.\n", files=None):
        folder = self.repo / "skills/engineering" / name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(f"---\n{frontmatter.format(name=name)}\n---\n{body}")
        for rel, text in (files or {}).items():
            (folder / rel).parent.mkdir(parents=True, exist_ok=True)
            (folder / rel).write_text(text)
        return folder

    def problems(self):
        return check(self.repo, inventory(self.repo).skills)

    def assertProblem(self, fragment):
        self.assertTrue(any(fragment in p for p in self.problems()), self.problems())
