# Skills

A personal collection of agent skills in the open Agent Skills format: each owned skill is a `skills/<bucket>/<name>/` folder with a `SKILL.md`, published through skills.sh and `.claude-plugin/plugin.json`. Other people's skills are curated in `third-party/skills.json` and installed from their own repos, never copied in. The Python tooling in `scripts/` lints the skills, renders the skill catalogs from them and from `third-party/skills.json`, and installs both sets: `scripts/sync-skills.py` links the owned skills from a clone into the local agents and syncs the curated ones.
Domain terms are in `GLOSSARY.md`; decisions and their trade-offs are in `docs/adr/`.

## Commands

```bash
./scripts/lint-skills.py  # check every skill against the authoring and listing rules (CI runs it)
./scripts/build-catalog.py  # rewrite the skill catalogs: README.md, skills/*/README.md, plugin.json, third-party/README.md
./scripts/sync-skills.py --check  # what a sync would change: checkout, links, curated installs, upstream versions
uv run --locked --no-build python3 -m unittest discover -s tests -t .  # run every test
uv run --locked --no-build python3 -m unittest tests.tooling.test_catalog  # run one test module
uvx ruff@0.17.0 check scripts tests  # lint the Python
npx rumdl check .  # lint the Markdown
shellcheck skills/*/*/scripts/*.sh  # lint the bundled shell scripts
git ls-files -z | xargs -0 skills/engineering/setup-lefthook/scripts/check-dashes.py  # no em or en dashes anywhere
npx changeset  # add a changeset for a user-visible change
```

## Conventions

### Buckets and the catalog

- **A skill's bucket says how it's used.** `engineering/` daily code work, `productivity/` daily non-code workflow, `misc/` rarely used, `personal/` tied to my own setup, `in-progress/` drafts, `deprecated/` no longer used. Only `engineering/`, `productivity/` and `misc/` are published.
- **The skill catalogs are generated.** The lists in `README.md`, each `skills/<bucket>/README.md` and `.claude-plugin/plugin.json` come from the skills, and the one in `third-party/README.md` from `third-party/skills.json`; `scripts/build-catalog.py` writes them (format in `scripts/tooling/catalog.py`). To change an entry, change its source and rerun it. Prose outside the `skill-catalog` markers is hand-written.
- **A skill's `description` is its catalog entry.** A user-invoked description is a human-facing summary, used whole; a model-invoked one is a summary followed by trigger phrasing that starts with a "Use when…" or "Use before…" sentence, and the catalog keeps only the summary.

### Invocation

- **Every skill is user-invoked or model-invoked.** User-invoked sets `disable-model-invocation: true` and is reachable only by the human; model-invoked omits it. Definitions and description conventions: `docs/invocation.md`.
- **A skill reaches another by calling the Skill tool with it.** Only a model-invoked skill can be reached that way; a step that needs a user-invoked skill tells the user to run `/<name>`.

### Third-party skills

- **A curated skill records its `invocation` in `skills.json`.** `"user"` when its frontmatter sets `disable-model-invocation: true`, else `"model"`; lint requires it and `sync-third-party.py --check` compares it with the installed copy.
- **Curated, never vendored.** A third-party skill is an entry in `third-party/skills.json`, installed by `scripts/sync-third-party.py`; it never goes in `skills/`, the catalog or `plugin.json` ([ADR 0002](docs/adr/0002-curate-third-party-skills-instead-of-vendoring.md)).
- **A retired or declined curated skill moves to its source's `archived` list with the reason**, never out of `skills.json`.

### Authoring

- **Skills follow the [Agent Skills specification](https://agentskills.io/specification), its [best practices](https://agentskills.io/skill-creation/best-practices) and Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).** Run `scripts/lint-skills.py` after changing a skill.
- **Every rule the lint checks is listed in the module that checks it.** Authoring rules in `scripts/tooling/authoring_rules.py`, catalog and listing rules in `published_rules.py` and `catalog.py`, bucket and name rules in `skill_inventory.py`. When a guide adds a rule a script can check, add it there with a test rather than as prose here.
- **Fragile, exact operations go in the skill's `scripts/` folder**, not inline in `SKILL.md`: API calls, multi-step shell sequences. Each bundled script is tested from `tests/skill_scripts/` against the fake `gh` in `tests/skill_scripts/fake_gh.py`.

### Tooling and tests

- **One executable per command at the top of `scripts/`, shared code in the `scripts/tooling/` package.** What counts as an owned skill lives only in `scripts/tooling/skill_inventory.py`, and everything about `third-party/skills.json` only in `scripts/tooling/third_party.py`.
- **Tests live in `tests/`, never beside the code.** `tests/tooling/` for the package, `tests/skill_scripts/` for scripts bundled in skills, `tests/skills/` for checks on skill prose (rules a `SKILL.md` and its sibling files must keep).
- **Use `uv run --locked --no-build`, not `pip`.** `pyproject.toml` and `uv.lock` pin `ruamel.yaml`, the tooling's one dependency.

## Hard constraints

- **Never hand-edit a skill catalog.** Edit the skill or `third-party/skills.json` and run `scripts/build-catalog.py`; lint fails on a stale catalog.
- **Never edit `CHANGELOG.md`.** Every PR a skill's user would notice adds a `.changeset/<name>.md` with `"simonsteiner-skills": minor|patch` front matter and a prose note; CI writes the changelog on `main` ([ADR 0006](docs/adr/0006-apply-changesets-on-main-without-a-version-pr.md)).
- **Never rewrite an ADR.** Supersede it with a new one.

## Gotchas

- **The links point at this checkout's working tree.** Whatever branch is checked out is what the local agents run, and they read skill names and descriptions only at startup.
- **Don't run `scripts/sync-skills.py` or `sync-third-party.py` from inside an agent session.** The skills.sh CLI then installs to that agent alone and leaves the others on their old copies.

## Docs

- **No deploy step:** merging to `main` publishes, since skills.sh installs straight from this repo; `.github/workflows/changelog.yml` then writes `CHANGELOG.md` from the changesets ([ADR 0006](docs/adr/0006-apply-changesets-on-main-without-a-version-pr.md)).
- `README.md`: what the repo is, how to install it, and the generated skill catalog.
- `docs/setup.md`: what the sync does and when to rerun it, every check and the git hooks.
- `docs/invocation.md`: user-invoked vs model-invoked in full; read before writing a description or a cross-skill call.
- `docs/evals.md`: running a skill's evals and trigger evals; `docs/session-mining.md`: mining real sessions before writing evals or changing a description.
- `third-party/README.md`: the curated skills, why each is there, and what the sync's `--check` reports.
- `docs/adr/`: decisions; `.out-of-scope/`: ideas deliberately not built; `docs/research/`: dated research notes, not kept current.
- `docs/arch-review/`: architecture review reports, written by the `arch-review` skill.
