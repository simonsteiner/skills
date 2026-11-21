---
"simonsteiner-skills": minor
---

New user-invoked `review-doc` skill. It reviews a design doc, plan or spec with fresh sub-agents that never saw the conversation behind it. A paraphrase lens always runs; a simplicity-and-reuse lens and an implementation-readiness lens run when the doc calls for them. It verifies each finding and disagrees only with evidence a reviewer could check. It edits the doc for clear fixes and asks you about anything that changes a decision. After such a decision, the next round runs every lens again. Rounds repeat with new reviewers until two in a row come back clean, and stop at five rounds or on churn. The report holds the full diff, and the skill deletes its scratch copies afterwards. The idea comes from Google's Elephant-Goldfish Model.
