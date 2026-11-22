# Install by cloning the repo and running `sync-skills.py`

Supersedes [ADR 0001](./0001-fork-and-pare-down-to-conventional-commit.md)'s split of a dev-linked install on the development machine and skills.sh everywhere else.

## Context

Installing used to take two tools, depending on the machine. On the development machine, `link-skills.py` linked the owned skills from the checkout. Everywhere else, `npx skills add simonsteiner/skills` installed them. On every machine, `sync-third-party.py` installed the curated skills. In practice every machine was set up the same way: clone the repo, then run the scripts. Nothing in that flow said whether the checkout was behind `origin`, or whether a curated skill had changed upstream since its install.

## Decision

- **`scripts/sync-skills.py` is the one command**, on every machine. It fetches `origin` and fast-forwards the checkout when the default branch is checked out, reruns its updated copy if that pulled anything, links the owned skills, then installs the curated ones. Rerunning it is the update.
- **`--check` reports what a sync would change**: commits the checkout is behind, links and installs that disagree with the repo, and curated skills whose upstream folder changed since install. The last one compares the `skillFolderHash` the skills.sh lock file records with the folder's git tree SHA on the upstream default branch (`sync-third-party.py --outdated`).
- **It never moves a non-default branch.** A checkout on a feature branch is being developed, so it only reports how far behind that branch is.
- `npx skills add simonsteiner/skills` stays the way to take only the owned skills without a clone.

## Consequences

- A clone's agents run its working tree, so whatever branch is checked out is what they load. On a machine that only uses the skills, keep the checkout on `main`.
- Each sync and each `--check` calls GitHub: one API call per curated source with `--outdated`, authenticated by `GH_TOKEN`, `GITHUB_TOKEN` or a `gh` login when there is one, else anonymous.
- Curated skills are still unpinned. `--outdated` says a sync would change something, not what changed; read the upstream diff for that.
