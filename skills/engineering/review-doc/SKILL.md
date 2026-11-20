---
name: review-doc
description: Reviews a design doc, plan, RFC or spec with fresh sub-agents that never saw the conversation behind it — a paraphrase test, a simplicity-and-reuse check against the code, and an implementation-readiness check — then settles the findings with you, edits the doc, and repeats until two rounds in a row come back clean.
disable-model-invocation: true
---

# Review Doc

The thread that helped write a plan can't review it: it fills every gap from memory. A reader who sees only the written doc can't do that, so every gap they hit is one the next human reader hits too. This skill sends the doc to such readers, and keeps the judgment, what's a real gap and what to change, with this thread and the user.

Fresh means no conversation, not no evidence: reviewers read the doc, the files it links, and the code.

Each round costs one sub-agent per lens, and a doc with findings takes at least three rounds to converge. Say so when the doc is a few lines long; a short plan may not need this.

---

## Step 1 — Pin the doc

- **Target.** A path the user gave → that file. None → the doc this thread just wrote or edited, if there's exactly one; otherwise ask for the path. A plan that exists only in chat is saved first, to the path the user names or else `.scratch/<slug>.md`, since a reviewer reads only files.
- **Reading list.** Every relative link in the doc that resolves to an existing file inside the repo. Links that leave the repo, and URLs: list them and ask which to include. Save each included URL's page to `.scratch/` and list the saved file, so every reviewer can read it. Add any files the user names.
- **Never on the list:** a summary of the conversation, the brief the doc came from, or notes on what the author meant. That's the context the review exists to remove.
- **Baseline.** If the doc has uncommitted changes, say the review edits on top of them; `git diff -- <doc>` at the end then shows both.

---

## Step 2 — Pick the lenses

Read the doc once to pick. From [LENSES.md](LENSES.md):

- **Paraphrase** — always.
- **Simplicity** — when the doc proposes something to build or change in a codebase.
- **Readiness** — when the doc has an implementation plan (a section like *Implementation plan*, *Steps*, *Work breakdown*, *Tasks*), or the user says it's about to be built.

Say which lenses run and why the others don't; don't ask. The user can add or drop lenses, or give a standard a lens should apply (a team's RFC template), and that wins.

---

## Step 3 — Run a round

Spawn one fresh sub-agent per lens, in parallel. Start each one empty, never as a fork or with inherited context, and give it only:

- the doc's path, the reading list, and the repo root
- its lens section from LENSES.md, copied verbatim
- the settled list (Step 5) from earlier rounds, so it doesn't raise those again
- these rules: read-only (edit, write and change nothing); every finding gives a severity (**Blocker**, **Major**, **Nit**), the heading or line range, a quote, what's wrong, and what would fix it; return findings only, no praise and no summary beyond what the lens asks for

Use the session's model: a doc review is judgment, not lookup. A sub-agent that errors, times out or returns nothing is relaunched once. One that fails again is **not run** for that round; never count a lens that didn't run as a lens with no findings.

---

## Step 4 — Verify and settle

**Verify.** Open the doc at each finding's line and, for a claim about code, the code. Drop a finding you can't ground, and note why for the report. Merge duplicates across lenses, keeping the higher severity.

**Check the paraphrase.** Compare the Paraphrase lens's two paragraphs with what the doc is meant to say, as this thread and the user know it. A wrong paraphrase is a Blocker on the section it got wrong, even when every term was defined.

**Give each finding one verdict:**

| Verdict | When | What follows |
|---------|------|--------------|
| fix | the finding is right | edit the doc |
| contest | the finding is wrong, and a line or file shows it | record the evidence; no edit |
| needs a decision | the fix is a choice between designs or a scope call, or the evidence lives only in someone's head | ask the user |
| decline | a Nit not worth the edit, or context only a zero-history reader would need | record why; no edit |

**Contest only with evidence:**

- Cite what the reviewer could have read: a line in the doc, a file and symbol in the repo. "This was intentional" isn't evidence; that's *needs a decision*.
- Never contest a comprehension gap. If a fresh reader couldn't follow a section, the doc is missing something, even when the reader's conclusion was wrong.
- Don't lower a severity on the way to a fix. Disagree with a Blocker by contesting it, out loud.
- This thread wrote or shaped the doc. Wanting the reviewer to be wrong is not evidence that they are.

**Edit straight away** for each *fix* that doesn't change a decision: a missing definition, a fact taken from the code, a step spelled out, a wrong path. Fix the gap in the doc's own voice and structure; don't rewrite the section around it. A fix that changes a decision (a different design, a dropped feature, a new requirement) is *needs a decision*.

**Ask the decisions together**, once per round, with the structured question tool when there is one. Each question names the finding and quotes the doc, gives the options, and says which you'd pick and why. Apply the answers.

The doc is the only file this skill edits, apart from what it saves to `.scratch/`. Never touch code, even when a finding shows the code is wrong; put that in the report.

---

## Step 5 — Loop until clean

Keep a **settled list** across rounds: each finding contested, declined or decided against, with its scope. A later round that raises a settled finding again (same scope, same issue) doesn't reopen it. A finding that comes back after a *fix* does: the fix didn't work.

A round is **clean** when every lens ran and none raised a Blocker or Major that isn't settled. Decide that from the round's findings, before applying its fixes.

- **Converged:** two clean rounds in a row. One isn't enough, since the next fresh reader can find a different gap in the same text.
- **Next round's lenses:** Paraphrase always, since any edit can break comprehension, plus each lens that raised an unsettled Blocker or Major last round.
- **Fresh reviewers every round.** Never send a message to a reviewer from an earlier round: it has read the old version.
- **Stop and ask** after five rounds, or on **churn**: a new finding at the scope of the last round's edit, which undoing that edit would fix. List the open findings by severity, then ask once: accept and stop, run more rounds, or take the doc back to drafting.

---

## Step 6 — Report

- **Doc:** its path, the rounds run, and how it ended: converged, accepted at the cap or on churn, or stopped by the user.
- **Lenses:** per round, which ran and which were not run.
- **Changed:** one line per fixed finding; `git diff -- <doc>` is the full record.
- **Contested and declined:** each with its evidence or reason, so the user can overrule it.
- **Decided:** each question asked, and the answer.
- **Still open:** findings left at the cap or on churn, by severity, and code the findings show is wrong.
- **Paraphrase:** the last round's, so the user can hold it against their intent one more time.

Don't commit. If the user asks for a commit, call the Skill tool with "conventional-commit".
