"""Tests for skills/engineering/address-review-findings/scripts/pick-repo.sh, in throwaway repos through a fake gh.

    uv run --locked --no-build python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/address-review-findings/scripts/pick-repo.sh"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
TOKENS = {"GH_ENTERPRISE_TOKEN": "t1", "GITHUB_ENTERPRISE_TOKEN": "t2"}


class PickRepoTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.repo = Path(tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, env=ENV, check=True)
        # A fake `ssh -G <host>`, so the developer's ~/.ssh/config can't alias a test's host.
        self.ssh_hosts = Path(tmp.name) / "ssh-hosts"
        self.ssh_hosts.write_text("")
        ssh = Path(tmp.name) / "bin" / "ssh"
        ssh.write_text(f'#!/bin/sh\n[ "$1" = -G ] || exit 255\n'
                       f'real="$(awk -v h="$2" \'$1 == h {{ print $2 }}\' "{self.ssh_hosts}")"\n'
                       f'echo "user git"; echo "hostname ${{real:-$2}}"; echo "port 22"\n')
        ssh.chmod(0o755)

    def alias(self, name, real):
        with self.ssh_hosts.open("a") as f:
            f.write(f"{name} {real}\n")

    def default(self, url):
        self.gh.on("repo", "view", "--json", json={"url": url})

    def pick(self, origin=None, env=None, code=0):
        if origin:
            subprocess.run(["git", "config", "remote.origin.url", origin], cwd=self.repo, env=ENV, check=True)
        result = self.gh.run(SCRIPT, env=env, cwd=self.repo)
        self.assertEqual(result.returncode, code, result.stderr)
        return result.stdout

    def origin_probes(self):
        return [c for c in self.gh.calls if c["args"][2:3] != ["--json"]]

    def test_gh_repo_wins_without_asking_gh(self):
        self.assertEqual(self.pick("git@github.com:me/web.git", env={"GH_REPO": "ghe.example.com/me/web"}),
                         "ghe.example.com/me/web\n")
        self.assertEqual(self.gh.calls, [])

    def test_same_repo_prints_one_line(self):
        self.default("https://github.com/acme/web")
        self.assertEqual(self.pick("https://github.com/acme/web.git"), "acme/web\n")

    def test_fork_prints_upstream_then_origin(self):
        self.default("https://github.com/acme/web")
        for origin in ("git@github.com:me/web.git", "https://github.com/me/web", "ssh://git@ssh.github.com:443/me/web.git"):
            with self.subTest(origin=origin):
                self.assertEqual(self.pick(origin), "acme/web\nme/web\n")
                self.assertEqual(self.origin_probes(), [])

    def test_ssh_alias_for_github_com_needs_no_gh_call(self):
        self.alias("github-work", "github.com")
        self.default("https://github.com/acme/web")
        self.assertEqual(self.pick("git@github-work:me/web.git"), "acme/web\nme/web\n")
        self.assertEqual(self.origin_probes(), [])

    def test_github_enterprise_origin_keeps_its_host(self):
        self.alias("corp", "ghe.example.com")
        self.default("https://ghe.example.com/acme/web")
        self.gh.on("repo", "view", "https://ghe.example.com/me/web", json={"url": "https://ghe.example.com/me/web"})
        self.assertEqual(self.pick("git@corp:me/web.git", env={**TOKENS, "GH_HOST": "ghe.example.com"}),
                         "ghe.example.com/acme/web\nghe.example.com/me/web\n")
        [probe] = self.origin_probes()
        self.assertEqual({k: v for k, v in probe["env"].items() if k in TOKENS}, TOKENS)

    def test_enterprise_token_stays_off_an_unknown_origin_host(self):
        self.default("https://github.com/acme/web")
        self.gh.on("repo", "view", "https://evil.example.com/me/web", json={"url": "https://evil.example.com/me/web"})
        self.pick("https://evil.example.com/me/web.git", env={**TOKENS, "GH_HOST": "ghe.example.com"})
        [probe] = self.origin_probes()
        self.assertEqual({k: v for k, v in probe["env"].items() if k in TOKENS}, {})

    def test_github_com_is_spelled_out_when_gh_host_is_another_host(self):
        # gh resolves a bare owner/repo on GH_HOST, so acme/web would mean ghe.example.com/acme/web.
        self.default("https://github.com/acme/web")
        self.assertEqual(self.pick("git@github.com:me/web.git", env={"GH_HOST": "ghe.example.com"}),
                         "github.com/acme/web\ngithub.com/me/web\n")

    def test_origin_alone_when_gh_has_no_default(self):
        self.assertEqual(self.pick("git@github.com:me/web.git"), "me/web\n")

    def test_fails_when_neither_repo_reads(self):
        self.pick("git@gitlab.com:me/web.git", code=1)


class PickRepoForPrsTest(unittest.TestCase):
    """PR numbers and --head map each PR to the repo it lives on: acme/web upstream, me/web origin."""

    def setUp(self):
        PickRepoTest.setUp(self)
        self.gh.on("repo", "view", "--json", json={"url": "https://github.com/acme/web"})
        subprocess.run(["git", "config", "remote.origin.url", "git@github.com:me/web.git"], cwd=self.repo, env=ENV, check=True)
        subprocess.run(["git", "checkout", "-q", "-b", "feat/x"], cwd=self.repo, env=ENV, check=True)

    MISSING = "GraphQL: Could not resolve to a PullRequest with the number of 0. (repository.pullRequest)\n"

    def pr(self, n, repo, head):
        self.gh.on("pr", "view", str(n), "--repo", repo, json={"url": f"https://github.com/{repo}/pull/{n}", "headRefName": head})

    def map(self, *args, env=None, code=0):
        result = self.gh.run(SCRIPT, *args, env=env, cwd=self.repo)
        self.assertEqual(result.returncode, code, result.stderr)
        return result.stdout, result.stderr

    def test_a_number_on_one_repo_goes_there(self):
        self.pr(12, "me/web", "feat/x")
        self.gh.on("pr", "view", "12", stderr=self.MISSING, exit=1)
        self.assertEqual(self.map(12)[0], "12\tme/web\n")

    def test_a_number_on_both_goes_to_the_checkouts_branch(self):
        self.pr(12, "acme/web", "fix/y")
        self.pr(12, "me/web", "feat/x")
        self.assertEqual(self.map(12)[0], "12\tme/web\n")

    def test_head_overrides_the_checkouts_branch(self):
        self.pr(12, "acme/web", "fix/y")
        self.pr(12, "me/web", "feat/x")
        self.assertEqual(self.map("--head", "fix/y", 12)[0], "12\tacme/web\n")

    def test_ambiguous_and_missing_prs_go_to_stderr_after_the_resolved_ones(self):
        self.pr(12, "acme/web", "other")
        self.pr(12, "me/web", "other")
        self.pr(15, "acme/web", "feat/z")
        self.gh.on("pr", "view", stderr=self.MISSING, exit=1)
        out, err = self.map(12, 15, 16, code=3)
        self.assertEqual(out, "15\tacme/web\n")
        self.assertIn("https://github.com/acme/web/pull/12 https://github.com/me/web/pull/12", err)
        self.assertIn("PR #16 not found", err)

    def test_missing_alone_exits_4(self):
        self.gh.on("pr", "view", stderr=self.MISSING, exit=1)
        self.map(16, code=4)

    def test_head_finds_the_open_pr_on_either_repo(self):
        self.gh.on("pr", "list", "--head", "feat/x", "--state", "open", "--repo", "acme/web",
                   json=[{"number": 21, "url": "https://github.com/acme/web/pull/21", "headRepositoryOwner": {"login": "me"}}])
        self.gh.on("pr", "list", "--head", "feat/x", "--state", "open", "--repo", "me/web", json=[])
        self.assertEqual(self.map("--head", "feat/x")[0], "21\tacme/web\n")

    def test_head_with_a_pr_on_each_repo_is_ambiguous(self):
        for repo, n in (("acme/web", 21), ("me/web", 3)):
            self.gh.on("pr", "list", "--head", "feat/x", "--state", "open", "--repo", repo,
                       json=[{"number": n, "url": f"https://github.com/{repo}/pull/{n}", "headRepositoryOwner": {"login": "Me"}}])
        out, err = self.map("--head", "feat/x", code=3)
        self.assertEqual(out, "")
        self.assertIn("https://github.com/acme/web/pull/21 https://github.com/me/web/pull/3", err)

    def test_head_skips_another_forks_branch_of_the_same_name(self):
        self.gh.on("pr", "list", "--head", "feat/x", "--state", "open", "--repo", "acme/web",
                   json=[{"number": 21, "url": "https://github.com/acme/web/pull/21", "headRepositoryOwner": {"login": "other"}}])
        self.gh.on("pr", "list", "--head", "feat/x", "--state", "open", "--repo", "me/web", json=[])
        out, err = self.map("--head", "feat/x", code=4)
        self.assertEqual(out, "")
        self.assertIn("no open PR for branch feat/x", err)

    def test_a_failed_lookup_stops_instead_of_reading_as_missing(self):
        self.pr(12, "me/web", "feat/x")
        self.gh.on("pr", "view", "12", "--repo", "acme/web", stderr="HTTP 502: Bad Gateway\n", exit=1)
        out, err = self.map(12, code=1)
        self.assertEqual(out, "")
        self.assertIn("could not look up PR #12 on acme/web: HTTP 502", err)

    def test_a_failed_head_lookup_exits_1_not_gh_s_code(self):
        self.gh.on("pr", "list", stderr="To get started with GitHub CLI, please run:  gh auth login\n", exit=4)
        out, err = self.map("--head", "feat/x", code=1)
        self.assertEqual(out, "")
        self.assertIn("could not list PRs for feat/x on acme/web: To get started", err)

    def test_head_with_no_open_pr_exits_4(self):
        self.gh.on("pr", "list", json=[])
        self.map("--head", "feat/x", code=4)

    def test_gh_repo_maps_every_pr_unchecked(self):
        self.assertEqual(self.map(12, 15, env={"GH_REPO": "me/web"})[0], "12\tme/web\n15\tme/web\n")
        self.assertEqual(self.gh.calls, [])

    def test_bad_usage_exits_2(self):
        self.map("twelve", code=2)
        self.map("--head", code=2)


if __name__ == "__main__":
    unittest.main()
