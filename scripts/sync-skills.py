#!/usr/bin/env python3
"""The one command to install and update every skill: clone this repo, run this, rerun it to update.

    scripts/sync-skills.py          pull, link the owned skills, sync the curated ones
    scripts/sync-skills.py --check  report what a sync would change, and exit 1 if anything

A sync runs, in order:

1. the checkout: fetch origin and fast-forward when the default branch is checked out and
   behind. On any other branch it only says how far behind it is, so a feature branch
   being developed is never moved.
2. scripts/link-skills.py: link the owned skills from this checkout into the agents.
3. scripts/sync-third-party.py: install the curated skills from upstream, at latest.

--check fetches but changes nothing: how far the checkout is behind, link-skills.py
--check, sync-third-party.py --check, and sync-third-party.py --outdated (whether upstream
changed a curated skill since it was installed).

Needs git, Python 3.10+ and Node's npx (for the skills.sh CLI). Run it from a plain
terminal, not inside an agent session (the CLI would install curated skills to that agent
alone), and restart your agents afterwards: they read their skill list at startup.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent

USAGE = """\
Usage: scripts/sync-skills.py [--check]

  (no args)  fast-forward the checkout on its default branch, link the owned
             skills, install the curated ones
  --check    report what a sync would change; exit 1 if anything"""


def git(*args):
    """(returncode, stdout) of a git command in this checkout."""
    done = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=False)
    return done.returncode, done.stdout.strip()


def checkout(check):
    """Bring the checkout up to date with origin, or say why not; 1 when it's still behind."""
    if git("fetch", "--quiet", "origin")[0] != 0:
        print("could not fetch origin; carrying on with the checkout as it is")
        return 0
    code, upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if code != 0:
        print("this branch tracks no remote branch; not pulled")
        return 0
    behind = int(git("rev-list", "--count", f"HEAD..{upstream}")[1] or 0)
    if not behind:
        print(f"up to date with {upstream}")
        return 0
    if check:
        print(f"{behind} commit(s) behind {upstream}; a sync pulls them")
        return 1
    branch = git("rev-parse", "--abbrev-ref", "HEAD")[1]
    default = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")[1].removeprefix("origin/")
    if branch != default:
        print(f"{branch} is {behind} commit(s) behind {upstream}; only {default or 'the default branch'} is pulled")
        return 0
    code = subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only", "--quiet"], check=False).returncode
    print(f"pulled {behind} commit(s) from {upstream}" if code == 0 else "git pull --ff-only failed; see above")
    return 1 if code else 0


def run(script, *args):
    """Run one of the sibling scripts; 1 when it failed."""
    return int(subprocess.run([sys.executable, str(SCRIPTS / script), *args], check=False).returncode != 0)


def main(argv):
    if argv in (["-h"], ["--help"]):
        print(USAGE)
        return 0
    if argv not in ([], ["--check"]):
        print(f"error: unknown argument '{' '.join(argv)}'\n{USAGE}", file=sys.stderr)
        return 2
    check = bool(argv)
    steps = [("checkout", lambda: checkout(check)),
             ("owned skills", lambda: run("link-skills.py", *argv)),
             ("third-party skills", lambda: run("sync-third-party.py", *argv))]
    if check:
        steps.append(("third-party versions", lambda: run("sync-third-party.py", "--outdated")))
    status = 0
    for title, step in steps:
        print(f"==> {title}", flush=True)
        status |= step()
        print(flush=True)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
