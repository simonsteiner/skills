---
name: review-doc
description: Reviews a design doc, plan, RFC or spec with fresh sub-agents that never saw the conversation behind it (a paraphrase test, a simplicity-and-reuse check against the code, and an implementation-readiness check), then settles the findings with you, edits the doc, and repeats on what changed until a round comes back clean.
disable-model-invocation: true
---

# Review Doc

The thread that helped write a plan can't review it: it fills every gap from memory. A reader who sees only the written doc can't do that, so every gap they hit is one the next human reader hits too. This skill sends the doc to such readers, and keeps the judgment, what's a real gap and what to change, with this thread and the user.

Fresh means no conversation, not no evidence: reviewers read the doc, the files it links, and the code.

Each round costs one sub-agent per lens, and a doc with findings takes at least two rounds to converge. Say so when the doc is a few lines long; a short plan may not need this.

---

## Step 1: Pin the doc

- **Target.** A path the user gave → that file. None → the doc this thread just wrote or edited, if there's exactly one; otherwise ask for the path. A plan that exists only in chat is saved first, to the path the user names or else `.scratch/<slug>.md`, since a reviewer reads only files.
- **Reading list.** Every relative link in the doc that resolves to an existing file inside the repo. Links that leave the repo, and URLs: list them and ask which to include. Save each included URL's page to `.scratch/` (Step 6 deletes it) and list the saved file, so every reviewer can read it. Add any files the user names.
- **Never on the list:** a summary of the conversation, the brief the doc came from, or notes on what the author meant. That's the context the review exists to remove.
- **Baseline.** Copy the doc to `.scratch/<slug>.orig.md` before the first round (Step 6 deletes it). The report's record is `git diff --no-index <orig> <doc>`, which works whether the doc is tracked, untracked or gitignored, and shows only this review's edits even when the doc already had uncommitted changes.
- **Round snapshot.** Copy the doc to `.scratch/<slug>.round.md` too (Step 6 deletes it). It holds the doc as the last round's reviewers read it, so later rounds can be sent only what changed (Step 3).

---

## Step 2: Pick the lenses

Read the doc once to pick. From [LENSES.md](LENSES.md):

- **Paraphrase**: always.
- **Simplicity**: when the doc proposes something to build or change in a codebase.
- **Readiness**: when the doc has an implementation plan (a section like *Implementation plan*, *Steps*, *Work breakdown*, *Tasks*), or the user says it's about to be built.

