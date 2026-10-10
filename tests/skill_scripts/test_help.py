"""Every script bundled in a skill answers --help without touching gh.

    python3 -m unittest discover -s tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPTS = sorted(p for p in (Path(__file__).resolve().parents[2] / "skills").glob("*/*/scripts/*")
                 if p.is_file() and not p.name.startswith("."))


class HelpTest(unittest.TestCase):
    def test_help_prints_usage_and_exits_0(self):
        self.assertTrue(SCRIPTS)
        for script in SCRIPTS:
            for flag in ("--help", "-h"):
                with self.subTest(script=script.name, flag=flag), tempfile.TemporaryDirectory() as tmp:
                    gh = FakeGh(tmp)
                    result = gh.run(script, flag)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(script.name, result.stdout)
                    self.assertEqual(gh.calls, [])


if __name__ == "__main__":
    unittest.main()
