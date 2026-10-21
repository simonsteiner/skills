---
"simonsteiner-skills": patch
---

`setup-lefthook` now has projects that load the token-budget remote add `".git/**"` to `exclude` in `.rumdl.toml`. lefthook clones the remote into `.git/info/lefthook-remotes/`, and rumdl walks `.git`, so `rumdl check .` linted the remote's Markdown and failed CI. The migration steps also add the remote's words to the cspell dictionary.
