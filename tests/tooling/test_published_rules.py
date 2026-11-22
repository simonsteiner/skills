"""Tests for published_rules.py, against throwaway repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from tooling import catalog
from tooling.published_rules import check
from tooling.skill_inventory import inventory

README = f"""# Skills

{catalog.START}
{catalog.END}

## Third-party skills

- **[elsewhere](./third-party/README.md)** — not an owned skill.
"""


class PublishedRulesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.skill("engineering", "u", "disable-model-invocation: true")
        self.skill("engineering", "m")
        self.write("README.md", README)
        self.write(".claude-plugin/plugin.json", json.dumps({"skills": []}))
        self.write("third-party/skills.json", json.dumps({"agents": ["claude-code"], "sources": [
            {"repo": "o/r", "why": "w", "skills": [{"name": "c", "why": "w"}],
             "archived": [{"name": "a", "why": "w"}]}]}))
        self.build()

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def skill(self, bucket, name, extra=""):
        self.write(f"skills/{bucket}/{name}/SKILL.md",
                   f"---\nname: {name}\ndescription: Does x. Use when x.\n{extra}\n---\nBody.\n")

    def build(self):
        catalog.write(inventory(self.repo).skills, self.repo)

    def edit(self, rel, old, new):
        path = self.repo / rel
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new))

    def problems(self):
        return check(self.repo, inventory(self.repo).skills)

    def test_the_fixture_passes(self):
        self.assertEqual(self.problems(), [])

    def test_a_new_skill_leaves_the_catalog_stale_until_rebuilt(self):
        # The C2 case from docs/arch-review/2026-10-08-tooling.md: `zz` missing from its bucket README.
        self.skill("engineering", "zz")
        self.assertEqual(self.problems(), [
            "README.md: the skill catalog is out of date; run scripts/build-catalog.py",
            "skills/engineering/README.md: the skill catalog is out of date; run scripts/build-catalog.py",
            ".claude-plugin/plugin.json: the skill catalog is out of date; run scripts/build-catalog.py",
        ])
        self.build()
        self.assertEqual(self.problems(), [])

    def test_a_hand_edit_inside_the_catalog_is_stale(self):
        self.edit("skills/engineering/README.md", "Does x.", "Does y.")
        self.assertEqual(self.problems(),
                         ["skills/engineering/README.md: the skill catalog is out of date; run scripts/build-catalog.py"])

    def test_a_model_invoked_description_without_a_use_sentence(self):
        self.write("skills/engineering/m/SKILL.md", "---\nname: m\ndescription: Does x when asked.\n---\nBody.\n")
        self.assertEqual(self.problems()[0],
                         "skills/engineering/m/SKILL.md: model-invoked description needs a summary before "
                         'a sentence starting "Use" ("Use when…"); the catalog lists that summary')

    def test_unpublished_skill_stays_out_of_the_readme_and_plugin(self):
        self.skill("personal", "p")
        self.build()
        self.assertEqual(self.problems(), [])
        self.assertNotIn("personal", (self.repo / "README.md").read_text())
        self.assertNotIn("personal", (self.repo / ".claude-plugin/plugin.json").read_text())
        self.assertIn("[p](./p/SKILL.md)", (self.repo / "skills/personal/README.md").read_text())

    def test_any_link_to_an_unpublished_skill_fails(self):
        self.skill("personal", "p")
        self.build()
        self.edit("README.md", "## Third", "See [p](./skills/personal/p/SKILL.md), [it](skills/personal/p/).\n\n## Third")
        n = (self.repo / "README.md").read_text().split("\n").index(
            "See [p](./skills/personal/p/SKILL.md), [it](skills/personal/p/).") + 1
        self.assertEqual(self.problems(), [f"README.md:{n}: p is in personal/ but README.md links it"] * 2)

    def test_links_in_comments_and_code_fences_dont_count(self):
        self.skill("personal", "p")
        for wrap in ("<!-- {} -->", "```md\n{}\n```", "~~~\n{}\n~~~"):
            link = wrap.format("[p](./skills/personal/p/SKILL.md)")
            self.write("README.md", README.replace("## Third", f"{link}\n\n## Third"))
            self.build()
            self.assertEqual(self.problems(), [], wrap)

    def test_readme_without_a_catalog_block(self):
        self.write("README.md", "# Skills\n")
        self.assertEqual(self.problems(), [
            f"README.md has no generated skill catalog: add the {catalog.START!r} and {catalog.END!r} lines"])

    def test_archived_entry_without_a_reason(self):
        self.edit("third-party/skills.json", '{"name": "a", "why": "w"}', '{"name": "a", "why": " "}')
        self.assertEqual(self.problems(), ["third-party/skills.json: archived entry a from o/r doesn't say why"])

    def test_every_reason_must_be_text(self):
        manifest = {"agents": ["x"], "sources": [{"repo": "o/r", "why": None, "skills": [{"name": "c", "why": ""}],
                                               "archived": [{"name": "a"}]}]}
        self.write("third-party/skills.json", json.dumps(manifest))
        self.assertEqual(self.problems(), [
            "third-party/skills.json: source o/r doesn't say why",
            "third-party/skills.json: skills entry c from o/r doesn't say why",
            "third-party/skills.json: archived entry a from o/r doesn't say why",
        ])

    def test_a_source_needs_agents(self):
        self.edit("third-party/skills.json", '"agents": ["claude-code"]', '"agents": []')
        self.assertEqual(self.problems(), ["third-party/skills.json: source o/r has no agents, nor does the manifest"])


if __name__ == "__main__":
    unittest.main()
