Skills are organized into bucket folders under `skills/`:

- `engineering/` — daily code work
- `productivity/` — daily non-code workflow tools
- `misc/` — kept around but rarely used
- `personal/` — tied to my own setup, not promoted
- `in-progress/` — drafts not yet ready to ship
- `deprecated/` — no longer used

Currently only `engineering/` holds skills; the other buckets have been emptied but the taxonomy is kept so they can be reintroduced later.

Every skill in `engineering/`, `productivity/`, or `misc/` must have a reference in the top-level `README.md` and an entry in `.claude-plugin/plugin.json`. Skills in `personal/`, `in-progress/`, and `deprecated/` must not appear in either.

Each skill entry in the top-level `README.md` must link the skill name to its `SKILL.md`.

Each bucket folder has a `README.md` that lists every skill in the bucket with a one-line description, with the skill name linked to its `SKILL.md`. Bucket `README.md`s and the top-level `README.md` group entries into **User-invoked** and **Model-invoked**.

Third-party skills are **curated, never vendored**: they are listed in [`third-party/skills.json`](./third-party/skills.json) and installed from their own upstream repos by [`scripts/sync-third-party.py`](./scripts/sync-third-party.py). Never copy one into `skills/`, the top-level `README.md` skill list, or `.claude-plugin/plugin.json` — those describe only the skills this repo owns and publishes. A curated skill's name must not collide with a skill under `skills/`. Retired curated skills move to their source's `archived` list in `skills.json`, with the reason, rather than being deleted from it. See [docs/adr/0002-curate-third-party-skills-instead-of-vendoring.md](./docs/adr/0002-curate-third-party-skills-instead-of-vendoring.md).

Every `SKILL.md` is either user-invoked (`disable-model-invocation: true`, reachable only by the human) or model-invoked (model- or user-reachable). For the full definitions, description conventions, and why a user-invoked skill can invoke model-invoked skills but never another user-invoked one, see [docs/invocation.md](./docs/invocation.md).

Skills follow Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). Run `scripts/lint-skills.py` after changing a skill; CI runs it too. Fragile, exact operations (API calls, multi-step shell sequences) go in a skill's `scripts/` folder rather than inline in `SKILL.md`.

Every PR that changes something a user of these skills would notice adds a changeset (`npx changeset`, or a `.changeset/<name>.md` with `"simonsteiner-skills": minor|patch` front matter and a prose note). CI writes pending changesets into `CHANGELOG.md` on `main`; don't edit the changelog by hand. See [docs/adr/0006-apply-changesets-on-main-without-a-version-pr.md](./docs/adr/0006-apply-changesets-on-main-without-a-version-pr.md).
