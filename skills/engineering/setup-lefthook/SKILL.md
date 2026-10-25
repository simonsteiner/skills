---
name: setup-lefthook
description: >
  Sets up lefthook git hooks in a project — installs lefthook the way the stack expects, writes a lefthook.yml whose pre-commit jobs fix and check only what's staged, and adds a per-file token budget that blocks oversized agent-written files with instructions for splitting them. Use when the user wants pre-commit or pre-push hooks, asks to add or set up lefthook, wants lint, format or type checks on commit, or wants to stop agents committing huge files.
---

# Setup Lefthook

Give a project git hooks that catch on commit what CI would catch later, in a few seconds, without fighting each other. CI stays the gate; the hooks are the early warning.

---

## 1. Read the project

Before writing a line, find out:

- **Stack and package manager**: `uv.lock` / `pyproject.toml`, `package.json` with `package-lock.json` or `pnpm-lock.yaml`, `Cargo.toml`. A second stack in a subfolder (`web/package.json` in a Python repo) gets its own jobs with `root:`.
- **What CI runs**, in `.github/workflows/`: each lint, format, type and test step, and the version it pins. A hook runs the same command at the same version; say so in its comment ("Same as CI's ruff step; bump the version in both places").
- **Tool configs already there**: `ruff.toml` / `[tool.ruff]`, `[tool.mypy]` / `mypy.ini`, `biome.json`, `tsconfig.json`, `.rumdl.toml`, `cspell.json`. Hook what the project uses. For a project with nothing yet, the baseline is: Python → ruff, mypy, pytest on push; TypeScript → biome, tsc, tests on push; every project → rumdl for Markdown and the token budget.
- **SonarQube**: `sonar-project.properties`, `.sonarlint/connectedMode.json`, a SonarQube or SonarCloud step in CI, or a Sonar check on PRs. A Sonar project gets the catalog's [SonarQube](references/JOBS.md#sonarqube) job. A `sonar integrate git` hook already installed (a global `core.hooksPath` pointing at Sonar's hooks, or a `# sonar:begin` block in `.husky/`) is replaced by that job, the same as any other existing hook.
- **Existing hooks**: `.husky/`, `.pre-commit-config.yaml`, `core.hooksPath`. Carry their checks over and remove the old setup in the same change, or both run.

---

## 2. Install lefthook

As a dev dependency of the project, so every clone gets the same version. The install commands per package manager, and the header line that names the right one, are in [references/JOBS.md](references/JOBS.md#header-and-install). In a Node project the `prepare` script installs the hooks on `npm install`; elsewhere, run the install command once yourself.

---

## 3. Write `lefthook.yml`

Compose it from the jobs in [references/JOBS.md](references/JOBS.md). These rules are what the catalog's jobs already follow; hold any job you add to them:

- **`parallel: true`, no `priority`.** Lefthook ignores `priority` under `parallel`, so a `priority:` key only suggests an order that doesn't exist.
- **One fixer per file type.** Two fixers rewriting the same file at once undo each other's work. When one tool both fixes and formats, chain both steps in one job (`ruff check --fix … && ruff format …`). Readers (cspell, a type checker) can run beside the fixer.
- **Every fixer has `stage_fixed: true`**, so its fixes land in the commit instead of being left unstaged.
- **`{staged_files}` for per-file tools; the whole project for cross-file ones.** mypy, tsc, clippy, a repo-wide linter and tests give different answers on a subset, so they run whole and keep a `glob:` only to decide whether they run at all. The comment says which, and why.
- **Excludes live in the tool's own config** (`.rumdl.toml`, `cspell.json`'s `ignorePaths`, mypy's `exclude`), so the hook, CI and the editor agree. A tool that applies them only to files it finds itself gets the flag that applies them to named files too (ruff's `--force-exclude`). A lefthook `exclude:` is for a tool that can't express it.
- **Slow goes to pre-push.** A test suite over ~10 seconds runs in `pre-push`, not on every commit.
- **One-off runners pin a version**: `uvx tool@1.2.3`, `npx --yes tool@1.2.3`. Project tools run through the project (`uv run`, `npm exec --`), which already pins them.
- **A comment says why, not what**: where the config lives, why this job runs whole, why it's a separate job. A job whose `run:` line explains itself gets none.

---

## 4. Add the token budget

Every project gets a pre-commit job that blocks any staged file over 5,000 tokens (bytes / 4), so no file grows past what an agent can read whole. [scripts/check-file-tokens.py](scripts/check-file-tokens.py) does it; it's stdlib Python, so it works in a Node or Rust repo too. Projects don't copy it: lefthook fetches it from this skill's repo as a `remotes:` entry pinned to a `filetokens.v*` tag, so every repo runs the same reviewed version.

