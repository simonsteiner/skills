# Skills

A personal collection of agent skills in the open Agent Skills format, plus a curated list of other people's skills installed from their own repos.

## Language

**Skill**:
A folder with a `SKILL.md` that an agent loads on demand.
_Avoid_: command, prompt, plugin

**Owned skill**:
A skill this repo writes and publishes, under `skills/<bucket>/`.
_Avoid_: local skill, custom skill

**Curated skill**:
Someone else's skill listed in `third-party/skills.json` and installed from its upstream repo; never copied into this one.
_Avoid_: vendored, forked, third-party copy

**Archived skill**:
A curated skill that was retired: kept in its source's `archived` list with the reason, no longer installed.
_Avoid_: deleted, dropped

**Bucket**:
A folder under `skills/` grouping owned skills by how often and where they're used (`engineering/`, `productivity/`, `misc/`, `personal/`, `in-progress/`, `deprecated/`).
_Avoid_: category

**User-invoked**:
A skill only the human can start, by typing its name (`disable-model-invocation: true`).
_Avoid_: slash command, manual skill

**Model-invoked**:
A skill the model can start on its own when the task matches its description, and the human can too.
_Avoid_: auto skill

**Bundled script**:
An executable inside a skill's own `scripts/` folder that the agent runs while using the skill; it ships with the skill.
_Avoid_: helper, tool

**Tooling**:
The commands this repo's maintainer runs to lint, link and sync skills, and the code they share; never shipped with a skill.
_Avoid_: scripts (ambiguous with bundled scripts)

**Sync**:
Running `scripts/sync-third-party.py` to install or upgrade every curated skill at upstream's latest.
_Avoid_: update, pull
