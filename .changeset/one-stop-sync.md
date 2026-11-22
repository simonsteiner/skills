---
"simonsteiner-skills": minor
---

`scripts/sync-skills.py` is now the one command to install and update everything: clone the repo and run it. It fast-forwards the checkout when the default branch is checked out, links the owned skills and installs the curated ones. `--check` also reports how far the checkout is behind and, through the new `scripts/sync-third-party.py --outdated`, which curated skills changed upstream since they were installed. It compares the folder hash in the skills.sh lock file with the upstream folder.
