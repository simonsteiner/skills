---
name: conventional-commit
description: >
  Generate a Conventional Commits v1.0.0 message (header + body + footers) from the current worktree state. Use when asked to write or improve a commit message, or before committing staged changes.
---

# Conventional Commit Message Generator

Produce a **Conventional Commits v1.0.0**-compliant commit message for the current worktree (staged changes; fall back to unstaged tracked changes if nothing is staged). Spec: https://www.conventionalcommits.org/en/v1.0.0/

For more examples and edge cases, see `references/commit-examples.md`.

---

## Step 1 — Gather worktree information

Run these in the repository root (default to the current working directory):

```bash
# staged = what would commit now
git diff --cached --stat && git diff --cached
# unstaged = what would commit if staged
git diff --stat && git diff
# recent log = match the repo's style
git log --oneline -10
# branch = may hold a ticket id
git rev-parse --abbrev-ref HEAD
```

- If `git diff --cached` is empty, base the message on the unstaged diff and tell the user nothing is staged.
- If both diffs are empty, tell the user there are no changes and stop.
- Skim `git log` to match this repo's conventions (scope usage, body style) rather than imposing a generic style.

---

## Step 2 — Analyse the changes

Before writing, silently answer:

1. **What changed?** — files touched, additions/removals, patterns.
2. **Why?** — infer intent from the code, file names, branch, and recent log.
3. **Primary concern?** — if many things changed, pick the single dominant one.
4. **Scope?** — which module/subsystem is affected.
5. **Breaking?** — does this change a public contract or behaviour callers rely on?

If the worktree mixes logically unrelated changes, flag it and suggest splitting into separate commits (offer a message for each). Each commit should be atomic and self-consistent.

---

## Step 3 — Write the message

Structure (each part separated by a blank line):

```
<type>[(scope)][!]: <description>

[body]

[footer(s)]
```

### Header (≤ 72 chars)

**Type** — required, lowercase, one of:

| type     | when to use |
|----------|-------------|
| feat     | a new feature (correlates with SemVer MINOR) |
| fix      | a bug fix (correlates with SemVer PATCH) |
| refactor | code change that neither fixes a bug nor adds a feature |
| perf     | performance improvement |
| test     | adding or correcting tests |
| docs     | documentation only |
| style    | formatting/whitespace, no logic change |
| build    | build system or dependencies |
| ci       | CI configuration and scripts |
| chore    | maintenance, tooling, config (no src behaviour change) |
| revert   | reverts a previous commit |

**Scope** — optional, lowercase noun in parentheses, naming a section of the codebase: `feat(auth):`. Use scopes that match this repo (e.g. `auth`, `api`, `db`, `ai`, `sync`, `views`). Omit when the change is genuinely cross-cutting.

**Description** — required. Imperative mood ("add", not "added"/"adds"), lowercase first letter, no trailing period. State the change, not the file.

### Body — optional, recommended for non-trivial changes

- Explain **what** and **why**, not how (the diff shows how).
- Be as long as it needs to be to say what changed — don't truncate for length.
- Free-form; one blank line after the header.
- Lowercase first letter, no trailing period.
- Use `-` bullets for multiple distinct points.
- **Do not hard-wrap body lines.** Write each bullet or paragraph as one continuous line and let the editor soft-wrap it — never insert manual newlines at ~72 chars or any other column. The ≤ 72 char limit applies only to the header; body and footer lines run as long as they need to. (A multi-line bullet wraps only because the content has a real line break, not to hit a width.)

### Footers — optional

One per line, `Token: value` (use `-` instead of spaces in the token, except `BREAKING CHANGE`). Examples:

- Issue refs: `Closes #42`, `Fixes #123`, `Refs PROJ-7`
- Trailers: `Co-authored-by: Name <email>`, `Reviewed-by: Name <email>`
- If the branch encodes a ticket (e.g. `feature/PROJ-42-login`), add `Refs PROJ-42`.

### Breaking changes

Mark **either** way (both is fine):

- A `!` before the colon: `feat(api)!: drop legacy /login endpoint`
- A `BREAKING CHANGE:` footer describing the break and migration path.

A `BREAKING CHANGE` footer correlates with a SemVer MAJOR bump and may appear on any type, not just `feat`/`fix`.

```
feat(api)!: require client_id on the auth endpoint

BREAKING CHANGE: /api/auth now rejects requests without client_id. Add client_id to every auth call before upgrading.
```

---

## Step 4 — Present the result

Output the full message in a single code block so it's copy-pasteable:

```
feat(scope): short imperative description

- What changed and why.
- Caveats or context.

Closes #123
```

Do not run `git commit` unless the user asks.

---

## Rules of thumb

- Specific beats vague: `fix(parser): handle empty input in tokenise()` over `fix: bug`.
- Never invent changes not present in the diff.
- For very large diffs (>500 lines), summarise by file/module, not line by line.
- One logical change per commit; never commit known-broken code.
