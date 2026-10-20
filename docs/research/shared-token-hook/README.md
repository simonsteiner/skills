# One shared, pinned `check-file-tokens.py` for ~22 repos

Research notes, 2026-10-20. How to stop copying `skills/engineering/setup-lefthook/scripts/check-file-tokens.py` into every repo and run one pinned version instead. Primary sources only; anything not checked against a source or an experiment is marked **Unverified**.

- [lefthook-remotes.md](lefthook-remotes.md): question 1, lefthook `remotes:` (syntax, scripts in a remote, merging, offline, clone size, version bumps)
- [runners.md](runners.md): question 2, running the script from uvx, pipx, npm/npx, pnpm or bare `python3`
- [experiment-log.md](experiment-log.md): the commands and trimmed outputs behind every "verified by experiment" claim

## TL;DR

- **Use lefthook `remotes:`, pointed at this repo (`simonsteiner/skills`), pinned to a hook-only tag such as `file-tokens-v1.0.0`.** lefthook shallow-clones the tag once into `.git/info/lefthook-remotes/` and runs a script from it on every commit, with `{staged_files}` and the project root as the working directory. Measured: the job takes 0.04 s, the same as today's copy.
- **The script stays in the skill; the remote only exposes it.** lefthook looks for remote scripts in `<remote root>/.lefthook/<hook>/`, so this repo adds `.lefthook/pre-commit/check-file-tokens.py` as a symlink to the skill's script (works, tested on Linux) plus a jobs-free config file for consumers to load.
- **Each repo defines the `file-tokens` job itself** (`script:` + `runner: python3` + `args:`) and takes only the script from the remote. That's the one shape that is fail-closed when the remote can't be fetched and lets a repo set its own `--max-tokens`. A job defined *in* the remote fails open and can't be overridden from `lefthook.yml`.
- **It needs nothing new on any stack**: lefthook (already there) and `python3` ≥ 3.9 (tested on 3.9). No uv, pipx or Node needed. That's why it beats the runner-up, a PyPI package run with `uvx file-tokens@X.Y.Z` (fast and offline-safe, but uv on every machine plus a publishing pipeline). `uvx --from git+…@tag` is out: it resolves the tag over the network on every run (~0.8 s) and fails offline.
- **A version bump is a one-line `ref:` change per repo.** The next `git commit` in each clone fetches the new tag and deletes the old checkout, with no `lefthook install`. Roll it out across 22 repos with a scripted `gh` loop, or with a Renovate regex manager (**Unverified**: not run).
- **Watch-outs**: `ref:` must be a tag or branch, not a commit SHA (a SHA fails to clone and lefthook silently falls back to whatever ref it has cached). Tags can be moved, so protect `file-tokens-v*` tags. Whether a claude.ai/code cloud session can `git clone` a second, unattached public GitHub repo is **Unverified**. If it can't, the commit fails with `script does not exist`, not silently.

## Recommendation

One approach for every stack (uv, npm/pnpm, Rust, maturin, docs-only).

**In this repo (the remote), once:**

```text
.lefthook/pre-commit/check-file-tokens.py   -> symlink to ../../skills/engineering/setup-lefthook/scripts/check-file-tokens.py
lefthook/file-tokens.yml                     # what consumers load: no jobs, so nothing merges into theirs
```

```yaml
# lefthook/file-tokens.yml — loaded by repos that use the shared token budget.
# Ships .lefthook/pre-commit/check-file-tokens.py; the job lives in each repo.
min_version: 2.0.5 # `args:` on script jobs
```

