# AGENTS.md format

Every line of `AGENTS.md` is read on every request. Aim for under 150 lines; past 200, adherence drops.

## Sections, in order

1. **H1 that names the project** (`# Acme Billing`, never `# AGENTS.md`), then three sentences: the major pieces and how they talk to each other. End with one line pointing to `GLOSSARY.md` and `docs/adr/`.
2. **Commands** — one fenced block, one command per line with a short trailing `# comment`. Don't pad comments into a column or leave blank lines between groups. Include the single-file forms (one test file, one lint target) next to the full runs. Only commands that exist in the manifest or task runner; run each one you're unsure of.
3. **Conventions** — "X lives only in Y, never re-implement" bullets, grouped by area under `###` headings. Use nested bullets when one bullet holds several rules. Point to a canonical example as `path/to/file.ts`, never paste the code.
4. **Hard constraints** — what never happens (edit generated files, push schema to prod, send secrets to the client), and what needs the user's approval first (new dependencies, migrations, deleting data).
5. **Gotchas** — what every new engineer trips on, including dev-environment rules ("the dev server is already running, don't start another").
6. **Docs** — a bullet list of where each kind of doc lives, with one line on when to read it. Not a table.

No contents line: the headings are enough in a file this short.

## Include

- commands, with the exact tool ("`uv`, not `pip`")
- conventions and "we use X, not Y"
- hard constraints and approval boundaries
- gotchas

## Exclude

- the file tree, and API or feature descriptions the code already shows
- style rules a linter, formatter or type checker enforces
- history and anecdotes ("this used to…", "PR #N broke…"): keep the rule, drop the story
- changelogs
- rules the code doesn't follow (check them, e.g. version pins against the manifest)
- long rationale: link the ADR instead
- secrets, credentials and production hostnames

## Bullets

Bold lead, then one or two sentences. One fact per bullet.

```markdown
- **Money is integer cents.** `src/money.ts` is the only place that converts to and from display strings; never use floats for amounts.
```

Not:

```markdown
- We had a bug in 2024 where floats caused rounding errors in invoices, so we decided to switch to cents, and now all money handling should go through the money module, which also formats currencies.
```
