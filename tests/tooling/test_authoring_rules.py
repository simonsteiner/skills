"""Tests for authoring_rules.py, against throwaway repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import tempfile
import time
import unittest
from pathlib import Path

from tooling.authoring_rules import UNPINNED, check
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
                        "`pipx run 'black==24.10.0'`, `npx @scope/tool@1.2`, `npx prettier@latest .`, `npx -- jest`.\n\n"
                        "In prose uvx is handy.\n\n```bash\nbunx tsc --noEmit\n```\n")
        self.assertEqual([p.split("command for ")[1].split(";")[0] for p in self.problems() if "unpinned" in p],
                         ["'eslint'", "'prettier@latest'", "'jest'", "'tsc'"])

    def test_unpinned_pattern_stays_linear_on_a_long_run_of_flags(self):
        # each `--x` used to split two ways (`-` + `-x` or `--` + `x`): 2^n tries on a miss
        started = time.monotonic()
        self.assertIsNone(UNPINNED.search("npx " + "--ab " * 40 + "!"))
        self.assertLess(time.monotonic() - started, 1)

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

    def test_metadata_field_is_not_allowed(self):
        expected = ("skills/engineering/a/SKILL.md: metadata isn't allowed in owned skills "
                    "(put credits in CREDITS.md, version in plugin.json)")
        for case, fm in {
            "flat map": GOOD + '\nmetadata:\n  author: example-org\n  version: "1.0"',
            "nested": GOOD + "\nmetadata:\n  credits:\n    - skill: x",
            "empty": GOOD + "\nmetadata:\nlicense: MIT",
        }.items():
            with self.subTest(case):
                self.setUp()
                self.skill("a", fm)
                self.assertEqual(self.problems(), [expected])

    def test_invalid_yaml_frontmatter_is_rejected(self):
        bad = {
            "colon-space in description": "name: a\ndescription: Use when: the user asks.",
            "trailing colon": "name: a\ndescription: Use when asked:",
            "colon-space in compatibility": GOOD + "\ncompatibility: Requires git: 2.30+",
            "folded plain continuation": "name: a\ndescription: Does it.\n  Use when: the user asks.",
            "comment then indented plain": "name: a\ndescription: # draft\n  Does it.\n  Use when: the user asks.",
            "leading quoted phrase then colon": 'name: a\ndescription: "Ship it" helper: Use when the user asks.',
            "unclosed quote": 'name: a\ndescription: "Use when asked.',
            "duplicate key": "name: a\nname: a\ndescription: Use when asked.",
            "tab indentation": "name: a\ndescription:\n\tUse when asked.",
            "list frontmatter": "- a\n- b",
            "empty frontmatter": "",
        }
        for case, fm in bad.items():
            with self.subTest(case):
                self.setUp()
                self.skill("a", fm)
                self.assertProblem("invalid YAML frontmatter")

    def test_valid_yaml_frontmatter_shapes_are_allowed(self):
        ok = {
            "double-quoted": 'name: a\ndescription: "Use when: the user asks."',
            "double-quoted with comment": 'name: a\ndescription: "Use when: the user asks." # note: keep short',
            "escaped quotes": 'name: a\ndescription: "Use when the user says \\"ship it\\"."',
            "single-quoted": "name: a\ndescription: 'Use when: the user asks.'",
            "indented quoted": 'name: a\ndescription:\n  "Use when: the user asks."',
            "folded block": "name: a\ndescription: >\n  Use when: the user asks.",
            "folded keep block": "name: a\ndescription: >+\n  Use when: the user asks.",
            "indented block indicator": "name: a\ndescription:\n  >\n  Use when: the user asks.",
            "literal block": "name: a\ndescription: |-\n  Use when: the user asks.",
            "url": "name: a\ndescription: See https://example.com when asked.",
            "trailing comment": "name: a\ndescription: Use when asked. # note: keep short",
            "license with comment": GOOD + "\nlicense: MIT # note: optional",
            "allowed-tools": GOOD + "\nallowed-tools: Read Grep",
        }
        for case, fm in ok.items():
            with self.subTest(case):
                self.setUp()
                self.skill("a", fm)
                self.assertEqual(self.problems(), [])

    def test_unknown_frontmatter_fields_are_rejected(self):
        for case, extra in {
            "typo in disable-model-invocation": "disable-model-invocaton: true",
            "typo in compatibility": "compatability: git",
            "arbitrary extension": "argument-hint: <file>",
        }.items():
            with self.subTest(case):
                self.setUp()
                self.skill("a", GOOD + "\n" + extra)
                self.assertProblem("unknown frontmatter field")

    def test_frontmatter_field_types_are_checked(self):
        cases = {
            "yaml 1.2 yes string": (GOOD + "\ndisable-model-invocation: yes", "disable-model-invocation is 'yes'"),
            "quoted boolean": (GOOD + '\ndisable-model-invocation: "true"', "disable-model-invocation is 'true'"),
            "mapping description": ("name: a\ndescription:\n  Use when: the user asks.", "description must be a string"),
            "list description": ("name: a\ndescription:\n  - a\n  - b", "description must be a string"),
            "numeric name": ("name: 123\ndescription: Use when asked.", "name must be a string"),
            "null license": (GOOD + "\nlicense: # note: optional", "license must be a non-empty string"),
            "empty allowed-tools": (GOOD + '\nallowed-tools: "   "', "allowed-tools must be a non-empty string"),
            "numeric compatibility": (GOOD + "\ncompatibility: 42", "compatibility must be 1-500 chars"),
        }
        for case, (fm, fragment) in cases.items():
            with self.subTest(case):
                self.setUp()
                self.skill("a", fm)
                self.assertProblem(fragment)

    def test_description_vague_phrases_and_routing_labels(self):
        for case, desc, fragment in (
            ("helps with", "Helps with git commits when asked.", 'vague description phrase "helps with"'),
            ("various", "Handles various git tasks when asked.", 'vague description phrase "various"'),
            ("general purpose", "General purpose helper when asked.", 'vague description phrase "general purpose"'),
            ("triggers on label", 'Does it. Triggers on: when asked.', "routing label 'Triggers on:'"),
            ("use cases label", 'Does it. Use cases: when asked.', "routing label 'Use cases:'"),
        ):
            with self.subTest(case):
                self.setUp()
                self.skill("a", f"name: a\ndescription: >\n  {desc}")
                self.assertProblem(fragment)

    def test_bundled_python_scripts_must_be_stdlib_only_unless_pep723(self):
        folder = self.skill(
            body=("Run scripts/ok.py, scripts/helper.py, scripts/pep.py, scripts/pep_no_deps.py, "
                  "scripts/pep_unclosed.py, scripts/bad.py, scripts/broken.py.\n"),
            files={
                "scripts/helper.py": "#!/usr/bin/env python3\n# --help\nimport json\n",
                "scripts/ok.py": "#!/usr/bin/env python3\n# --help\nimport json\nimport helper\n",
                "scripts/pep.py": "#!/usr/bin/env -S uv run --script\n# /// script\n# dependencies = [\n#   \"requests\",\n# ]\n# ///\n# --help\nimport requests\n",
                "scripts/pep_no_deps.py": "#!/usr/bin/env -S uv run --script\n# /// script\n# requires-python = \">=3.11\"\n# ///\n# --help\nimport requests\n",
                "scripts/pep_unclosed.py": "#!/usr/bin/env -S uv run --script\n# /// script\n# dependencies = [\"requests\"]\n# --help\nimport requests\n",
                "scripts/bad.py": "#!/usr/bin/env python3\n# --help\nimport requests\nfrom yaml import safe_load\n",
                "scripts/broken.py": "#!/usr/bin/env python3\n# --help\ndef nope(:\n",
            },
        )
        for name in ("helper.py", "ok.py", "pep.py", "pep_no_deps.py", "pep_unclosed.py", "bad.py", "broken.py"):
            (folder / "scripts" / name).chmod(0o755)
        problems = self.problems()
        self.assertEqual(
            [p.split(": ", 1)[1] for p in problems if "bad.py" in p],
            [
                "bundled Python script imports non-stdlib module 'requests' without PEP 723 dependencies",
                "bundled Python script imports non-stdlib module 'yaml' without PEP 723 dependencies",
            ],
        )
        for bad_pep in ("pep_no_deps.py", "pep_unclosed.py"):
            self.assertEqual(
                [p.split(": ", 1)[1] for p in problems if bad_pep in p],
                ["bundled Python script imports non-stdlib module 'requests' without PEP 723 dependencies"],
                bad_pep,
            )
        self.assertTrue(any("broken.py: bundled Python script has a syntax error" in p for p in problems), problems)
        for clean in ("helper.py", "ok.py", "pep.py"):
            self.assertFalse([p for p in problems if clean in p], problems)

    def test_an_import_error_fallback_is_optional_not_a_dependency(self):
        folder = self.skill(
            body="Run scripts/toml.py, scripts/tuple.py, scripts/wrong.py.\n",
            files={
                "scripts/toml.py": ("#!/usr/bin/env python3\n# --help\ntry:\n    import tomllib\n"
                                    "except ImportError:\n    import tomli as tomllib\n"),
                "scripts/tuple.py": ("#!/usr/bin/env python3\n# --help\ntry:\n    import tomllib\n"
                                     "except (OSError, ModuleNotFoundError):\n    from tomli import loads\n"),
                # only the fallback is optional: a third-party first choice is still a dependency,
                # and a handler that doesn't catch ImportError isn't a fallback
                "scripts/wrong.py": ("#!/usr/bin/env python3\n# --help\ntry:\n    import yaml\n"
                                     "except ImportError:\n    import json\ntry:\n    pass\n"
                                     "except ValueError:\n    import tomli\n"),
            },
        )
        for name in ("toml.py", "tuple.py", "wrong.py"):
            (folder / "scripts" / name).chmod(0o755)
        problems = self.problems()
        self.assertEqual(
            [p.split(": ", 1)[1] for p in problems if "wrong.py" in p],
            [
                "bundled Python script imports non-stdlib module 'tomli' without PEP 723 dependencies",
                "bundled Python script imports non-stdlib module 'yaml' without PEP 723 dependencies",
            ],
        )
        self.assertFalse([p for p in problems if "toml.py" in p or "tuple.py" in p], problems)

    def test_a_pep723_script_needs_a_uv_run_script_shebang(self):
        block = "# /// script\n# dependencies = [\"requests\"]\n# ///\n# --help\nimport requests\n"
        folder = self.skill(
            body="Run scripts/uv.py, scripts/uv_flags.py, scripts/python.py, scripts/uv_no_script.py.\n",
            files={
                "scripts/uv.py": "#!/usr/bin/env -S uv run --script\n" + block,
                "scripts/uv_flags.py": "#!/usr/bin/env -S uv run --quiet --script\n" + block,
                "scripts/python.py": "#!/usr/bin/env python3\n" + block,
                "scripts/uv_no_script.py": "#!/usr/bin/env -S uv run python3\n" + block,
            },
        )
        for name in ("uv.py", "uv_flags.py", "python.py", "uv_no_script.py"):
            (folder / "scripts" / name).chmod(0o755)
        problems = self.problems()
        for bad in ("python.py", "uv_no_script.py"):
            self.assertEqual(
                [p.split(": ", 1)[1] for p in problems if f"/{bad}" in p],
                ["bundled Python script has a PEP 723 block but no `uv run --script` shebang"],
                bad,
            )
        self.assertFalse([p for p in problems if "/uv.py" in p or "uv_flags.py" in p], problems)

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

    def test_invalid_evals_are_reported_against_evals_json(self):
        self.skill(files={"evals/evals.json": '{"skills": ["a"], "evals": []}'})
        self.assertEqual(self.problems(), ['skills/engineering/a/evals/evals.json: "evals" must be a non-empty list'])

    def test_shared_trigger_between_model_invoked_skills(self):
        self.skill("a", 'name: a\ndescription: Use when the user says "ship it".')
        self.skill("b", 'name: b\ndescription: Use when the user says "Ship it".')
        self.assertProblem('trigger "Ship it" is in both a and b')


    def test_a_skill_tool_call_cannot_name_a_user_invoked_skill(self):
        self.skill("typed", "name: typed\ndescription: Does it.\ndisable-model-invocation: true")
        self.skill("other", body='Call the Skill tool with "typed".\nTell the user to run `/typed`.\n')
        self.assertEqual(self.problems(), [
            ("skills/engineering/other/SKILL.md:5: calls the user-invoked typed through the Skill tool, "
             "which can't reach it; tell the user to run `/typed` instead")])

    def test_a_skill_tool_call_may_name_a_model_invoked_skill(self):
        self.skill("reached")
        self.skill("other", body='Call the Skill tool twice, for "reached" and "grilling".\n')
        self.assertEqual(self.problems(), [])

    def test_tests_beside_the_code_fail(self):
        self.skill(files={"scripts/test_x.py": "", "scripts/y.test.ts": ""})
        (self.repo / "scripts/tooling").mkdir(parents=True)
        (self.repo / "scripts/tooling/z_test.py").write_text("")
        self.assertEqual([p for p in self.problems() if "tests live" in p], [
            "skills/engineering/a/scripts/test_x.py: tests live in tests/, never beside the code",
            "skills/engineering/a/scripts/y.test.ts: tests live in tests/, never beside the code",
            "scripts/tooling/z_test.py: tests live in tests/, never beside the code",
        ])

if __name__ == "__main__":
    unittest.main()
