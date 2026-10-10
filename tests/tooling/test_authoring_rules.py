"""Tests for authoring_rules.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from tooling.authoring_rules import check
from tooling.skill_inventory import inventory

GOOD = "name: {name}\ndescription: Does it. Use when asked."


class AuthoringRulesTest(unittest.TestCase):
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

    def test_a_clean_skill_has_no_problems(self):
        self.skill()
        self.assertEqual(self.problems(), [])

    def test_name_hyphens_follow_the_spec(self):
        for name in ("-a", "a-", "a--b"):
            with self.subTest(name=name):
                self.setUp()
                self.skill(name)
                self.assertProblem("single inner hyphens")

    def test_reserved_word_and_folder_mismatch(self):
        self.skill("claude-x")
        self.skill("b", "name: c\ndescription: Does it. Use when asked.")
        self.assertProblem("reserved word")
        self.assertProblem("doesn't match its folder")

    def test_description_rules(self):
        self.skill("a", "name: a\ndescription: I can do it.")
        self.assertProblem("isn't third person")
        self.assertProblem("never says when")

    def test_user_invoked_description_needs_no_when(self):
        self.skill("a", "name: a\ndescription: Does it.\ndisable-model-invocation: true")
        self.assertEqual(self.problems(), [])

    def test_compatibility_is_at_most_500_chars(self):
        self.skill("a", GOOD + "\ncompatibility: " + "x" * 501)
        self.assertProblem("compatibility must be 1-500 chars")

    def test_body_over_the_token_budget(self):
        self.skill(body="word " * 5000)
        self.assertProblem("tokens, over 5000")

    def test_vague_instruction(self):
        self.skill(body="Handle errors appropriately.\n")
        self.assertProblem('vague instruction "handle errors appropriately"')

    def test_one_off_commands_pin_a_version(self):
        self.skill(body="Run `npx eslint --fix .`, `uvx ruff@0.8.0 check`, `npx --yes rumdl@0.2 check`, "
                        "`pipx run 'black==24.10.0'`, `npx @scope/tool@1.2`, `npx prettier@latest .`.\n\n"
                        "In prose uvx is handy.\n\n```bash\nbunx tsc --noEmit\n```\n")
        self.assertEqual([p.split("command for ")[1].split(";")[0] for p in self.problems() if "unpinned" in p],
                         ["'eslint'", "'prettier@latest'", "'tsc'"])

    def test_unmentioned_and_nested_files(self):
        self.skill(files={"NOTES.md": "x\n", "references/deep/x.md": "x\n", "README.md": "x\n"})
        self.assertProblem("NOTES.md: bundled file is never mentioned")
        self.assertProblem("more than one level below")
        self.assertProblem("documentation file inside a skill folder")

    def test_broken_link_and_chained_reference(self):
        self.skill(body="See [A](A.md), [B](B.md) and [gone](gone.md).\n",
                   files={"A.md": "See [B](B.md).\n", "B.md": "x\n"})
        self.assertProblem("link to 'gone.md' doesn't resolve")
        self.assertProblem("A.md: links to bundled 'B.md'")

    def test_long_reference_needs_contents_but_skill_md_and_templates_dont(self):
        long = "x\n" * 101
        self.skill(body=long + "[R](R.md) [t](assets/t-template.md)\n", files={"R.md": long, "assets/t-template.md": long})
        self.assertEqual([p for p in self.problems() if "Contents" in p],
                         ["skills/engineering/a/R.md: over 100 lines without a '## Contents' list"])

    def test_templates_sit_in_assets(self):
        self.skill(body="[a](a-template.md) [b](assets/b-template.md)\n",
                   files={"a-template.md": "x\n", "assets/b-template.md": "x\n"})
        self.assertEqual([p for p in self.problems() if "template" in p],
                         ["skills/engineering/a/a-template.md: output template outside assets/"])

    def bare_script_problems(self, body, reference=None):
        files = {"scripts/x.sh": "#!/bin/sh\n# --help\n"}
        if reference is not None:
            files["references/r.md"] = reference
        folder = self.skill(body="Run [x](scripts/x.sh), see [r](references/r.md).\n\n" + body, files=files)
        (folder / "scripts/x.sh").chmod(0o755)
        return [p.split(": ")[0] for p in self.problems() if "skill-dir" in p]

    def test_code_blocks_run_bundled_scripts_by_skill_dir(self):
        flagged = {
            "bare": "```bash\nscripts/x.sh 7\n```\n",
            "after a command": "```bash\nbash scripts/x.sh\n```\n",
            "dot-slash": "```bash\n./scripts/x.sh\n```\n",
            "tilde fence": "~~~bash\nscripts/x.sh\n~~~\n",
            "indented in a list": "1. Run:\n\n   ```bash\n   scripts/x.sh\n   ```\n",
            "inside a 4-backtick wrapper": "````markdown\n```bash\nscripts/x.sh\n```\n````\n",
            "after a block holding a fence with an info string": ("```text\nexample:\n```bash\n```\n\nprose\n\n"
                                                                  "```bash\nscripts/x.sh\n```\n"),
        }
        for case, body in flagged.items():
            with self.subTest(case):
                self.setUp()
                self.assertEqual(self.bare_script_problems(body, reference=""), ["skills/engineering/a/SKILL.md"])

    def test_skill_dir_prose_and_other_scripts_arent_flagged(self):
        body = ("Run scripts/x.sh, or `scripts/x.sh` inline.\n\n```bash\n<skill-dir>/scripts/x.sh 7\n"
                "\"$SKILL_DIR/scripts/x.sh\"\npython3 scripts/other.py\n```\n")
        self.assertEqual(self.bare_script_problems(body, reference=""), [])

    def test_bundled_markdown_is_checked_too(self):
        self.assertEqual(self.bare_script_problems("", reference="```bash\nscripts/x.sh\n```\n"),
                         ["skills/engineering/a/references/r.md"])

    def test_scripts_and_evals_named_template_arent_output_templates(self):
        folder = self.skill(body="Run scripts/render-template.sh.\n",
                            files={"scripts/render-template.sh": "#!/bin/sh\n# --help\n",
                                   "evals/template-input.md": "x\n"})
        (folder / "scripts/render-template.sh").chmod(0o755)
        self.assertEqual(self.problems(), [])

    def test_frontmatter_rules(self):
        cases = {
            "no YAML frontmatter": None,
            "disable-model-invocation is 'yes'": GOOD + "\ndisable-model-invocation: yes",
            "over 1024": "name: {name}\ndescription: Use when " + "x" * 1024,
            "contains an XML tag": "name: {name}\ndescription: Use when <b>asked</b>.",
        }
        for fragment, frontmatter in cases.items():
            with self.subTest(fragment):
                self.setUp()
                folder = self.skill(frontmatter=frontmatter or GOOD)
                if frontmatter is None:
                    (folder / "SKILL.md").write_text("Body.\n")
                self.assertProblem(fragment)

    def test_body_over_500_lines(self):
        self.skill(body="x\n" * 500)
        self.assertProblem("body is 500 lines")

    def test_windows_paths_and_dates_in_any_instruction_file(self):
        self.skill(body="Run scripts\\x.sh. See [R](R.md).\n",
                   files={"R.md": "Use it until March 2026.\n", "CREDITS.md": "Before May 2025, scripts\\y.\n"})
        self.assertProblem("SKILL.md: Windows-style path")
        self.assertProblem("R.md: time-sensitive instruction")
        self.assertFalse([p for p in self.problems() if "CREDITS.md" in p])

    def test_bundled_script_rules(self):
        folder = self.skill(body="Run scripts/ok.sh and scripts/bad.py.\n", files={
            "scripts/ok.sh": "#!/usr/bin/env bash\n# --help prints this\n",
            "scripts/bad.py": "x = input('Name? ')\n"})
        (folder / "scripts/ok.sh").chmod(0o755)
        problems = [p.split(": ", 1)[1] for p in self.problems() if "bad.py" in p]
        self.assertEqual(problems, ["bundled script has no shebang", "bundled script isn't executable",
                                    "bundled script doesn't answer --help",
                                    "bundled script prompts for input; take it from flags, env or stdin"])
        self.assertFalse([p for p in self.problems() if "ok.sh" in p])

    def test_binary_file_in_scripts_is_reported_not_a_crash(self):
        folder = self.skill(body="Run scripts/.DS_Store.\n")
        (folder / "scripts").mkdir()
        (folder / "scripts/.DS_Store").write_bytes(b"\x00\xff\xfe")
        self.assertProblem("bundled script isn't text")

    def test_shared_trigger_between_model_invoked_skills(self):
        self.skill("a", 'name: a\ndescription: Use when the user says "ship it".')
        self.skill("b", 'name: b\ndescription: Use when the user says "Ship it".')
        self.assertProblem('trigger "Ship it" is in both a and b')


if __name__ == "__main__":
    unittest.main()
