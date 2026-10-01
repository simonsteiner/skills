# Model-invoked vs user-invoked

The file format itself — a folder with a `SKILL.md`, its frontmatter, and the discovery/activation/execution loading model — is the open [Agent Skills](https://github.com/agentskills/agentskills) spec, not something this repo defines. This doc covers only the one axis the spec leaves to the author.

Every `SKILL.md` in this repo is a skill. The one axis that splits them is **invocation** — who can reach it:

- **User-invoked** — reachable **only by the human typing its name**. Set `disable-model-invocation: true` in the frontmatter. The `description` is **human-facing**: a one-line summary read by a person browsing slash-commands. Strip trigger lists ("Use when the user says…").
- **Model-invoked** — reachable by **model or user**. The default: omit `disable-model-invocation`. The `description` is **model-facing** and keeps rich trigger phrasing ("Use when the user wants…, mentions…, asks for…") so auto-invocation fires. The test for whether a skill should stay model-invoked: _could the model usefully reach for this autonomously?_ (Reuse is the reason to extract a skill, not the test.)

Because a user-invoked skill has no description, nothing but the human can reach it — no other skill can fire it. So a user-invoked skill may invoke model-invoked skills, but it can never reach another user-invoked skill.

Bucket `README.md`s and the top-level `README.md` group entries into **User-invoked** and **Model-invoked**.

## Dependencies between them

Dependencies are expressed as an explicit instruction to **call the Skill tool** with the named skill (`Call the Skill tool with "conventional-commit"`), not deep `../other-skill/FILE.md` cross-references, and not a bare `/skill` mention left for the model to interpret. Naming the tool is what gets it fired: most harnesses expose skills as a tool the model calls, and saying so hits more reliably than a `/name` dropped into prose. A bare skill name also stays harness-neutral — it assumes no harness's trigger syntax. Shared reference docs live inside the skill that owns them; other skills reach that material by calling the Skill tool with it, not by linking across folders.

This covers **operative** instructions only — a skill's own steps telling the agent to run another skill now. Prose that merely names a skill (a README, a rule of thumb, a credit) isn't invoking anything and stays a plain label.

The Skill tool takes one skill per call. A step that needs two says so: `Call the Skill tool twice, for "grilling" and "domain-modeling"`.

Only a **model-invoked** skill can be reached this way. When a step depends on a user-invoked skill, phrase it for the human: "tell the user to run `/<name>`" — never a Skill tool call.

The convention follows upstream's [`.agents/invocation.md`](https://github.com/mattpocock/skills/blob/main/.agents/invocation.md).

## Passive vs active domain work

Merely _reading_ `CONTEXT.md` for vocabulary is a one-line prose pointer, not the `domain-modeling` skill. Only the active build/sharpen discipline (challenge terms, edge-case scenarios, write ADRs, update `CONTEXT.md` inline) is `domain-modeling`.
