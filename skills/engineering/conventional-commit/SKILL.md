---
name: conventional-commit
description: >
  Write Conventional Commits v1.0.0 messages and make the commits — one, or several atomic ones when the work spans concerns. Use before running any `git commit`, including when the user says "commit", "commit and push", "commit in logical chunks", "commit this to a new branch", or when another workflow (review fixes, refactors, releases) reaches its commit step. Also use when asked to write or improve a commit message.
---

# Conventional Commit

Turn the current worktree into **Conventional Commits v1.0.0**-compliant commits (staged changes; fall back to unstaged tracked changes if nothing is staged). Spec: https://www.conventionalcommits.org/en/v1.0.0/

**Pick the mode from what was asked:**

- **Commit** — the user said "commit" in any form, or the commit is a step in a larger task. Write the message(s) and run `git commit` (Step 4). This is the usual case.
- **Message only** — the user asked for a message, wording help, or a review of one. Present it and stop (Step 5).

Push only when the push was asked for too ("commit and push").

For more examples and edge cases, see `references/commit-examples.md`.

---

## Step 1 — Gather worktree information

Run these in the repository root (default to the current working directory):

```bash
# everything in play, including new untracked files the diffs below don't show
git status --short
# staged = what would commit now
git diff --cached --stat && git diff --cached
# unstaged = what would commit if staged
git diff --stat && git diff
# recent log = match the repo's style
git log --oneline -10
# branch = may hold a ticket id
git rev-parse --abbrev-ref HEAD
```

- If something is staged, the user chose it — commit that, and leave the rest alone unless asked.
- If nothing is staged, the work is the unstaged diff plus the untracked files that belong to it. In message-only mode, say nothing is staged.
- If there are no changes at all, say so and stop.
- Skim `git log` to match this repo's conventions (scope usage, body style) rather than imposing a generic style.

---

## Step 2 — Analyse the changes

Before writing, silently answer:

1. **What changed?** — files touched, additions/removals, patterns.
2. **Why?** — infer intent from the code, file names, branch, and recent log.
3. **Primary concern?** — if many things changed, pick the single dominant one.
4. **Scope?** — which module/subsystem is affected.
5. **Breaking?** — does this change a public contract or behaviour callers rely on?

If the worktree mixes logically unrelated changes, plan one commit per concern — in commit mode that's what gets committed (Step 4), in message-only mode it's a message for each. Each commit should be atomic and self-consistent. "Commit in logical chunks" asks for exactly this; a single commit for everything is the wrong answer to it.

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

## Step 4 — Commit

Pass the message through a quoted heredoc, so the body reaches git exactly as written — no shell expansion, no `-m` per paragraph:

```bash
git commit -F - <<'EOF'
feat(scope): short imperative description

- What changed and why, on one line however long it runs.
- Caveats or context.

Closes #123
EOF
```

Harness-required trailers (e.g. `Co-Authored-By:`) go in the footer block, after any issue refs.

**Several commits.** Commit the planned groups in dependency order — a commit never references something only a later one adds. For each group:

```bash
git add -- <paths of this concern>
git diff --cached --stat    # check the group before committing it
git commit -F - <<'EOF'
...
EOF
```

- Stage by path. `git add -p` is interactive and won't work here.
- A file holding two concerns: commit it whole with the dominant one and mention the other in the body — unless the separation matters (a fix that must be revertible alone). Then stage just its hunks non-interactively: `git diff -- <file> > /tmp/hunks.patch`, cut the patch down to the hunks you want, `git apply --cached /tmp/hunks.patch`.
- Never fold in files the user didn't touch in this work (stray build output, someone else's edits). Leave them unstaged and say so.

**Verify** after the last commit:

```bash
git log --format='%h %s' -n <N>     # headers as intended, ≤ 72 chars
git log -1 --format=%B              # body unwrapped
git status --short                  # nothing left behind by accident
```

If a body came out hard-wrapped, `git commit --amend -F -` it before pushing — never after.

---

## Step 5 — Message only

Output the full message in a single code block so it's copy-pasteable:

```
feat(scope): short imperative description

- What changed and why.
- Caveats or context.

Closes #123
```

For a planned split, one code block per commit, in commit order, each with the paths it covers.

---

## Rules of thumb

- Specific beats vague: `fix(parser): handle empty input in tokenise()` over `fix: bug`.
- Never invent changes not present in the diff.
- For very large diffs (>500 lines), summarise by file/module, not line by line.
- One logical change per commit; never commit known-broken code.
- The no-hard-wrap rule is the one most often broken by habit. Check the body before committing, not after pushing.
