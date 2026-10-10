"""Tests for dev_links.py, against a throwaway repo and home directory.

    python3 -m unittest discover -s tests -t .
"""

import os
import tempfile
import unittest
from pathlib import Path

from tooling.dev_links import LinkError, check, link
from tooling.skill_inventory import inventory
from tooling.third_party import Home


class DevLinksTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(os.path.realpath(tmp.name))
        self.repo, self.home = root / "repo", Home(root / "home")
        for bucket, name in (("engineering", "a"), ("personal", "b"), ("deprecated", "c")):
            folder = self.repo / "skills" / bucket / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
        self.skills = [s for s in inventory(self.repo).skills if s.active]
        self.store, self.claude = self.home.store, self.home.agent_dir("claude-code")
        self.log = []

    def statuses(self):
        return [str(s) for s in check(self.skills, self.home, self.repo, "link")]

    def test_links_active_skills_in_the_skills_sh_layout(self):
        link(self.skills, self.home, self.repo, self.log.append)
        self.assertEqual(os.readlink(self.store / "a"), str(self.repo / "skills/engineering/a"))
        self.assertEqual(os.readlink(self.claude / "b"), "../../.agents/skills/b")
        self.assertFalse((self.store / "c").exists())
        self.assertEqual(self.statuses(), ["ok        a", "ok        b"])

    def test_check_reports_what_isnt_linked(self):
        self.assertEqual(self.statuses(), [
            f"missing   a (not linked into {self.claude} — run link)",
            f"missing   b (not linked into {self.claude} — run link)",
        ])

    def test_replaces_an_installed_copy(self):
        (self.store / "a").mkdir(parents=True)
        (self.store / "a/SKILL.md").write_text("copy")
        link(self.skills, self.home, self.repo, self.log.append)
        self.assertTrue((self.store / "a").is_symlink())

    def test_replaces_a_plain_file(self):
        for d in (self.store, self.claude):
            d.mkdir(parents=True, exist_ok=True)
            (d / "a").write_text("stray")
        link(self.skills, self.home, self.repo, self.log.append)
        self.assertEqual(self.statuses(), ["ok        a", "ok        b"])

    def test_prunes_links_to_skills_that_are_gone_and_nothing_else(self):
        link(self.skills, self.home, self.repo, self.log.append)
        (self.store / "gone").symlink_to(self.repo / "skills/engineering/gone")
        (self.claude / "gone").symlink_to("../../.agents/skills/gone")
        (self.store / "other").symlink_to("/elsewhere")
        (self.store / "c").symlink_to(self.repo / "skills/deprecated/c")
        self.assertEqual(self.statuses()[2:], [
            f"dead      c ({self.store / 'c'} -> {self.repo / 'skills/deprecated/c'} — run link)",
            f"dead      gone ({self.store / 'gone'} -> {self.repo / 'skills/engineering/gone'} — run link)",
        ])
        link(self.skills, self.home, self.repo, self.log.append)
        self.assertEqual(self.log[-2:], ["pruned c", "pruned gone"])
        self.assertFalse((self.claude / "gone").is_symlink())
        self.assertTrue((self.store / "other").is_symlink())

    def test_refuses_a_store_that_links_into_the_repo(self):
        self.store.parent.mkdir(parents=True)
        self.store.symlink_to(self.repo / "skills")
        with self.assertRaises(LinkError):
            link(self.skills, self.home, self.repo, self.log.append)


if __name__ == "__main__":
    unittest.main()
