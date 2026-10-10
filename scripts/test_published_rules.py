"""Tests for published_rules.py, against throwaway repos.

    python3 -m unittest discover -s scripts
"""

import json
import tempfile
import unittest
from pathlib import Path

from published_rules import check
from skill_inventory import inventory

README = """# Skills

### Engineering

#### User-invoked

- **[u](./skills/engineering/u/SKILL.md)** — typed.

#### Model-invoked

- **[m](./skills/engineering/m/SKILL.md)** — reached for.

## Third-party skills

- **[elsewhere](./third-party/README.md)** — not an owned skill.
"""

BUCKET = """# Engineering

## User-invoked

- **[u](./u/SKILL.md)** — typed.

## Model-invoked

- **[m](./m/SKILL.md)** — reached for.
"""


class PublishedRulesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.skill("engineering", "u", "disable-model-invocation: true")
        self.skill("engineering", "m")
        self.write("README.md", README)
        self.write("skills/engineering/README.md", BUCKET)
        self.write(".claude-plugin/plugin.json", json.dumps(
            {"skills": ["./skills/engineering/u", "./skills/engineering/m"]}))
        self.write("third-party/skills.json", json.dumps({"agents": [], "sources": [
            {"repo": "o/r", "why": "w", "skills": [{"name": "c", "why": "w"}],
             "archived": [{"name": "a", "why": "w"}]}]}))

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def skill(self, bucket, name, extra=""):
        self.write(f"skills/{bucket}/{name}/SKILL.md", f"---\nname: {name}\ndescription: x\n{extra}\n---\nBody.\n")

    def edit(self, rel, old, new):
        path = self.repo / rel
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new))

    def problems(self):
        return check(self.repo, inventory(self.repo).skills)

    def test_the_fixture_passes(self):
        self.assertEqual(self.problems(), [])

    def test_skill_missing_from_its_bucket_readme(self):
        # Reproduced in docs/arch-review/2026-10-08-tooling.md (C2): `zz` passed lint.
        self.skill("engineering", "zz")
        self.edit("README.md", "## Third", "- **[zz](./skills/engineering/zz/SKILL.md)** — new.\n\n## Third")
        self.edit(".claude-plugin/plugin.json", '"]}', '", "./skills/engineering/zz"]}')
        self.assertEqual(self.problems(), ["skills/engineering/README.md: no entry linking zz to ./zz/SKILL.md"])

    def test_link_inside_an_html_comment_is_no_entry(self):
        self.edit("README.md", "- **[m](./skills/engineering/m/SKILL.md)** — reached for.",
                  "<!-- - **[m](./skills/engineering/m/SKILL.md)** -->")
        self.assertEqual(self.problems(), ["README.md: no entry linking m to ./skills/engineering/m/SKILL.md"])

    def test_skill_under_the_wrong_group(self):
        self.edit("skills/engineering/README.md", "- **[u](./u/SKILL.md)** — typed.\n", "")
        self.edit("skills/engineering/README.md", "reached for.", "reached for.\n- **[u](./u/SKILL.md)** — typed.")
        self.assertEqual(self.problems(),
                         ["skills/engineering/README.md:9: u is User-invoked but listed under Model-invoked"])

    def test_link_text_must_be_the_name(self):
        self.edit("README.md", "**[u](", "**[You](")
        self.assertEqual(self.problems(), ["README.md:7: link text 'You' isn't the skill's name 'u'"])

    def test_unpublished_skill_in_the_readme_and_plugin(self):
        self.skill("personal", "p")
        self.write("skills/personal/README.md", "## Model-invoked\n\n- **[p](./p/SKILL.md)** — mine.\n")
        self.edit("README.md", "## Third", "- **[p](./skills/personal/p/SKILL.md)** — mine.\n\n## Third")
        self.edit(".claude-plugin/plugin.json", '"]}', '", "./skills/personal/p"]}')
        self.assertEqual(self.problems(), [
            "README.md:13: p is in personal/ but README.md links it",
            ".claude-plugin/plugin.json lists ./skills/personal/p, which is no published skill",
        ])

    def test_archived_entry_without_a_reason(self):
        self.edit("third-party/skills.json", '{"name": "a", "why": "w"}', '{"name": "a", "why": " "}')
        self.assertEqual(self.problems(), ["third-party/skills.json: archived entry a from o/r doesn't say why"])

    def test_missing_bucket_readme(self):
        self.skill("misc", "x")
        self.edit("README.md", "## Third", "#### Model-invoked\n\n- **[x](./skills/misc/x/SKILL.md)** — x.\n\n## Third")
        self.edit(".claude-plugin/plugin.json", '"]}', '", "./skills/misc/x"]}')
        self.assertEqual(self.problems(), ["skills/misc/README.md is missing"])

    def test_any_link_to_an_unpublished_skill_fails(self):
        self.skill("personal", "p")
        self.write("skills/personal/README.md", "## Model-invoked\n\n- **[p](./p/SKILL.md)** — mine.\n")
        self.edit("README.md", "## Third", "See [p](./skills/personal/p/SKILL.md), [it](skills/personal/p/).\n\n## Third")
        self.assertEqual(self.problems(), ["README.md:13: p is in personal/ but README.md links it"] * 2)

    def test_an_emptied_bucket_readme_is_still_checked(self):
        self.write("skills/misc/README.md", "## Model-invoked\n\n- **[gone](./gone/SKILL.md)** — moved.\n")
        self.assertEqual(self.problems(),
                         ["skills/misc/README.md:3: gone links ./gone/SKILL.md, which is no skill this file lists"])

    def test_entries_in_code_fences_dont_count(self):
        for fence in ("```", "~~~", "````"):
            self.edit("README.md", "## Third", f"{fence}md\n- **[zz](./skills/engineering/zz/SKILL.md)** — x.\n{fence}\n\n## Third")
            self.assertEqual(self.problems(), [], fence)
            self.write("README.md", README)

    def test_a_skill_listed_twice(self):
        self.edit("skills/engineering/README.md", "reached for.", "reached for.\n- **[m](./m/SKILL.md)** — again.")
        self.assertEqual(self.problems(), ["skills/engineering/README.md:10: m is listed twice"])

    def test_every_reason_must_be_text(self):
        manifest = {"agents": [], "sources": [{"repo": "o/r", "why": None, "skills": [{"name": "c", "why": ""}],
                                               "archived": [{"name": "a"}]}]}
        self.write("third-party/skills.json", json.dumps(manifest))
        self.assertEqual(self.problems(), [
            "third-party/skills.json: source o/r doesn't say why",
            "third-party/skills.json: skills entry c from o/r doesn't say why",
            "third-party/skills.json: archived entry a from o/r doesn't say why",
        ])


if __name__ == "__main__":
    unittest.main()
