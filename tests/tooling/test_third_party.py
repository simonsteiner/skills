"""Tests for third_party.py, against a throwaway home directory and manifest.

    python3 -m unittest discover -s tests -t .
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from tooling import third_party
from tooling.third_party import Home, check, install_commands, link, load, sync

MANIFEST = {
    "agents": ["claude-code"],
    "sources": [
        {"repo": "a/one", "why": "w", "agents": ["claude-code", "codex"],
         "skills": [{"name": "alpha", "why": "w"}],
         "archived": [{"name": "old", "why": "w"}]},
        {"repo": "b/two", "why": "w", "skills": [{"name": "beta", "why": "w"}]},
        {"repo": "c/none", "why": "w", "skills": [], "archived": [{"name": "gone", "why": "w"}]},
    ],
}


class ThirdPartyTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "repo/third-party").mkdir(parents=True)
        (root / "repo/third-party/skills.json").write_text(json.dumps(MANIFEST))
        self.manifest = load(root / "repo")
        self.home = Home(root / "home")
        self.lock = {}
        self.out = []

    def installed(self, name, where=None, text="same", mtime=None):
        folder = (where or self.home.store) / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text(text)
        if mtime is not None:
            os.utime(folder / "SKILL.md", (mtime, mtime))

    def locked(self, name, source, kind="github"):
        self.lock[name] = {"source": source, "sourceType": kind}

    def findings(self, owned=()):
        self.home.lock.parent.mkdir(parents=True, exist_ok=True)
        self.home.lock.write_text(json.dumps({"skills": self.lock}))
        return [(str(f), f.fails) for f in check(self.manifest, self.home, owned)]

    def good_install(self):
        for name, repo in (("alpha", "a/one"), ("beta", "b/two")):
            self.installed(name)
            self.locked(name, repo)
        codex = self.home.agent_dir("codex")
        codex.mkdir(parents=True)
        (codex / "alpha").symlink_to(self.home.store / "alpha")

    def test_a_source_without_agents_falls_back_to_the_top_level_list(self):
        self.assertEqual([(k.name, k.agents) for k in self.manifest.curated],
                         [("alpha", ("claude-code", "codex")), ("beta", ("claude-code",))])
        self.assertEqual([k.name for k in self.manifest.archived], ["old", "gone"])

    def test_install_commands_skip_a_source_with_nothing_curated(self):
        self.assertEqual([cmd for _, cmd in install_commands(self.manifest)], [
            ["npx", "--yes", "skills@latest", "add", "a/one", "--global", "--yes",
             "--skill", "alpha", "--agent", "claude-code", "--agent", "codex"],
            ["npx", "--yes", "skills@latest", "add", "b/two", "--global", "--yes",
             "--skill", "beta", "--agent", "claude-code"],
        ])

    def test_a_good_install_is_all_ok(self):
        self.good_install()
        self.assertEqual(self.findings(), [("ok        alpha", False), ("ok        beta", False)])

    def test_missing_and_conflict_fail(self):
        self.locked("alpha", "someone/else")
        found = self.findings()
        self.assertIn(("conflict  alpha installed from someone/else, manifest says a/one", True), found)
        self.assertIn(("missing   beta (from b/two)", True), found)

    def test_archived_still_installed_fails_and_uncurated_only_reports(self):
        # S3 in docs/arch-review/2026-10-08-tooling.md: both used to exit 0.
        self.good_install()
        self.locked("old", "a/one")
        self.locked("random", "x/y")
        self.locked("local", "/tmp/x", kind="local")
        found = self.findings()
        self.assertIn(("archived  old is still installed — remove it with: npx skills remove -g old", True), found)
        self.assertIn(("uncurated random (installed from x/y)", False), found)
        self.assertNotIn("local", " ".join(f for f, _ in found))

    def test_unmanaged_skips_what_is_locked_curated_or_owned(self):
        self.good_install()
        claude = self.home.agent_dir("claude-code")
        for name in ("stray", "mine"):
            self.installed(name, claude)
        self.installed("stray")
        found = self.findings(owned=["mine"])
        self.assertIn((f"unmanaged stray (in 2: {self.home.store}, {claude})", False), found)
        self.assertNotIn("mine", " ".join(f for f, _ in found))

    def test_an_agent_copy_older_than_the_store_is_drift(self):
        self.good_install()
        claude = self.home.agent_dir("claude-code")
        self.installed("alpha", claude, text="older", mtime=1)
        self.installed("beta", claude, text="newer", mtime=4_000_000_000)
        found = self.findings()
        self.assertIn((f"drift     alpha ({claude} is older than the store — re-sync from a plain terminal)", True), found)
        self.assertIn((f"note      1 store copies under {self.home.store} are older than what the agents load, and unused",
                       False), found)

    def test_a_universal_agent_needs_a_link_not_a_copy(self):
        self.good_install()
        codex = self.home.agent_dir("codex")
        (codex / "alpha").unlink()
        self.installed("alpha", codex)
        stale = f"({codex / 'alpha'} is a stale copy, not a link into the store — move it aside, then run the sync)"
        self.assertIn((f"drift     alpha {stale}", True), self.findings())
        (codex / "alpha" / "SKILL.md").unlink()
        (codex / "alpha").rmdir()
        self.assertIn((f"drift     alpha (codex is missing the link {codex / 'alpha'} — run the sync)", True),
                      self.findings())

    def test_link_makes_missing_links_and_refuses_to_replace_a_copy(self):
        self.installed("alpha")
        errors = []
        self.assertEqual(link(self.manifest, self.home, self.out.append, errors.append), [])
        target = self.home.agent_dir("codex") / "alpha"
        self.assertEqual(os.readlink(target), str(self.home.store / "alpha"))
        target.unlink()
        self.installed("alpha", self.home.agent_dir("codex"))
        self.assertEqual(link(self.manifest, self.home, self.out.append, errors.append), ["link alpha into codex"])
        self.assertIn("refusing to replace", errors[0])

    def test_sync_carries_on_past_a_failing_source_and_still_links(self):
        # S2 in docs/arch-review/2026-10-08-tooling.md: the first failure stopped everything.
        self.installed("alpha")
        calls = []

        def run(cmd, **_):
            calls.append(cmd[4])
            return SimpleNamespace(returncode=1 if cmd[4] == "a/one" else 0)

        failed = sync(self.manifest, self.home, run, self.out.append, self.out.append)
        self.assertEqual(calls, ["a/one", "b/two"])
        self.assertEqual(failed, ["install from a/one"])
        self.assertTrue((self.home.agent_dir("codex") / "alpha").is_symlink())

    def test_sync_records_an_npx_it_cannot_run(self):
        self.installed("alpha")
        errors = []

        def run(cmd, **_):
            raise FileNotFoundError(2, "No such file or directory", cmd[0])

        failed = sync(self.manifest, self.home, run, self.out.append, errors.append)
        self.assertEqual(failed, ["install from a/one", "install from b/two"])
        self.assertIn("error: cannot run npx: No such file or directory", errors)
        self.assertTrue((self.home.agent_dir("codex") / "alpha").is_symlink())

    def test_a_source_without_agents_anywhere_has_none(self):
        repo = self.home.root.parent / "bare"
        (repo / "third-party").mkdir(parents=True)
        (repo / "third-party/skills.json").write_text(json.dumps(
            {"sources": [{"repo": "a/b", "why": None, "skills": [{"name": "x"}]}]}))
        [source] = load(repo).sources
        self.assertEqual((source.agents, source.why, source.skills[0].why), ((), "", ""))

    def test_listing(self):
        lines = third_party.listing(self.manifest)
        self.assertEqual(lines[:4], ["", "a/one — w", f"  {'alpha':<30} w", f"  {'old (archived)':<30} w"])



if __name__ == "__main__":
    unittest.main()
