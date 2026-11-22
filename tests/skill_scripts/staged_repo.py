"""A throwaway git repo to stage files in, for the setup-lefthook hook scripts' tests (not a test module itself)."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


class StagedRepoTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=ENV, capture_output=True, check=True)

    def stage(self, path, content):
        f = self.repo / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(content.encode() if isinstance(content, str) else content)
        self.git("add", path)