1. Add the `remotes:` entry, the `file-tokens` job and `min_version: 2.0.5` from the catalog's [Every project](references/JOBS.md#every-project) section. The job goes in the project's own `lefthook.yml`, never only in the remote: that way a clone that can't fetch the remote fails the commit instead of skipping the check, and the project sets its budget in the job's `args:` (`--max-tokens 5000`). No `glob:`: every file type counts.
2. Run `lefthook install` once (in a Node project, `npm install` does it through `prepare`). The first hook run clones the tag into `.git/info/lefthook-remotes/`; after that it works offline.

`ref:` takes a tag, never a commit SHA: lefthook clones with `--branch`, so a SHA fails. The tags have no `-` or `/` in them (`filetokens.v1.0.0`, not `file-tokens-v1.0.0`) because of how lefthook recovers from a failed fetch. It falls back to the clone it has cached, but reads the ref back from the escaped directory name, so for a ref with `-` or `/` it finds no clone, deletes the cached one, and every commit fails with `script does not exist` until the new `ref:` can be fetched. To update, change `ref:` to the new tag; the next commit in each clone fetches it, and one that can't (offline, tag not pushed yet) keeps running the previous version.

**A project that already has a copy** (`scripts/hooks/check-file-tokens.py`, sometimes `tools/hooks/`): delete it in the same change, and replace its `file-tokens` command with the catalog's job, keeping the `--max-tokens` it passed. Drop the folder if nothing else lives in it, and anything that pointed at the copy (a ruff or cspell exclude, a README line). Add `".git/**"` to the `exclude` list in `.rumdl.toml` (see the catalog), and the remote's words (`filetokens`, `simonsteiner`) to the cspell dictionary when cspell checks `*.yml`.

It measures the staged content, not the working tree, and skips what no agent writes: lockfiles, minified bundles, source maps, snapshots, tabular and geographic data (`*.csv`, `*.geojson`, `*.jsonl`, …), anything under `vendor/` or `third_party/`, binaries (including PDFs and other non-UTF-8 files), files `.gitattributes` marks `linguist-generated` or `linguist-vendored`, and files whose first lines carry a codegen header (`@generated`, or a comment saying `DO NOT EDIT` or opening with `auto-generated` / `generated by`; a comment or prose that only mentions generated code doesn't count). Codegen output the script doesn't recognize gets a `.gitattributes` line (`src/api/schema.ts linguist-generated`), never a raised budget.

When it fails, it lists each file with its size and how many files to split it into, then gives the steps: split along the seams (classes, functions, components, `##` sections that change together) into modules named for what they do, update the imports, split the tests the same way, turn long Markdown into an overview linking to parts, move data out of code, and never minify or `--no-verify` to get under.

**Files already over the budget** fail the next commit that touches them, not every commit. Run the job over every tracked file (`lefthook run pre-commit --job file-tokens --all-files`, through the project's lefthook: `uv run lefthook …`, `npm exec -- lefthook …`) and sort what's over into two groups:

- **Not written by hand**: pipeline output (transcripts, reports, exported docs), data the script can't tell from authored files (`*.json`, `*.txt`, `*.html` fixtures and examples), vendored code outside a `vendor/` folder, a tool-written `CHANGELOG.md`, and dated records that are never split, such as single-file arch-review reports (`docs/arch-review/YYYY-MM-DD-<slug>.md`). Mark them in `.gitattributes` in this change, one pattern per folder rather than per file (`transcripts/** linguist-generated`, `js/lib/** linguist-vendored`), with a comment saying what writes them. A folder that also holds files that should stay checked gets one line per file instead: arch-review reports by file name, since reports written as folders keep every file under the budget. Ask when it's unclear whether a person edits a file.
- **Written by hand**: source, tests and docs. Report them with their sizes, so the user knows what's coming. Splitting them is separate work; offer it, don't do it in this change.

---

## 5. Prove it works

```bash
uv run lefthook validate          # or: npm exec -- lefthook validate
uv run lefthook run pre-commit --all-files
```

The first run clones the token-budget remote, so it needs network once. Every job should pass or fail for a real reason; fix the config until a clean tree passes. Then stage a file over the budget, run `lefthook run pre-commit`, confirm it fails with the split instructions, and unstage it.

Mention the hooks in the README's development section: what runs on commit, what on push, and how to skip once (`LEFTHOOK=0 git commit …`, for emergencies).

Report the jobs added and which run whole versus on staged files, any old hook setup removed, and the files already over the budget.
