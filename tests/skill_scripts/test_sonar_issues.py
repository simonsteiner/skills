"""Tests for skills/engineering/review-prs/scripts/sonar-issues.sh, through a fake curl.

    python3 -m unittest discover -s tests -t .
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/review-prs/scripts/sonar-issues.sh"

# Answers from FAKE_CURL_PAGES (one JSON page per `p=`), logs argv, fails on an unknown page.
FAKE_CURL = r'''
import json, os, sys
argv = sys.argv[1:]
with open(os.environ["FAKE_CURL_LOG"], "a") as log:
    log.write(json.dumps(argv) + "\n")
pages = json.load(open(os.environ["FAKE_CURL_PAGES"]))
page = next(a[2:] for a in argv if a.startswith("p="))
if page not in pages:
    sys.stderr.write("curl: (22) The requested URL returned error: 400\n")
    sys.exit(22)
sys.stdout.write(json.dumps(pages[page]))
'''


def issue(n, project="acme_web"):
    return {"key": f"AX{n}", "rule": "java:S2259", "severity": "MAJOR", "type": "BUG",
            "component": f"{project}:src/F{n}.java", "line": n, "message": f"null #{n}", "status": "OPEN"}


class SonarIssuesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        (self.dir / "bin").mkdir()
        (self.dir / "fake_curl.py").write_text(FAKE_CURL)
        shim = self.dir / "bin" / "curl"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -I "{self.dir / "fake_curl.py"}" "$@"\n')
        shim.chmod(0o755)
        self.log = self.dir / "calls.jsonl"

    def run_with(self, pages, *args):
        (self.dir / "pages.json").write_text(json.dumps(pages))
        self.log.write_text("")
        env = {**os.environ, "PATH": f"{self.dir / 'bin'}{os.pathsep}{os.environ['PATH']}",
               "FAKE_CURL_PAGES": str(self.dir / "pages.json"), "FAKE_CURL_LOG": str(self.log)}
        return subprocess.run([str(SCRIPT), *args], capture_output=True, text=True, env=env, check=False)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_prints_one_line_per_issue_with_the_path_inside_the_project(self):
        result = self.run_with({"1": {"paging": {"pageIndex": 1, "pageSize": 500, "total": 1}, "issues": [issue(7)]}},
                               "acme_web", "41")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"rule": "java:S2259", "severity": "MAJOR", "type": "BUG",
                                                     "path": "src/F7.java", "line": 7, "message": "null #7"})
        [argv] = self.calls()
        for arg in ("componentKeys=acme_web", "pullRequest=41", "resolved=false", "ps=500", "p=1"):
            self.assertIn(arg, argv)

    def test_strips_a_project_key_that_holds_colons(self):
        page = {"paging": {"total": 1}, "issues": [issue(3, project="com.acme:web")]}
        result = self.run_with({"1": page}, "com.acme:web", "41")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["path"], "src/F3.java")

    def test_pages_on_until_the_total_is_read(self):
        pages = {"1": {"paging": {"total": 3}, "issues": [issue(1), issue(2)]},
                 "2": {"paging": {"total": 3}, "issues": [issue(3)]}}
        result = self.run_with(pages, "acme_web", "41")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([json.loads(line)["line"] for line in result.stdout.splitlines()], [1, 2, 3])
        self.assertEqual(len(self.calls()), 2)

    def test_no_issues_prints_nothing(self):
        result = self.run_with({"1": {"paging": {"total": 0}, "issues": []}}, "acme_web", "41")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_a_failed_request_exits_1(self):
        result = self.run_with({}, "private_proj", "41")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SonarCloud request failed", result.stderr)

    def test_needs_both_arguments(self):
        result = self.run_with({}, "acme_web")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
