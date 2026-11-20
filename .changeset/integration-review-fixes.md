---
"simonsteiner-skills": patch
---

Fixes from reviewing the integration branch. Lint's `metadata` rule now rejects values YAML loads as something other than a string (`version: 1.0`, `enabled: true`, a null or a date), and an `npx -- tool` call counts as unpinned again. test-review's `test-history.py` reads a component prefix such as `parser: fix crash` by its words instead of dropping the commit, and no longer pairs a source file with a fixture of the same name. It and arch-review's `co-change.py` ignore `log.showSignature`. test-review stops a candidate whose row comes back `blocked`, as arch-review does, and arch-review takes candidates from any lens. `pick-repo.sh --head` exits 1 on a failed `gh` call instead of reading as "no PR". attach-media's example runs as one command and cleans up after itself.
