"""Tests for catalog.py, against throwaway repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import json
import tempfile
import unittest
from pathlib import Path

from tooling import catalog
from tooling.skill_inventory import inventory


class CatalogTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.write("README.md", f"# Skills\n\nHand-written.\n\n{catalog.START}\nstale\n{catalog.END}\n\n## After\n")
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "n", "skills": ["./gone"], "version": "1"}))

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def skill(self, bucket, name, description, user_invoked=False):
        extra = "disable-model-invocation: true\n" if user_invoked else ""
        self.write(f"skills/{bucket}/{name}/SKILL.md",
                   f"---\nname: {name}\ndescription: >\n  {description}\n{extra}---\nBody.\n")

    def skills(self):
        return inventory(self.repo).skills

    def read(self, rel):
        return (self.repo / rel).read_text()

    def test_summary_is_a_model_invoked_description_up_to_its_use_sentence(self):
        self.skill("engineering", "m", "Does x, and y.  Also z. Use when x. Not for w.")
        self.assertEqual(catalog.summary(self.skills()[0]), "Does x, and y. Also z.")

    def test_summary_is_a_whole_user_invoked_description(self):
        self.skill("engineering", "u", "Does x. Then y. Use it twice.", user_invoked=True)
        self.assertEqual(catalog.summary(self.skills()[0]), "Does x. Then y. Use it twice.")

    def test_a_use_inside_a_sentence_doesnt_end_the_summary(self):
        self.skill("engineering", "m", "Picks the tool to use. Use when unsure.")
        self.assertEqual(catalog.summary(self.skills()[0]), "Picks the tool to use.")

    def test_no_use_sentence_is_a_problem(self):
        self.skill("engineering", "m", "Does x whenever asked.")
        self.assertEqual(len(catalog.problems(self.skills(), self.repo)), 1)

    def test_write_renders_every_list_and_keeps_the_prose(self):
        self.skill("engineering", "b-model", "Does b. Use when b.")
        self.skill("engineering", "a-model", "Does a. Use when a.")
        self.skill("engineering", "typed", "Does t.", user_invoked=True)
        self.skill("misc", "rare", "Does r. Use when r.")
        self.skill("in-progress", "draft", "Does d. Use when d.")
        catalog.write(self.skills(), self.repo)

        readme = self.read("README.md")
        self.assertTrue(readme.startswith("# Skills\n\nHand-written.\n\n"))
        self.assertTrue(readme.endswith(f"{catalog.END}\n\n## After\n"))
        self.assertNotIn("stale", readme)
        self.assertNotIn("draft", readme)
        block = readme[readme.index(catalog.START) + len(catalog.START):readme.index(catalog.END)]
        self.assertEqual(block, """

### Engineering

#### User-invoked

- **[typed](./skills/engineering/typed/SKILL.md)**: Does t.

#### Model-invoked

- **[a-model](./skills/engineering/a-model/SKILL.md)**: Does a.
- **[b-model](./skills/engineering/b-model/SKILL.md)**: Does b.

### Misc

#### Model-invoked

- **[rare](./skills/misc/rare/SKILL.md)**: Does r.

""")

        self.assertEqual(self.read("skills/in-progress/README.md"), f"""# In-progress

{catalog.START}

## Model-invoked

- **[draft](./draft/SKILL.md)**: Does d.

{catalog.END}
""")
        self.assertEqual(json.loads(self.read(".claude-plugin/plugin.json")), {
            "name": "n", "version": "1",
            "skills": ["./skills/engineering/a-model", "./skills/engineering/b-model",
                       "./skills/engineering/typed", "./skills/misc/rare"],
        })
        self.assertEqual(catalog.stale(self.skills(), self.repo), [])
        self.assertEqual(catalog.write(self.skills(), self.repo), [])

    def test_an_emptied_bucket_readme_keeps_an_empty_block(self):
        self.write("skills/misc/README.md", f"# Misc\n\n{catalog.START}\n\n- **[gone](./gone/SKILL.md)**: x.\n\n{catalog.END}\n")
        catalog.write(self.skills(), self.repo)
        self.assertEqual(self.read("skills/misc/README.md"), f"# Misc\n\n{catalog.START}\n{catalog.END}\n")


    def test_third_party_readme_lists_each_source_from_the_manifest(self):
        self.write("third-party/skills.json", json.dumps({"agents": ["claude-code"], "sources": [
            {"repo": "o/r", "why": "Their skills.\n  Kept.",
             "skills": [{"name": "c", "path": "skills/c", "invocation": "model", "why": "Does c. Worth it because x."},
                        {"name": "t", "path": "t", "invocation": "user", "why": "Typed."}],
             "archived": [{"name": "a", "path": ".", "why": "Retired. Replaced."}]},
            {"repo": "p/q", "why": "", "archived": [{"name": "b", "path": "b", "why": "Declined."}]}]}))
        self.write("third-party/README.md", f"# Third\n\n{catalog.START}\n{catalog.END}\n")
        catalog.write(self.skills(), self.repo)
        self.assertEqual(self.read("third-party/README.md"), f"""# Third

{catalog.START}

### [o/r](https://github.com/o/r)

Their skills. Kept.

#### User-invoked

- **[t](https://github.com/o/r/blob/HEAD/t/SKILL.md)**: Typed.

#### Model-invoked

- **[c](https://github.com/o/r/blob/HEAD/skills/c/SKILL.md)**: Does c.

<details>
<summary>Archived (1)</summary>

- **[a](https://github.com/o/r/blob/HEAD/SKILL.md)**: Retired. Replaced.

</details>

### [p/q](https://github.com/p/q)

<details>
<summary>Archived (1)</summary>

- **[b](https://github.com/p/q/blob/HEAD/b/SKILL.md)**: Declined.

</details>

{catalog.END}
""")

if __name__ == "__main__":
    unittest.main()
