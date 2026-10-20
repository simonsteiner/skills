# Lefthook job catalog

Jobs to compose `lefthook.yml` from, each with the comment it carries. The versions shown are examples: look up the current one, and use the one CI already pins when it pins one.

## Contents

- [Header and install](#header-and-install)
- [Every project](#every-project)
- [Python](#python)
- [TypeScript and JavaScript](#typescript-and-javascript)
- [A subproject in its own folder](#a-subproject-in-its-own-folder)
- [Rust](#rust)
- [Markdown and spelling](#markdown-and-spelling)
- [Shell](#shell)
- [Generated files kept in sync](#generated-files-kept-in-sync)
- [Pre-push](#pre-push)

## Header and install

The file opens with the reference and the one command that installs the hooks in this project:

```yaml
# Ref: https://github.com/evilmartians/lefthook
# Install the git hooks with: uv run lefthook install
```

Then the hooks. Every job in this catalog is an entry under `commands:`, a map keyed by job name, not lefthook 2's `jobs:` list:

```yaml
pre-commit:
  parallel: true
  commands:
    ruff:
      glob: "*.py"
      run: …

pre-push:
  commands:
    test:
      run: …
```

| Project | Add lefthook | Install line |
|---|---|---|
| uv | `uv add --dev lefthook` | `uv run lefthook install` |
| npm | `npm install --save-dev lefthook` and a `prepare` script | `npm install` (the `prepare` script) |
| pnpm | `pnpm add -D lefthook` and a `prepare` script | `pnpm install` (the `prepare` script) |
| neither (Rust, C++, docs) | nothing; `uvx` fetches it | `uvx lefthook@2.2.2 install` |

The `prepare` script, in `package.json`:

```json
"scripts": { "prepare": "lefthook install || true" }
```

The header for a Node project names both ways in:

```yaml
# Installed by `npm install` (the `prepare` script); by hand: npm exec -- lefthook install
```

`|| true` keeps `npm install` working in a tarball or a CI checkout without `.git`.

## Every project

```yaml
    # Every staged file an agent writes stays under 5,000 tokens (bytes / 4), so
    # an agent can read it whole. Lockfiles, build output, binaries and generated
    # files are skipped; mark more with linguist-generated in .gitattributes.
    # On failure it prints how to split the file.
    file-tokens:
      run: python3 scripts/hooks/check-file-tokens.py --max-tokens 5000 {staged_files}
```

No `glob`: every file type counts. Lefthook skips a job whose `{staged_files}` comes out empty, so a commit that only deletes files doesn't run it.

For a repo carrying vendored or reference code, a diff check that ignores it:

```yaml
    whitespace:
      # Trailing whitespace and leftover conflict markers in the staged changes,
      # outside vendored code. Skipped while concluding a merge, whose diff
      # carries upstream's lines too.
      skip: merge
      run: git diff --cached --check -- . ':!third_party/'
```

## Python

```yaml
    # One job, not two: two fixers rewriting the same files at once undo each
    # other's fixes. --force-exclude: ruff skips its configured excludes only for
    # files it finds itself, not for files named on the command line.
    ruff:
      glob: "*.py"
      run: uv run ruff check --fix --force-exclude {staged_files} && uv run ruff format --force-exclude {staged_files}
      stage_fixed: true

    # The whole project, not the staged files: a file's errors depend on what it
    # imports. The paths come from [tool.mypy] in pyproject.toml.
    mypy:
      glob: "*.py"
      run: uv run mypy
```

When mypy has no configured `files`, name them: `uv run mypy src tests`. A `*.pyi` stub beside its `*.py` makes mypy stop on a duplicate module when both are passed, so keep mypy's glob to `*.py`. Folders mypy must not see (throwaway experiments, one-off scripts) go in its config's `exclude`, or in the job's `exclude:` list when mypy runs on staged files.

A test suite that finishes in a few seconds can run on every commit; anything slower goes to [pre-push](#pre-push):

```yaml
    # Fast enough for every commit (~3 s).
    pytest:
      glob: "*.py"
      run: uv run pytest -q
```

## TypeScript and JavaScript

```yaml
    # Whole project, not just the staged files: tsc only applies tsconfig.json
    # when it is given no file arguments.
    typecheck:
      glob: "*.{ts,tsx}"
      run: npm run typecheck

    # Lints and formats; config in biome.json. Markdown is left to rumdl.
    biome:
      glob: "*.{ts,tsx,js,mjs,json,jsonc,css}"
      run: npx @biomejs/biome@2.5.15 check --write --no-errors-on-unmatched --files-ignore-unknown=true {staged_files}
      stage_fixed: true
```

A project on eslint and prettier instead of biome: eslint reads, prettier is the one fixer.

```yaml
    eslint:
      glob: "*.{ts,tsx,astro}"
      run: npm exec -- eslint {staged_files}

    # Deliberately not Markdown: rumdl fixes that, and two fixers fight.
    prettier:
      glob: "*.{ts,tsx,astro,js,mjs,json,css}"
      run: npm exec -- prettier --write {staged_files}
      stage_fixed: true
```

An Astro project adds `astro check` (whole project; eslint doesn't resolve names across an `.astro` file's frontmatter and its client script):

```yaml
    astro-check:
      glob: "*.astro"
      run: npm run check
```

## A subproject in its own folder

A Python repo with a website in `web/`: `root:` runs the job from that folder and hands it paths relative to it, so the folder's own tools and configs answer.

```yaml
    web-lint:
      root: "web/"
      glob: "*.{ts,tsx,astro,mjs}"
      run: npm exec -- eslint {staged_files}

    web-test:
      root: "web/"
      glob: "*.{ts,tsx,astro,mjs}"
      # node_modules is not committed: a fresh checkout installs once.
      run: (test -d node_modules || npm ci --silent) && npm test --silent
```

## Rust

```yaml
    rustfmt:
      glob: "*.rs"
      run: cargo fmt -- {staged_files}
      stage_fixed: true

    # Whole crate rather than the staged files: clippy lints a crate, not a file.
    clippy:
      glob: "*.rs"
      run: cargo clippy --all-targets -- -D warnings
```

When `rustfmt.toml` uses unstable options, pin the nightly CI uses (`cargo +nightly-2025-10-18 fmt`) and put the one-time `rustup toolchain install` command in the job's comment.

## Markdown and spelling

```yaml
    # The only fixer of *.md, so it can run beside cspell, which reads the same
    # files. Config and excludes in .rumdl.toml; an excluded staged file is
    # skipped, not an error.
    rumdl:
      glob: "*.md"
      run: uv run rumdl check --fix {staged_files}
      stage_fixed: true
```

In a Node project: `npx rumdl@0.3.0 check --fix {staged_files}`, the same version as `package.json`. With neither: `uvx rumdl@0.3.0 check --fix {staged_files}`.

```yaml
    # Generated data is excluded via cspell.json's ignorePaths. Project words go
    # in cspell-dictionary.txt.
    cspell:
      glob: "*.{py,ts,md,txt,toml,yml,yaml,json}"
      run: npx --yes cspell@10.4.0 --no-progress --no-must-find-files --config cspell.json {staged_files}
```

## Shell

```yaml
    # Same as CI's shellcheck step.
    shellcheck:
      glob: "*.sh"
      run: shellcheck {staged_files}
```

## Generated files kept in sync

When a committed file is derived from another one, regenerate it in the hook. `stage_fixed` only restages the job's own `{staged_files}`, so a file outside them is added by hand:

```yaml
    # The Cloud Function installs src/requirements.txt; keep it the lock file's
    # runtime dependencies.
    requirements:
      glob: "{pyproject.toml,uv.lock}"
      run: uv export --no-dev --no-hashes --no-emit-project --no-header -q -o src/requirements.txt && git add src/requirements.txt
```

## Pre-push

The full test suite, and anything else over ~10 seconds:

```yaml
pre-push:
  commands:
    test:
      run: uv run pytest   # or: npm test, cargo test
```
