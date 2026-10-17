"""Tests for skills/engineering/attach-media/scripts/upload.sh, against a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/attach-media/scripts/upload.sh"
UPLOAD = "https://uploads.github.com/user-attachments/assets?"


class UploadTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.gh = FakeGh(tmp.name)

    def file(self, name):
        path = self.dir / name
        path.write_text("bytes")
        return path

    def uploads(self):
        return [c["args"][3] for c in self.gh.calls if c["args"][:2] == ["api", "-X"]]

    def test_images_embed_and_videos_stay_bare_urls_in_argument_order(self):
        shot, clip = self.file("after shot.png"), self.file("demo.MOV")
        self.gh.on("api", "repos/{owner}/{repo}", json={"id": 42})
        self.gh.on("api", "-X", "POST", once=True, json={"url": "https://github.com/user-attachments/assets/a"})
        self.gh.on("api", "-X", "POST", once=True, json={"url": "https://github.com/user-attachments/assets/b"})
        result = self.gh.run(SCRIPT, shot, clip)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "![after shot.png](https://github.com/user-attachments/assets/a)\n"
                                        "https://github.com/user-attachments/assets/b\n")
        self.assertEqual(self.uploads(), [
            UPLOAD + "name=after%20shot.png&content_type=image%2Fpng&repository_id=42",
            UPLOAD + "name=demo.MOV&content_type=video%2Fquicktime&repository_id=42",
        ])
        self.assertIn(str(shot), self.gh.calls[1]["args"])  # the file itself is the body

    def test_repo_flag_names_the_target(self):
        self.gh.on("api", "repos/me/fork", json={"id": 7})
        self.gh.on("api", "-X", "POST", json={"url": "u"})
        result = self.gh.run(SCRIPT, "--repo", "me/fork", self.file("a.svg"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.uploads(), [UPLOAD + "name=a.svg&content_type=image%2Fsvg%2Bxml&repository_id=7"])

    def test_a_bad_file_anywhere_stops_before_any_call(self):
        for bad, error in ((self.file("notes.txt"), "unsupported type"), (self.dir / "gone.png", "no such file")):
            with self.subTest(bad=bad.name):
                result = self.gh.run(SCRIPT, self.file("ok.png"), bad)
                self.assertEqual(result.returncode, 1)
                self.assertIn(error, result.stderr)
                self.assertEqual(self.gh.calls, [])

    def test_a_rejected_upload_fails(self):
        self.gh.on("api", "repos/{owner}/{repo}", json={"id": 1})
        self.gh.on("api", "-X", "POST", exit=1)
        result = self.gh.run(SCRIPT, self.file("a.png"))
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("upload failed: ", result.stderr)

    def test_a_file_over_the_size_cap_stops_before_any_call(self):
        big = self.file("big.png")
        with big.open("r+b") as f:
            f.truncate(10 * 1024 * 1024 + 1)
        result = self.gh.run(SCRIPT, self.file("ok.png"), big)
        self.assertEqual(result.returncode, 1)
        self.assertIn("over GitHub's 10 MB limit", result.stderr)
        self.assertEqual(self.gh.calls, [])

    def test_a_later_failure_keeps_the_lines_already_uploaded(self):
        self.gh.on("api", "repos/{owner}/{repo}", json={"id": 1})
        self.gh.on("api", "-X", "POST", once=True, json={"url": "https://github.com/user-attachments/assets/a"})
        self.gh.on("api", "-X", "POST", exit=1)
        result = self.gh.run(SCRIPT, self.file("a.png"), self.file("b.png"))
        self.assertEqual((result.returncode, result.stdout), (1, "![a.png](https://github.com/user-attachments/assets/a)\n"))
        self.assertIn("upload failed: ", result.stderr)
        self.assertIn("b.png", result.stderr)

    def test_a_response_without_a_url_fails(self):
        self.gh.on("api", "repos/{owner}/{repo}", json={"id": 1})
        self.gh.on("api", "-X", "POST", stdout="")
        result = self.gh.run(SCRIPT, self.file("a.png"))
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("no URL in the response", result.stderr)

    def test_bad_usage_exits_2(self):
        for args in ((), ("--repo",), ("--repo", "", "a.png"), ("--repo", "--help"), ("--force", "a.png")):
            with self.subTest(args=args):
                self.assertEqual(self.gh.run(SCRIPT, *args).returncode, 2)
                self.assertEqual(self.gh.calls, [])


if __name__ == "__main__":
    unittest.main()
