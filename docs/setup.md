# Developing the skills

Everything here is for the machine where you edit this repo. The tooling runs through [uv](https://docs.astral.sh/uv/), which installs its one dependency (`ruamel.yaml`, pinned in `uv.lock`) on first run. Everywhere else, install the published skills with `npx skills@latest add simonsteiner/skills`.

## Set up

```bash
npm install               # changesets, rumdl, and the lefthook git hooks
./scripts/sync-skills.py  # dev-link the owned skills and install the curated ones
```

## Dev-mode links

To hack on a skill with live edits, symlink this repo's skills into your local agent directories:

```bash
./scripts/link-skills.py          # link every owned skill, prune links to removed or deprecated ones
./scripts/link-skills.py --check  # report owned skills that aren't linked, and dead links
```

This is the dev-mode equivalent of `npx skills add`: it links each skill into `~/.agents/skills` (and mirrors it for Claude Code under `~/.claude/skills` and Antigravity under `~/.gemini/config/skills`), so edits here take effect immediately. Pick one path per skill — dev-link it here, or install it with skills.sh — not both.

`./scripts/sync-skills.py` runs `link-skills.py` and then `sync-third-party.py` (pass `--check` to check both). The links point at this checkout's working tree, so whatever branch is checked out is what your agents run. That decides when a sync is needed:

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
