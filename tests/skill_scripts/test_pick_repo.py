"""Tests for skills/engineering/address-review-findings/scripts/pick-repo.sh, in throwaway repos through a fake gh.

    python3 -m unittest discover -s tests -t .
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


if __name__ == "__main__":
    unittest.main()
