"""Tests for script_rules.py, through authoring_rules.check() against throwaway repos.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import unittest

from tests.tooling.skill_repo import SkillRepoTest


class ScriptRulesTest(SkillRepoTest):
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


if __name__ == "__main__":
    unittest.main()
