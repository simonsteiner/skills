# Developing the skills

Installing is the same on every machine: clone the repo and run `./scripts/sync-skills.py` ([README](../README.md#install)). Editing the skills adds the checks and git hooks below. The lint and the catalog build run through [uv](https://docs.astral.sh/uv/), which installs their one dependency (`ruamel.yaml`, pinned in `uv.lock`) on first run; the sync scripts need only Python.

## Set up

```bash
npm install               # changesets, rumdl, and the lefthook git hooks
./scripts/sync-skills.py  # link the owned skills and install the curated ones
```

## The one-stop sync

`./scripts/sync-skills.py` runs three steps: it fetches `origin` and fast-forwards the checkout when the default branch is checked out (on any other branch it only says how far behind it is), runs `link-skills.py`, then runs `sync-third-party.py`. `--check` changes nothing and reports all of it, plus `sync-third-party.py --outdated`: which installed curated skills changed upstream since they were installed. That check compares the folder hash the skills.sh lock file recorded at install with the folder on the upstream default branch, one GitHub API call per source; set `GH_TOKEN` or `GITHUB_TOKEN` if you hit GitHub's anonymous limit of 60 calls an hour. Curated skills aren't pinned, so a sync always moves them to upstream's latest.

## Links

`sync-skills.py` links the owned skills with `link-skills.py`, which you can also run alone:

```bash
./scripts/link-skills.py          # link every owned skill, prune links to removed or deprecated ones
./scripts/link-skills.py --check  # report owned skills that aren't linked, and dead links
```

This is the clone's equivalent of `npx skills add`: it links each skill into `~/.agents/skills` (and mirrors it for Claude Code under `~/.claude/skills` and Antigravity under `~/.gemini/config/skills`), so edits here take effect immediately. Pick one path per skill — link it from a clone, or install it with skills.sh — not both.

The links point at this checkout's working tree, so whatever branch is checked out is what your agents run. That decides when a sync is needed:

| What changed | What to do |
|---|---|
| An existing skill's body, references or scripts (edited here, or pulled) | Nothing; the next invocation reads the new files |
| An existing skill's `name` or `description` | Restart your agents; they read the skill list at startup |
| A skill added, moved, renamed or removed (here, or in a pull) | Sync, then restart |
| `third-party/skills.json`, or an upstream curated skill you want to pick up | Sync (or just `sync-third-party.py`), then restart |

`sync-skills.py --check` reports whether anything is missing or stale, so when in doubt, run that. T3 Code caches each provider's skill list for its picker, so a new skill can stay missing there until T3 refreshes that list, even after you restart the agent.

## The skill catalog

The skill lists in `README.md`, each `skills/<bucket>/README.md` and `.claude-plugin/plugin.json` are generated from the skills by `./scripts/build-catalog.py` (`--check` to only report). An entry's text is the skill's `description`: whole for a user-invoked skill, and up to the first sentence starting "Use" for a model-invoked one. To change an entry, change the skill and rerun it; the pre-commit hook does that for you and stages the result.

## Checks

| Command | What it checks |
|---|---|
| `./scripts/lint-skills.py` | every skill against Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), the [Agent Skills spec and best practices](https://agentskills.io/skill-creation/best-practices), and the listing rules in `AGENTS.md` (rules in `scripts/tooling/authoring_rules.py` and `published_rules.py`) |
| `uv run --locked --no-build python3 -m unittest discover -s tests -t .` | every test: `tests/tooling/` for the `scripts/tooling/` package, `tests/skill_scripts/` for the scripts bundled in skills (against a fake `gh`, so no test touches GitHub), `tests/skills/` for checks on the skills' prose |
| `uvx ruff@0.17.0 check scripts tests` | the Python tooling ([ruff](https://docs.astral.sh/ruff/), config in `ruff.toml`) |
| `npx rumdl check .` | Markdown ([rumdl](https://rumdl.dev/), config in `.rumdl.toml`) |
| `shellcheck skills/*/*/scripts/*.sh` | the shell scripts bundled in skills |

CI (`.github/workflows/lint.yml`) runs all of them on every PR. The lefthook pre-commit hooks (`lefthook.yml`) run the same checks on the staged files, rebuild the skill catalog, and let rumdl fix what it can. With the [SonarQube CLI](https://sonarsource.com/sonarqube/cli) installed and logged in, they also scan the staged files for secrets and new dependency risks; without it that job is skipped, and SonarCloud's PR analysis still runs.

What counts as an owned skill — its bucket, its name, no duplicates and no clash with a curated skill — is decided once, in `scripts/tooling/skill_inventory.py`, and everything about `third-party/skills.json` in `scripts/tooling/third_party.py`; the commands at the top of `scripts/` read them.

A skill's evals run with `./scripts/eval-skill.py`; see [evals.md](evals.md).
