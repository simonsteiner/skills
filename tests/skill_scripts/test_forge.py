"""Tests for skills/engineering/review-prs/scripts/forge.sh, in throwaway repos through a fake gh.

    python3 -m unittest discover -s tests -t .
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from .fake_gh import FakeGh

SCRIPT = Path(__file__).resolve().parents[2] / "skills/engineering/review-prs/scripts/forge.sh"
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


class ForgeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.gh = FakeGh(tmp.name)
        self.repo = Path(tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
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

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=ENV, capture_output=True, text=True, check=True)

    def forge(self, origin, env=None):
        self.git("config", "remote.origin.url", origin)
        result = self.gh.run(SCRIPT, env=env, cwd=self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_github_https_and_ssh(self):
        for origin in ("https://github.com/acme/web.git", "https://github.com/acme/web",
                       "git@github.com:acme/web.git", "ssh://git@github.com/acme/web.git"):
            with self.subTest(origin=origin):
                self.assertEqual(self.forge(origin), "github\tacme/web\n")
        self.assertEqual(self.gh.calls, [])

    def test_azure_devops_https_and_ssh(self):
        origins = ("https://dev.azure.com/acme/Shop/_git/web", "https://acme@dev.azure.com/acme/Shop/_git/web",
                   "git@ssh.dev.azure.com:v3/acme/Shop/web", "ssh://git@ssh.dev.azure.com/v3/acme/Shop/web",
                   "https://acme.visualstudio.com/Shop/_git/web",
                   "https://acme.visualstudio.com/DefaultCollection/Shop/_git/web",
                   "acme@vs-ssh.visualstudio.com:v3/acme/Shop/web")
        for origin in origins:
            with self.subTest(origin=origin):
                self.assertEqual(self.forge(origin), "azure-devops\tacme\tShop\tweb\n")
        self.assertEqual(self.gh.calls, [])

    def test_url_decodes_azure_devops_names(self):
        self.assertEqual(self.forge("https://dev.azure.com/acme/My%20Shop/_git/web%20app"),
                         "azure-devops\tacme\tMy Shop\tweb app\n")

    def test_url_decodes_azure_devops_ssh_names(self):
        self.assertEqual(self.forge("git@ssh.dev.azure.com:v3/acme/My%20Shop/web"),
                         "azure-devops\tacme\tMy Shop\tweb\n")

    def test_azure_devops_url_without_a_project_uses_the_repo_name(self):
        self.assertEqual(self.forge("https://dev.azure.com/acme/_git/web"), "azure-devops\tacme\tweb\tweb\n")

    def test_azure_devops_origin_wins_over_gh_repo_and_upstream(self):
        self.git("remote", "add", "upstream", "https://github.com/acme/web.git")
        out = self.forge("https://dev.azure.com/acme/Shop/_git/web", env={"GH_REPO": "acme/web"})
        self.assertEqual(out, "azure-devops\tacme\tShop\tweb\n")
        self.assertEqual(self.gh.calls, [])

    def test_github_origin_ignores_gh_repo(self):
        self.assertEqual(self.forge("git@github.com:me/fork.git", env={"GH_REPO": "acme/web"}), "github\tme/fork\n")

    def test_ssh_host_alias_for_github_com(self):
        # gh reads a URL's host literally, so the alias must be resolved before anything asks it.
        self.alias("github-work", "github.com")
        for origin in ("git@github-work:acme/web.git", "ssh://git@github-work/acme/web.git"):
            with self.subTest(origin=origin):
                self.assertEqual(self.forge(origin, env={"GH_REPO": "other/repo"}), "github\tacme/web\n")
        self.assertEqual(self.gh.calls, [])

    def test_ssh_host_alias_for_github_enterprise_asks_gh_with_the_real_host(self):
        self.alias("corp", "GHE.example.com")
        self.gh.on("repo", "view", "https://ghe.example.com/acme/web.git", json={"nameWithOwner": "acme/web"})
        self.assertEqual(self.forge("git@corp:acme/web.git", env={"GH_REPO": "other/repo"}), "github\tacme/web\n")
        [call] = self.gh.calls
        self.assertEqual(call["args"][:3], ["repo", "view", "https://ghe.example.com/acme/web.git"])

    def test_ssh_over_port_443_is_still_github_com(self):
        # GitHub's documented `Host github.com` / `Hostname ssh.github.com` / `Port 443` config.
        self.alias("github.com", "ssh.github.com")
        for origin in ("git@github.com:acme/web.git", "ssh://git@github.com/acme/web.git"):
            with self.subTest(origin=origin):
                self.assertEqual(self.forge(origin), "github\tacme/web\n")
        self.assertEqual(self.gh.calls, [])

    def test_ssh_host_alias_for_azure_devops(self):
        self.alias("ado", "ssh.dev.azure.com")
        self.assertEqual(self.forge("git@ado:v3/acme/Shop/web"), "azure-devops\tacme\tShop\tweb\n")
        self.assertEqual(self.gh.calls, [])

    def test_https_origin_is_not_resolved_through_ssh(self):
        self.alias("github.com", "elsewhere.example.com")
        self.assertEqual(self.forge("https://github.com/acme/web"), "github\tacme/web\n")

    def test_github_enterprise_asks_gh(self):
        origin = "https://ghe.example.com/acme/web.git"
        self.gh.on("repo", "view", origin, json={"nameWithOwner": "acme/web"})
        self.assertEqual(self.forge(origin), "github\tacme/web\n")

    def test_unsupported_host(self):
        # No rule: the fake gh fails the `gh repo view`, as the real one does for a GitLab URL.
        self.assertEqual(self.forge("git@GitLab.com:acme/web.git"), "unsupported\tgitlab.com\n")
        self.assertEqual([c["args"][:2] for c in self.gh.calls], [["repo", "view"]])

    def test_reads_origin_only(self):
        self.git("remote", "add", "upstream", "https://dev.azure.com/acme/Shop/_git/web")
        self.assertEqual(self.forge("https://github.com/acme/web"), "github\tacme/web\n")

    def test_no_origin_fails_with_a_message(self):
        self.git("remote", "add", "upstream", "https://github.com/acme/web")
        result = self.gh.run(SCRIPT, cwd=self.repo)
        self.assertEqual((result.returncode, result.stdout), (1, ""))
        self.assertIn("no 'origin' remote", result.stderr)
        self.assertEqual(self.gh.calls, [])


if __name__ == "__main__":
    unittest.main()
