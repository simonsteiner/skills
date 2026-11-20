---
"simonsteiner-skills": minor
---

New user-invoked `review-doc` skill. It reviews a design doc, plan or spec with fresh sub-agents that never saw the conversation behind it. A paraphrase lens always runs; a simplicity-and-reuse lens and an implementation-readiness lens run when the doc calls for them. It verifies each finding, contests only with evidence a reviewer could check, edits the doc for clear fixes, and asks you about anything that changes a decision. Rounds repeat with new reviewers until two in a row come back clean, with a stop at five rounds or on churn. The idea comes from Google's Elephant-Goldfish Model.
