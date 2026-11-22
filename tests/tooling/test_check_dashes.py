"""Tests for scripts/check-dashes.py as a command.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

EM, EN = chr(0x2014), chr(0x2013)

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check-dashes.py"


class CheckDashesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def run_on(self, *names):
        return subprocess.run([sys.executable, str(SCRIPT), *names], cwd=self.dir,
                              capture_output=True, text=True, check=False)

    def test_reports_each_dash_with_its_position(self):
        (self.dir / "a.md").write_text(f"fine\nan aside {EM} here, pages 1{EN}5\n", encoding="utf-8")
        out = self.run_on("a.md")
        self.assertEqual(out.returncode, 1)
        self.assertEqual(out.stdout.splitlines(), ["a.md:2:10: em dash", "a.md:2:25: en dash"])

    def test_clean_binary_and_missing_files_pass(self):
        (self.dir / "a.md").write_text("a hyphen - and a range 1-5\n", encoding="utf-8")
        (self.dir / "b.png").write_bytes(b"\x89PNG\xff\xfe\x80")
        out = self.run_on("a.md", "b.png", "gone.md")
        self.assertEqual((out.returncode, out.stdout.strip()), (0, "ok"))

    def test_no_arguments_checks_every_tracked_file(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        (self.dir / "tracked.md").write_text(f"x {EM} y\n", encoding="utf-8")
        (self.dir / "untracked.md").write_text(f"x {EM} y\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.md"], cwd=self.dir, check=True)
        out = self.run_on()
        self.assertEqual(out.stdout.splitlines(), ["tracked.md:1:3: em dash"])


if __name__ == "__main__":
    unittest.main()
