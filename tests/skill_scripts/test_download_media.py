"""Tests for skills/engineering/download-media/scripts/download.sh, against a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/download-media/scripts/download.sh"
ASSET = "https://github.com/user-attachments/assets/82dd8a5f-3ccf-40f2-ac1b-26481e2a0220"
FILE = "https://github.com/user-attachments/files/123/report.pdf"
LEGACY = "https://user-images.githubusercontent.com/1/abc-def.png"
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>\n'


class DownloadTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name) / "out"
        self.gh = FakeGh(tmp.name)

    def lines(self, result):
        return [line.split("\t") for line in result.stdout.splitlines()]

    def test_pulls_attachment_urls_out_of_text_once_each_in_order(self):
        self.gh.on("api", ASSET, stdout=SVG).on("api", FILE, stdout="pdf").on("api", LEGACY, stdout="png")
        text = (f"![shot]({ASSET})\n<img src=\"{FILE}\"> and {LEGACY}, "
                f"not https://example.com/x.png, again {ASSET}\n")
        result = self.gh.run(SCRIPT, "-o", self.out, stdin=text)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lines(result), [
            [f"{self.out}/01-82dd8a5f-3ccf-40f2-ac1b-26481e2a0220.svg", ASSET],
            [f"{self.out}/02-report.pdf", FILE],
            [f"{self.out}/03-abc-def.png", LEGACY],
        ])
        self.assertEqual((self.out / "01-82dd8a5f-3ccf-40f2-ac1b-26481e2a0220.svg").read_text(), SVG)
        self.assertEqual([c["args"] for c in self.gh.calls], [["api", ASSET], ["api", FILE], ["api", LEGACY]])

    def test_a_non_attachment_url_is_refused_before_any_call(self):
        result = self.gh.run(SCRIPT, "-o", self.out, ASSET, "https://example.com/x.png")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a GitHub attachment URL", result.stderr)
        self.assertEqual(self.gh.calls, [])

    def test_a_failed_download_leaves_no_file_and_the_rest_still_run(self):
        self.gh.on("api", ASSET, exit=1).on("api", FILE, stdout="pdf")
        result = self.gh.run(SCRIPT, "-o", self.out, ASSET, FILE)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"download failed: {ASSET}", result.stderr)
        self.assertEqual(self.lines(result), [[f"{self.out}/02-report.pdf", FILE]])
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ["02-report.pdf"])

    def test_text_without_attachments_is_not_an_error(self):
        result = self.gh.run(SCRIPT, stdin="no media here\n")
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertEqual(self.gh.calls, [])

    def test_defaults_to_a_new_temp_folder(self):
        self.gh.on("api", FILE, stdout="pdf")
        result = self.gh.run(SCRIPT, FILE, env={"TMPDIR": str(self.out.parent)})
        self.assertEqual(result.returncode, 0, result.stderr)
        path = Path(self.lines(result)[0][0])
        self.assertTrue(path.parent.name.startswith("gh-media."))
        self.assertEqual(path.read_text(), "pdf")

    def test_bad_usage_exits_2(self):
        for args in (("-o",), ("--force", ASSET)):
            with self.subTest(args=args):
                self.assertEqual(self.gh.run(SCRIPT, *args).returncode, 2)
                self.assertEqual(self.gh.calls, [])


if __name__ == "__main__":
    unittest.main()
