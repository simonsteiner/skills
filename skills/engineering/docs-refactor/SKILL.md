---
name: docs-refactor
description: Refactors a repo's docs so each kind of knowledge has exactly one home — README, setup, deployment, .env.example, glossary, ADRs — fixes every claim the code contradicts, and rewrites the agent instructions into a short, high-signal AGENTS.md. Stages the result on a new branch with a report and a PR body.
disable-model-invocation: true
---

# Docs Refactor

Give every kind of knowledge exactly one home, make every doc agree with the code, and cut the agent instructions down to what earns its tokens on every request.

**Trace every line.** Each rule that ends up in `AGENTS.md` comes from an existing doc, the code, or an answer from the user. Never invent a convention: an agent-written instruction file that guesses spreads its mistakes into every later session.

---

## Step 1 — Branch

Call the Skill tool with "sync-and-branch" to cut `docs/refactor-docs` from the fresh default branch. Everything below happens there.

---

## Step 2 — Inventory

List every doc and every instruction file:

- root `*.md`, `docs/`, READMEs in subfolders, `.env.example`, setup scripts
- `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` and nested copies in subfolders, `.claude/rules/`
- `GLOSSARY.md`, `GLOSSARY-MAP.md`, `CONTEXT.md`, `docs/adr/`

For each, note who reads it (agent or human), what it repeats from another doc, and what is stale. Check claims against the code, the project manifest or task runner (`package.json`, `pyproject.toml`, `Makefile`, `justfile`, …), the CI config and the deploy config. A doc that disagrees with the code is a bug: fix the doc and record the claim, the evidence and the fix for the report. When the code looks wrong instead, don't change it; ask.

Also record instructions that contradict each other across files: an agent given both picks one arbitrarily.

---

## Step 3 — Glossary

First get to one file:

- Only `CONTEXT.md` exists → `git mv` it to `GLOSSARY.md`.
- Both exist → merge the `CONTEXT.md` terms into `GLOSSARY.md` and `git rm CONTEXT.md`.
- Neither exists → call the Skill tool with "domain-modeling" and build `GLOSSARY.md` from the domain terms the inventory turned up. Write each term you can settle from the docs and code; ask the user only where two words compete for one concept or the code and docs disagree on its meaning.

Then, however `GLOSSARY.md` came about, keep domain terms only: the term, its definition, the words to avoid. Move file paths, function names, env vars and implementation details out. A detail that is a rule goes to `AGENTS.md`; one the code already shows is dropped.

---

## Step 4 — One home per kind

Adapt this to what exists. Create a file only when there is content for it.

- **`AGENTS.md`** — rules for changing the code, written in Step 5. Leave one `AGENTS.md` and no `CLAUDE.md` or `.claude/CLAUDE.md` in the root and in every subfolder that has one:
  - No `AGENTS.md` there yet → `git mv` the `CLAUDE.md` (or `.claude/CLAUDE.md`) to `AGENTS.md` and merge the other one into it.
  - `AGENTS.md` already there → merge each `CLAUDE.md` into it, dropping one that only imports `@AGENTS.md`, and `git rm` it.

  Claude Code reads `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` sits in the working directory or above it, and a subfolder's `AGENTS.md` only when that subfolder has none of its own. So a leftover nested `CLAUDE.md` hides both. Warn in the report when a `CLAUDE.local.md` exists.
- **`README.md`** — what the project is, a quickstart of at most ten lines, a list of links to the other docs. No setup steps repeated from `docs/setup.md`.
- **`docs/setup.md`** — local setup step by step, configuration options, troubleshooting.
- **`docs/deployment.md`** — operating production: release flow, where secrets live (never their values), scaling. Only if the project deploys somewhere.
- **`.env.example`** — the only annotated list of env vars. Other docs point to it.
- **`GLOSSARY.md`** — from Step 3.
- **`docs/adr/`** — hard-to-reverse decisions with their trade-offs. Keep the existing ones.

Then:

- Delete obsolete bootstrap prompts and scratch docs that contradict the code; git history keeps them.
- Leave generated reports and dated historical records alone, even when they mention old file names.
- Update every reference to a renamed or moved file: code comments, CI, lint config, other docs. `git grep` each old path and filename before moving on.

---

## Step 5 — Write AGENTS.md

`AGENTS.md` is loaded into context on every request. Write it to [AGENTS-FORMAT.md](AGENTS-FORMAT.md), starting from [assets/agents-template.md](assets/agents-template.md). Sort every candidate rule first:

- **Applies to every task** → `AGENTS.md`.
- **Applies to one directory** → a nested `AGENTS.md` in that directory.
- **A multi-step procedure for one kind of task** → a doc under `docs/` that `AGENTS.md` links with one line on when to read it.
- **Enforced by a linter, formatter or type checker** → nowhere; the tool already says it.
- **Anything else** → dropped. Note each one with a reason for the report.

Mark every hard constraint a hook or a permission deny could enforce. Instructions are context, not enforcement, so the report suggests those as follow-ups.

---

## Step 6 — Check

1. Run the repo's formatters and Markdown linters on every changed doc.
2. `git grep` every old path one more time; only historical records may still name it.
3. **Cold read.** Spawn a fresh sub-agent that reads only the new `AGENTS.md` and answers four questions without opening other files: how to run one test file, where a core concern lives (pick one from the conventions), one thing it must never do, and which doc covers deployment. Fix `AGENTS.md` for each answer it gets wrong or can't give.

---

## Step 7 — Stage and report

Stage everything with `git add`; don't commit. Then report:

- **Moved:** what moved where.
- **Deleted:** what, and why.
- **Wrong against the code:** each claim, the evidence, and the fix.
- **Enforce, don't instruct:** the hard constraints a hook or a permission deny could enforce.
- **Warnings:** a `CLAUDE.local.md` that hides `AGENTS.md`, contradictions you couldn't settle, questions still open.

Call the Skill tool with "pr-body" and draft the PR body as a refactor. Put everything dropped from the agent instructions under `## Not done`, one line each with its reason, so the user can restore a rule once an agent gets it wrong twice. Print the draft at the end of the report.
