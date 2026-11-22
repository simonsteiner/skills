"""Tests for scripts/sync-third-party.py as a command, and for the GitHub adapter behind --outdated.

The command runs against the repo's real third-party/skills.json with HOME at a throwaway
directory (no lock file, nothing installed). The adapter, third_party.github_folders, runs
with the network (urllib.request.urlopen) replaced and the fake gh first on PATH.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tooling import third_party

from tests.skill_scripts.fake_gh import FakeGh

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "sync-third-party.py"


class SyncThirdPartyCommandTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = tmp.name

    def run_command(self, *args):
        env = {**os.environ, "HOME": self.home}
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              env=env, check=False)

    def test_an_unknown_argument_exits_2_and_names_it(self):
        out = self.run_command("--bogus")
        self.assertEqual(out.returncode, 2)
        self.assertIn("unknown argument '--bogus'", out.stderr)

    def test_two_arguments_exit_2_with_expected_at_most_one(self):
        out = self.run_command("--check", "--list")
        self.assertEqual(out.returncode, 2)
        self.assertIn("expected at most one argument, got: --check --list", out.stderr)

    def test_check_without_a_lock_file_exits_1_and_says_to_run_without_check(self):
        out = self.run_command("--check")
        self.assertEqual(out.returncode, 1)
        self.assertIn("Run without --check", out.stderr)

    def test_outdated_without_a_lock_file_exits_1(self):
        out = self.run_command("--outdated")
        self.assertEqual(out.returncode, 1)
        self.assertIn("no skills.sh lock file", out.stderr)

    def test_list_prints_one_line_per_curated_skill_and_exits_0(self):
        manifest = json.loads((REPO / "third-party" / "skills.json").read_text())
        names = [k["name"] for s in manifest["sources"] for k in s["skills"]]
        out = self.run_command("--list")
        self.assertEqual(out.returncode, 0, out.stderr)
        listed = [line.split()[0] for line in out.stdout.splitlines() if line.startswith("  ")]
        for name in names:
            self.assertIn(name, listed)
        self.assertGreater(len(names), 0)


def tree(**extra):
    return {"sha": "root", "tree": [{"path": "skills/a", "type": "tree", "sha": "sa"},
                                    {"path": "skills/a/SKILL.md", "type": "blob", "sha": "blob"}], **extra}


class GithubFoldersTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        env = mock.patch.dict(os.environ, {"PATH": self.gh.path})
        env.start()
        self.addCleanup(env.stop)
        for name in ("GH_TOKEN", "GITHUB_TOKEN"):
            os.environ.pop(name, None)
        self.requests = []

    def folders(self, answer=None, **kwargs):
        # Library calls reach gh through PATH, so write the rules and point the shim at them.
        self.gh.spec.write_text(json.dumps(self.gh.rules))
        os.environ.update(FAKE_GH_RULES=str(self.gh.spec), FAKE_GH_LOG=str(self.gh.log))
        def urlopen(request, timeout=None):
            self.requests.append(request)
            return io.BytesIO(json.dumps(answer if answer is not None else tree(**kwargs)).encode())
        with mock.patch("urllib.request.urlopen", urlopen):
            return third_party.github_folders("o/r")

    def authorization(self):
        return self.requests[-1].get_header("Authorization")

    def test_returns_the_root_and_every_folder_sha(self):
        self.assertEqual(self.folders(), {"": "root", "skills/a": "sa"})

    def test_gh_token_wins_over_github_token_and_the_gh_login(self):
        os.environ.update(GH_TOKEN="from-gh-token", GITHUB_TOKEN="from-github-token")
        self.gh.on("auth", "token", stdout="from-login\n")
        self.folders()
        self.assertEqual(self.authorization(), "Bearer from-gh-token")

    def test_github_token_is_used_when_gh_token_is_unset(self):
        os.environ["GITHUB_TOKEN"] = "from-github-token"
        self.gh.on("auth", "token", stdout="from-login\n")
        self.folders()
        self.assertEqual(self.authorization(), "Bearer from-github-token")

    def test_the_gh_login_is_used_when_no_token_variable_is_set(self):
        self.gh.on("auth", "token", stdout="from-login\n")
        self.folders()
        self.assertEqual(self.authorization(), "Bearer from-login")

    def test_a_logged_out_gh_sends_no_authorization_header(self):
        self.gh.on("auth", "token", stdout="not-a-token\n", exit=1)
        self.folders()
        self.assertIsNone(self.authorization())

    def test_a_missing_gh_sends_no_authorization_header(self):
        with tempfile.TemporaryDirectory() as empty:
            os.environ["PATH"] = empty
            self.folders()
        self.assertIsNone(self.authorization())

    def test_a_truncated_tree_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "incomplete tree"):
            self.folders(truncated=True)

    def test_an_answer_without_a_tree_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "incomplete tree"):
            self.folders(answer={"message": "Not Found"})


if __name__ == "__main__":
    unittest.main()
