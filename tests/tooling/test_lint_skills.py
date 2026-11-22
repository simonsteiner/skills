"""Tests for scripts/lint-skills.py as a command.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.tooling.skill_repo import SkillRepoTest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "lint-skills.py"


class LintSkillsCommandTest(unittest.TestCase):
    def test_runs_from_outside_the_repo_without_ruamel(self):
        # -S hides site-packages, so ruamel.yaml can't be imported and the script must
        # re-execute itself through the repo's uv project, whatever the current directory.
        env = {k: v for k, v in os.environ.items() if k != "LINT_SKILLS_REEXEC"}
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.run([sys.executable, "-S", str(SCRIPT)], cwd=tmp, env=env,
                                 capture_output=True, text=True, check=False)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(out.stdout.strip(), "ok")


class LintSkillsMainTest(SkillRepoTest):
    def lint(self):
        spec = importlib.util.spec_from_file_location("lint_skills", SCRIPT)
        lint_skills = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint_skills)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = lint_skills.main(self.repo)
        return status, out.getvalue()

    def test_a_broken_repo_prints_its_problems_and_exits_1(self):
        self.skill(frontmatter="name: {name}\ndescription: Does it.")
        status, out = self.lint()
        self.assertEqual(status, 1)
        self.assertIn("skills/engineering/a", out)
        self.assertNotEqual(out.strip(), "ok")


if __name__ == "__main__":
    unittest.main()
