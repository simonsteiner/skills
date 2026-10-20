---
"simonsteiner-skills": minor
---

Add `setup-lefthook`: sets up lefthook git hooks for a project's stack, following the conventions shared by my existing `lefthook.yml` files, and adds a pre-commit check that blocks any staged agent-written file over 5,000 tokens (bytes / 4), skipping lockfiles and generated code, with step-by-step instructions for splitting the file.
