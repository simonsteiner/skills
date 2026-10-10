#!/usr/bin/env python3
"""Dev-machine convenience: link the owned skills, then sync the curated third-party ones.

Run it after pulling, and after adding, moving or removing a skill. All the work happens
in the two scripts it calls; --check is passed through to both.

    scripts/sync-skills.py          scripts/link-skills.py, then scripts/sync-third-party.py
    scripts/sync-skills.py --check  both scripts' --check

Only for the machine where you develop the skills — everywhere else, owned skills come
from `npx skills add` and only sync-third-party.py applies. Run it from a plain terminal,
and restart your agents afterwards: they read their skill list at startup.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def main(argv):
    if argv not in ([], ["--check"]):
        print("Usage: scripts/sync-skills.py [--check]", file=sys.stderr)
        return 2
    status = 0
    for title, script in (("owned skills", "link-skills.py"), ("third-party skills", "sync-third-party.py")):
        print(f"==> {title}", flush=True)
        status |= subprocess.run([sys.executable, SCRIPTS / script, *argv], check=False).returncode != 0
        print(flush=True)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
