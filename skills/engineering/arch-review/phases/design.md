# Design phase

You decide one candidate's design alone and write it down; nobody answers questions mid-run. Your brief gives the report path, the candidate ID, the branch and its base, the context rules, and the model rule for anything you spawn. Follow them.

Call the Skill tool with "codebase-design" before anything else. Use its vocabulary exactly (module, interface, implementation, depth, seam, adapter, leverage, locality) in the Decisions and the commit.

1. Branch `refactor/<candidate-slug>` (the planned name in the status table) off the base.
2. Map the candidate as a decision tree: the shape of the deepened module, what sits behind the seam, the dependency category (codebase-design's DEEPENING), which tests survive, which callers change.
3. Work it in rounds. Each round, take every decision whose prerequisites are settled and **answer each one yourself with the recommended option**.
4. Ground every answer in a fact from this tree (a measurement, a grep count, a reproduced failure), not an assertion. Look facts up; never guess them. A decision without a fact is a guess, and recorded facts are what make the run safe to leave alone.
5. When the interface shape is genuinely open, use codebase-design's design-it-twice pattern and take your own recommendation.
6. Record every decision as `Q<n>: question → answer, because <fact>` in the **Decisions** block of the candidate's card. Call the Skill tool with "conventional-commit" to commit the Decisions on the candidate branch.
7. **A one-way door stops the candidate, not the run.** The card's door says what to expect, but a design that turns out to need one counts too: a data migration, a change to a published wire or file format, or deleting user data. Mark the row `blocked` with the question in Notes, commit it, and hand back.
8. A new domain term, or a sharpened one: call the Skill tool with "domain-modeling" and update the glossary inline. Dropping the candidate for a load-bearing reason: record it as an ADR the same way, so the next review doesn't re-suggest it, and mark the row `dropped` with the reason in Notes.

The report is a dated record: you change only the card's Decisions and, when the candidate stops, its status row. Never rewrite a finding.

**Hand back:** the Decisions committed on the candidate branch, or the row `blocked` (or `dropped`) with its question or reason.
