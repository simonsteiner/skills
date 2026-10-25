---
"simonsteiner-skills": minor
---

setup-lefthook adds a SonarQube job to projects analysed by SonarQube or SonarCloud. It runs the SonarQube CLI's own pre-commit check on the staged files, which scans for hardcoded secrets and for new dependency risks when a manifest changes. The job is skipped on a machine without the `sonar` CLI or not logged in, and an existing `sonar integrate git` hook is replaced by it, so lefthook stays the only hook manager.
