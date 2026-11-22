# Skills

A personal collection of agent skills in the open Agent Skills format, plus a curated list of other people's skills installed from their own repos.

## Language

**Skill**:
A folder with a `SKILL.md` that an agent loads on demand.
_Avoid_: command, prompt, plugin

**Owned skill**:
A skill this repo writes, kept in one of its buckets.
_Avoid_: local skill, custom skill

**Published skill**:
An owned skill in a bucket that ships (engineering, productivity, misc): listed in the skill catalog and installable from this repo.
_Avoid_: public skill, released skill

**Skill catalog**:
A generated list of skills: the published skills by bucket and invocation, each with the summary from its description, or the curated skills by source, each with the first sentence of its reason.
_Avoid_: skill list, index

**Bucket**:
A group of owned skills sorted by how often and where they're used: engineering, productivity, misc, personal, in-progress, deprecated.
_Avoid_: category

**User-invoked**:
A skill only the human can start, by typing its name.
_Avoid_: slash command, manual skill

**Model-invoked**:
A skill the model can start on its own when the task matches its description, and the human can too.
_Avoid_: auto skill

**Curated skill**:
Someone else's skill listed in the curated manifest and installed from its upstream repo; never copied into this one.
_Avoid_: vendored, forked, third-party copy

**Source**:
An upstream repo in the curated manifest, with the agents its skills are installed into and the skills curated from it.
_Avoid_: upstream, provider

**Archived skill**:
A skill kept in its source's archived list with the reason: curated once and retired, or considered and declined. Never installed.
_Avoid_: deleted, dropped

**Outdated**:
A curated skill whose folder upstream has changed since it was installed, so the next sync would change it.
_Avoid_: drift (which `--check` uses for a copy an agent missed), stale

**Store**:
The global folder every skill, owned or curated, is installed into; agents load it directly or through links.
_Avoid_: cache, install dir

**Bundled script**:
An executable inside a skill that the agent runs while using the skill; it ships with the skill.
_Avoid_: helper, tool

**Tooling**:
The commands this repo's maintainer runs to lint, link, catalog and sync skills, and the code they share; never shipped with a skill.
_Avoid_: scripts (ambiguous with bundled scripts)

**Sync**:
Bringing a clone's skills up to date: fast-forward the checkout, link the owned skills into the agents, and install every curated skill at its upstream's latest.
_Avoid_: update, pull
