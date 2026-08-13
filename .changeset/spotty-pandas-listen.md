---
"simonsteiner-skills": minor
---

Curate the eleven Cloudflare skills, which had been loading from an unmanaged plugin-marketplace install frozen since July. Adds per-source agent overrides to the manifest, fixes the sync's CLI invocation (one `--skill`/`--agent` flag per value; `npx` was also draining the loop's stdin and skipping every source after the first), and teaches `--check` to report `unmanaged` and `drift` — the two failure modes that hid this.
