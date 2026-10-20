"""Tests for skills/engineering/setup-lefthook/scripts/check-file-tokens.py, against throwaway repos.

    python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/engineering/setup-lefthook/scripts/check-file-tokens.py"
# What the lefthook remote (lefthook/file-tokens.yml) ships to other repos.
REMOTE_COPY = ROOT / ".lefthook/pre-commit/check-file-tokens.py"

# A git hook running the suite exports GIT_DIR, GIT_INDEX_FILE, …; they'd point every call at the outer repo.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

LIMIT = 100  # tokens, so 400 bytes
BIG = "x = 1\n" * 100  # 600 bytes, 150 tokens
SMALL = "x = 1\n" * 10


class CheckFileTokensTest(unittest.TestCase):
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

    def run_script(self, *paths, limit=LIMIT):
        return subprocess.run([str(SCRIPT), "--max-tokens", str(limit), *paths], cwd=self.repo, env=ENV,
                              capture_output=True, text=True, check=False)

    def test_files_under_the_limit_pass(self):
        self.stage("a.py", SMALL)
        result = self.run_script("a.py")
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_no_files_pass(self):
        self.assertEqual(self.run_script().returncode, 0)

    def test_a_file_over_the_limit_fails_with_split_instructions(self):
        self.stage("src/big.py", BIG)
        self.stage("a.py", SMALL)
        result = self.run_script("src/big.py", "a.py")
        self.assertEqual(result.returncode, 1)
        self.assertIn("src/big.py", result.stderr)
        self.assertNotIn("a.py ", result.stderr)
        self.assertIn("150 tokens", result.stderr)
        self.assertIn("50 over; split into 2+ files", result.stderr)
        self.assertIn("Find the seams", result.stderr)
        self.assertIn("--no-verify", result.stderr)

    def test_exactly_the_limit_passes(self):
        self.stage("a.py", "x" * LIMIT * 4)
        self.assertEqual(self.run_script("a.py").returncode, 0)
        self.stage("a.py", "x" * (LIMIT * 4 + 1))
        self.assertEqual(self.run_script("a.py").returncode, 1)

    def test_measures_the_staged_content_not_the_working_tree(self):
        self.stage("a.py", BIG)
        (self.repo / "a.py").write_text(SMALL)
        self.assertEqual(self.run_script("a.py").returncode, 1)
        self.stage("a.py", SMALL)
        (self.repo / "a.py").write_text(BIG)
        self.assertEqual(self.run_script("a.py").returncode, 0)

    def test_lockfiles_and_build_output_are_skipped(self):
        for path in ("package-lock.json", "web/pnpm-lock.yaml", "uv.lock", "Cargo.lock", "go.sum",
                     "dist/app.min.js", "dist/app.js.map", "tests/__snapshots__/a.test.ts.snap"):
            with self.subTest(path=path):
                self.stage(path, BIG)
                self.assertEqual(self.run_script(path).returncode, 0)

    def test_binary_files_are_skipped(self):
        self.stage("logo.png", b"\x89PNG\0" + b"x" * 1000)
        self.assertEqual(self.run_script("logo.png").returncode, 0)

    def test_a_pdf_without_a_nul_up_front_is_skipped(self):
        self.stage("reports/a.pdf", b"%PDF-1.4\n%\x93\x8c\x8b\x9e\n" + b"x" * 1000)
        self.assertEqual(self.run_script("reports/a.pdf").returncode, 0)

    def test_utf8_text_cut_mid_character_at_the_sniff_limit_is_still_text(self):
        self.stage("notes.md", "x" * 7999 + "é" * 1000)  # é is 2 bytes; the cut at 8000 splits one
        self.assertEqual(self.run_script("notes.md").returncode, 1)

    def test_data_files_are_skipped(self):
        for path in ("data/results.csv", "data/table.tsv", "map/cantons.geojson", "logs/events.jsonl", "tracks/a.GPX"):
            with self.subTest(path=path):
                self.stage(path, BIG)
                self.assertEqual(self.run_script(path).returncode, 0)

    def test_vendor_folders_are_skipped(self):
        for path in ("vendor/lib.js", "web/third_party/x/y.c", "static/bower_components/jq.js"):
            with self.subTest(path=path):
                self.stage(path, BIG)
                self.assertEqual(self.run_script(path).returncode, 0)

    def test_a_file_merely_named_vendor_is_checked(self):
        self.stage("src/vendor.py", BIG)
        self.assertEqual(self.run_script("src/vendor.py").returncode, 1)

    def test_files_with_a_generated_header_are_skipped(self):
        for header in ("// Code generated by protoc-gen-go. DO NOT EDIT.", "# @generated by sqlc",
                       "/* auto-generated from schema.json */", "# Generated by Django 5.0 on 2026-01-01",
                       "// This file was automatically generated. DO NOT EDIT.",
                       "/**\n * This file is auto-generated by openapi-typescript.\n */"):
            with self.subTest(header=header):
                self.stage("gen.go", f"{header}\n{BIG}")
                self.assertEqual(self.run_script("gen.go").returncode, 0)

    def test_a_markdown_html_comment_header_is_skipped(self):
        self.stage("docs/api.md", f"<!-- DO NOT EDIT: generated by typedoc -->\n{BIG}")
        self.assertEqual(self.run_script("docs/api.md").returncode, 0)

    def test_prose_mentioning_generated_code_does_not_skip(self):
        for path, header in (("README.md", "# Client\n\nThe client in src/client is auto-generated from openapi.yaml."),
                             ("README.md", "# Auto-generated clients"),
                             ("app.py", '"""Wraps the auto-generated client; do not edit it by hand."""'),
                             ("client.ts", "// Wraps the auto-generated OpenAPI client with retries and auth."),
                             ("app.py", "#!/usr/bin/env python3\n# Do not edit settings here; use config.toml.")):
            with self.subTest(path=path, header=header):
                self.stage(path, f"{header}\n{BIG}")
                self.assertEqual(self.run_script(path).returncode, 1)

    def test_a_marker_below_the_header_does_not_skip(self):
        self.stage("a.py", f"{BIG}# DO NOT EDIT this constant\n")
        self.assertEqual(self.run_script("a.py").returncode, 1)

    def test_gitattributes_marks_generated_and_vendored_files(self):
        self.stage(".gitattributes", "src/schema.ts linguist-generated\nvendor/** linguist-vendored\n")
        self.stage("src/schema.ts", BIG)
        self.stage("vendor/lib.js", BIG)
        self.stage("src/app.ts", BIG)
        result = self.run_script("src/schema.ts", "vendor/lib.js", "src/app.ts")
        self.assertEqual(result.returncode, 1)
        self.assertIn("src/app.ts", result.stderr)
        self.assertNotIn("schema.ts", result.stderr)
        self.assertNotIn("vendor/lib.js", result.stderr)

    def test_an_unset_attribute_does_not_skip(self):
        self.stage(".gitattributes", "*.ts linguist-generated\nsrc/app.ts -linguist-generated\n")
        self.stage("src/app.ts", BIG)
        self.assertEqual(self.run_script("src/app.ts").returncode, 1)

    def test_paths_with_spaces(self):
        self.stage("my docs/guide.md", BIG)
        result = self.run_script("my docs/guide.md")
        self.assertEqual(result.returncode, 1)
        self.assertIn("my docs/guide.md", result.stderr)

    def test_a_missing_path_is_ignored(self):
        self.assertEqual(self.run_script("gone.py").returncode, 0)

    def test_an_unstaged_file_is_not_read(self):
        (self.repo / "loose.py").write_text(BIG)
        self.assertEqual(self.run_script("loose.py").returncode, 0)

    def test_a_path_outside_the_repo_is_not_read(self):
        outside = self.repo.parent / f"{self.repo.name}-outside.py"
        outside.write_text(BIG)
        self.addCleanup(outside.unlink)
        for path in (f"../{outside.name}", str(outside)):
            with self.subTest(path=path):
                self.assertEqual(self.run_script(path).returncode, 0)

    def test_rejects_a_nonpositive_limit(self):
        self.assertEqual(self.run_script("a.py", limit=0).returncode, 2)



class RemoteCopyTest(unittest.TestCase):
    def test_the_remote_copy_matches_the_skill_script(self):
        # A regular file, not a symlink: a clone with core.symlinks=false (Git for Windows) checks a
        # symlink out as a text file holding its target, and python3 fails on it.
        self.assertFalse(REMOTE_COPY.is_symlink())
        self.assertEqual(REMOTE_COPY.read_bytes(), SCRIPT.read_bytes(), "copy the skill script to " + str(REMOTE_COPY))
        self.assertTrue(os.access(REMOTE_COPY, os.X_OK))


if __name__ == "__main__":
    unittest.main()