Say which lenses run and why the others don't; don't ask. The user can add or drop lenses, or give a standard a lens should apply (a team's RFC template), and that wins.

---

## Step 3: Run a round

Spawn one fresh sub-agent per lens, in parallel. Start each one empty, never as a fork or with inherited context, and give it only:

- the doc's path, the reading list, and the repo root
- its lens section from LENSES.md, copied verbatim
- the settled list (Step 5) from earlier rounds, so it doesn't raise those again
- from round 2 on, what changed since the last round: save `git diff --no-index .scratch/<slug>.round.md <doc>` to `.scratch/<slug>.changes.diff` and list it, then copy the doc over the round snapshot. Tell the reviewer: read the whole doc, but raise a **Blocker** or **Major** only on changed text, or on unchanged text the change contradicts or leaves dangling; anywhere else, raise Blockers only. Earlier rounds already read the unchanged text, and a fresh reader will always find finer detail in it, so without this limit rounds never come back clean.
- these rules: read-only (edit, write and change nothing); every finding gives a severity (**Blocker**, **Major**, **Nit**), the heading or line range, a quote, what's wrong, and what would fix it; return findings only, no praise and no summary beyond what the lens asks for

Use the session's model: a doc review is judgment, not lookup. A sub-agent that errors, times out or returns nothing is relaunched once. One that fails again is **not run** for that round; never count a lens that didn't run as a lens with no findings.

---

## Step 4: Verify and settle

**Verify.** Open the doc at each finding's line and, for a claim about code, the code. A finding you can't ground is dropped: put it on the settled list (Step 5) with why, so a later reviewer raising the same claim doesn't keep rounds from coming back clean. Merge duplicates across lenses, keeping the higher severity.

**Check the paraphrase.** Compare the Paraphrase lens's two paragraphs with what the doc is meant to say. When this thread helped write the doc, compare them with what it knows of the intent. When it didn't (a doc the user pointed at in a fresh session), it knows only the doc, which proves nothing: put the paraphrase to the user as the first question of the round's batch, asking whether it matches what they meant. A wrong paraphrase is a Blocker on the section it got wrong, even when every term was defined.

**Give each finding one verdict:**

| Verdict | When | What follows |
|---------|------|--------------|
| fix | the finding is right | edit the doc |
| disagree | the finding is wrong, and a line or file shows it | record the evidence; no edit |
| needs a decision | the fix is a choice between designs or a scope call, or the evidence lives only in someone's head | ask the user |
| decline | a Nit not worth the edit; never a comprehension finding | record why; no edit |

**Disagree only with evidence:**

- Cite what the reviewer could have read: a line in the doc, a file and symbol in the repo. "This was intentional" isn't evidence; that's *needs a decision*.
- Never disagree with a comprehension gap. If a fresh reader couldn't follow a section, the doc is missing something, even when the reader's conclusion was wrong.
- Don't lower a severity on the way to a fix. Disagree with a Blocker out loud, with the evidence.
- This thread wrote or shaped the doc. Wanting the reviewer to be wrong is not evidence that they are.

**Edit straight away** for each *fix* that doesn't change a decision: a missing definition, a fact taken from the code, a step spelled out, a wrong path. Fix the gap in the doc's own voice and structure; don't rewrite the section around it. Make one targeted edit per finding, never a whole-file or whole-section rewrite, even when most sections have fixes: a rewrite changes text no finding asked about, brings in new errors, and puts all of it in front of the next round. A fix that changes a decision (a different design, a dropped feature, a new requirement) is *needs a decision*.

**Ask the decisions together**, once per round, with the structured question tool when there is one. Each question names the finding and quotes the doc, gives the options, and says which you'd pick and why. Apply the answers.

The doc is the only file this skill edits, apart from what it saves to `.scratch/`. Never touch code, even when a finding shows the code is wrong; put that in the report.

---

## Step 5: Loop until clean

Keep a **settled list** across rounds: each finding dropped as ungrounded, disagreed with, declined or decided against, with its scope and reason. A later round that raises a settled finding again (same scope, same issue) doesn't reopen it. A finding that comes back after a *fix* does: the fix didn't work.

A round is **clean** when every lens ran and none raised a verified Blocker or Major that isn't settled. Decide that from the round's findings, before applying its fixes.

- **Converged:** one clean round. Its own fixes are Nits and settled findings, too small to need another round.
- **Next round's lenses:** after a round whose decisions changed the design (the scope, the approach, a section rewritten), every lens from Step 2, since a lens that came back clean read a different doc. After a round of ordinary fixes, Paraphrase always, since any edit can break comprehension, plus each lens that raised an unsettled Blocker or Major last round.
- **Fresh reviewers every round.** Never send a message to a reviewer from an earlier round: it has read the old version.
- **Stop and ask** after three rounds; when a round's verified, unsettled Blockers and Majors are no fewer than the round before (the review isn't converging); or on **churn**: a new finding at the scope of the last round's edit, which undoing that edit would fix. List the open findings by severity, then ask once: accept and stop, run more rounds, or take the doc back to drafting.

---

## Step 6: Report

- **Doc:** its path, the rounds run, and how it ended: converged, accepted at the cap, on a stalled count or on churn, or stopped by the user.
- **Lenses:** per round, which ran and which were not run.
- **Changed:** one line per fixed finding, then the output of `git diff --no-index <orig> <doc>` (Step 1) in a `diff` block. It's the full record, and the cleanup below deletes the baseline.
- **Dropped, disagreed with and declined:** each with its evidence or reason, so the user can overrule it.
- **Decided:** each question asked, and the answer.
- **Still open:** findings left at the cap, on a stalled count or on churn, by severity, and code the findings show is wrong.
- **Paraphrase:** the last round's, so the user can hold it against their intent one more time.

**Clean up** after the report: delete the baseline, the round snapshot, the changes diff and every page saved from a URL, and `.scratch/` itself if this review created it and it's now empty. A plan saved there from chat (Step 1) is the doc: keep it, and say where it is.

Don't commit. If the user asks for a commit, call the Skill tool with "conventional-commit".