Then tag a release of the hook: `git tag file-tokens-v1.0.0 && git push origin file-tokens-v1.0.0`. Do this from a local machine or a workflow; the cloud-session GitHub proxy rejects tag pushes ([cloud environments](https://code.claude.com/docs/en/cloud-environments#github-proxy)).

**In each of the 22 repos** (replaces the `scripts/hooks/check-file-tokens.py` copy and its job):

```yaml
# lefthook.yml
min_version: 2.0.5

remotes:
  # The shared token-budget script. Bump `ref` to update; the next commit fetches it.
  - git_url: https://github.com/simonsteiner/skills
    ref: file-tokens-v1.0.0
    configs:
      - lefthook/file-tokens.yml

pre-commit:
  parallel: true
  jobs:
    # Every staged file an agent writes stays under 5,000 tokens (bytes / 4).
    # The script comes from the remote above; the budget is set here.
    - name: file-tokens
      script: check-file-tokens.py
      runner: python3
      args: --max-tokens 5000 {staged_files}
```

Two repo-level conventions follow from this. Job and script names must not collide with the repo's own `.lefthook/pre-commit/` (lefthook runs a same-named script from every source dir). And `lefthook-local.yml` still works for one-off local overrides.

**Rolling out a bump across 22 repos:**

1. Change the script in this repo (PR, changeset, merge). Tag `file-tokens-vX.Y.Z` on `main`.
2. Open one PR per repo that changes `ref:`. A loop over `gh repo list` plus `sed -i 's/ref: file-tokens-v.*/ref: file-tokens-vX.Y.Z/' lefthook.yml` and `gh pr create` does it, or a Renovate custom regex manager with the `github-tags` datasource. Renovate has no lefthook manager, and Dependabot has no lefthook or generic-regex ecosystem (see [lefthook-remotes.md](lefthook-remotes.md#version-bumps-and-renovatedependabot)).
3. Nothing else: after the merge, each clone's next commit fetches the new tag and deletes the old one (verified, experiment D).

## What would change in the skills (described, not made)

**`skills/engineering/setup-lefthook/SKILL.md`, step 4:**

- Drop "copy it into the project" and the `mkdir -p scripts/hooks && cp …` block. Replace them with: add the `remotes:` entry and the `file-tokens` job from the catalog, set `min_version: 2.0.5`, and run `lefthook install` once (Node's `prepare` does it).
- Migration: when a repo already has `scripts/hooks/check-file-tokens.py` (or `tools/hooks/`), delete it in the same change and replace its job.
- Keep "no `glob:`" and the budget rules. Say that `--max-tokens` goes in the repo's own job `args:`.
- The "files already over the budget" sweep becomes `lefthook run pre-commit --job file-tokens --all-files` (verified: `--all-files` fills `{staged_files}` in `args:`), not `git ls-files -z | xargs -0 python3 scripts/hooks/…`.
- Step 5's proof stays. Add: the first run clones the remote, so it needs network once.

**`skills/engineering/setup-lefthook/references/JOBS.md`:** in "Every project", replace the `file-tokens: run: python3 scripts/hooks/check-file-tokens.py …` command with the `remotes:` block and the `jobs:` entry above. The catalog's other entries use `commands:`; write this one as a `jobs:` entry with a `name:`, the form that was tested and that merges by name. A hook can hold both `commands:` and `jobs:`: both ran, and `lefthook validate` passed (experiment N), so the rest of the catalog can stay as it is. Mention `ref:` takes a tag, never a SHA.

**`skills/engineering/arch-review/SKILL.md`** (the `git ls-files '*check-file-tokens.py'` line breaks once copies are gone):

- Find the budget from the config instead: look for a `file-tokens` job (`lefthook dump` shows the merged config, remotes and `lefthook-local.yml` included) and read `--max-tokens` from its `args:`. Fall back to an old-style copy via `git ls-files '*check-file-tokens.py'` for repos not yet migrated.
- Run the check through lefthook so it uses the repo's own pinned script and budget: `lefthook run pre-commit --job file-tokens --file <path> [--file …]` for a scope, or `--all-files`. Verified (experiment L). Invoke lefthook the way the repo installs it (`npm exec -- lefthook`, `uv run lefthook`, `lefthook`).
- No `file-tokens` job and no copy → the report's budget is 5,000 tokens, as today.

## Sources

Primary sources, grouped by topic, are listed at the end of each topic file. The ones the recommendation rests on:

- lefthook v2.2.2 (latest release, 2026-10-13): <https://github.com/evilmartians/lefthook/releases/tag/v2.2.2>; source at tag `v2.2.2` (commit `eb4e504b7c1d1ea6cb1fd29542431cb6d1a93a03`)
- lefthook `remotes` docs: <https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/remotes.md>
- lefthook `args` docs (added in 2.0.5): <https://github.com/evilmartians/lefthook/blob/v2.2.2/docs/configuration/args.md>
- Claude Code cloud environments: <https://code.claude.com/docs/en/cloud-environments>
