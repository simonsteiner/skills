#!/usr/bin/env python3
"""Check every skill under skills/ against the authoring rules this repo follows.

From Anthropic's skill authoring best practices
(https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

- name: 1-64 chars, lowercase letters, digits, hyphens; no "anthropic"/"claude"; matches its folder
- description: non-empty, at most 1024 chars, no XML tags
- SKILL.md body under 500 lines
- other Markdown files over 100 lines open with a "## Contents" list
  (templates are copied out verbatim, so `*template*` files are exempt)
- no quoted trigger phrase shared by two model-invoked descriptions

From the other two guides (https://agentskills.io/skill-creation/best-practices and
https://github.com/mgechev/skills-best-practices):

- description is third person: no "I can…" / "You can use this…" (injected into the system prompt)
- a model-invoked description says when to use it ("Use when…"), not only what it does
- no README / CHANGELOG / INSTALL files inside a skill folder
- bundled files sit at most one level below the skill folder (scripts/, references/, …)
- every relative Markdown link in SKILL.md resolves, and every bundled file is mentioned
  in SKILL.md (an unreferenced file is never read); CREDITS.md and evals/ are exempt
- bundled Markdown doesn't link to other bundled Markdown (references stay one level deep)
- no Windows-style paths, no time-sensitive "before <Month> <year>" instructions

From CLAUDE.md:

- disable-model-invocation is `true`, `false`, or absent
- the listing rules in published_rules.py: README.md, bucket READMEs, plugin.json,
  and a reason for every curated and archived skill
- the inventory rules in skill_inventory.py: known buckets, unique names, and no
  curated skill sharing a name with an owned one

    scripts/lint-skills.py      exit 1 and list every problem, or print "ok"
"""

import re
import sys
from pathlib import Path

import published_rules
from skill_inventory import REPO, inventory

problems = []


def problem(path, msg):
    problems.append(f"{path.relative_to(REPO)}: {msg}")


def check_guides(skill_md, folder, name, desc, fields, body):
    """Rules from the agentskills.io and mgechev guides."""
    if re.match(r"(I|You|We)\b", desc) or re.search(r"\b(I can|you can use|I will|I'll)\b", desc, re.IGNORECASE):
        problem(skill_md, "description isn't third person")
    if fields.get("disable-model-invocation") != "true" and not re.search(r"\bwhen\b", desc, re.IGNORECASE):
        problem(skill_md, "model-invoked description never says when to use it")

    files = [f for f in folder.rglob("*") if f.is_file()]
    for f in files:
        rel = f.relative_to(folder)
        if re.fullmatch(r"(README|CHANGELOG|INSTALL\w*)(\.\w+)?", f.name, re.IGNORECASE):
            problem(f, "documentation file inside a skill folder")
        if len(rel.parts) > 2:
            problem(f, "bundled file is more than one level below the skill folder")
        if rel.parts[0] == "evals":
            continue  # test cases for the author, never read by the agent
        if f != skill_md and f.name != "CREDITS.md" and f.name not in body and rel.as_posix() not in body:
            problem(f, "bundled file is never mentioned in SKILL.md")

    for target in re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+\.(?:md|sh|py|json|ya?ml))", body):
        if not (folder / target).exists():
            problem(skill_md, f"link to {target!r} doesn't resolve")

    names = {f.name for f in files if f.suffix == ".md" and f != skill_md}
    for md in files:
        if md.suffix != ".md" or md == skill_md:
            continue
        for target in re.findall(r"\]\((?!https?:|#)([^)#\s]+\.md)", md.read_text()):
            if Path(target).name in names:
                problem(md, f"links to bundled {target!r}; references should be one level deep from SKILL.md")

    text = body + "".join(f.read_text() for f in files if f.suffix == ".md" and f != skill_md)
    if re.search(r"\b(scripts|references|assets)\\\w", text):
        problem(skill_md, "Windows-style path (use forward slashes)")
    if re.search(r"\b(before|after|until|as of)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d", text, re.IGNORECASE):
        problem(skill_md, "time-sensitive instruction; move it to an 'old patterns' section")


inv = inventory()
problems.extend(inv.problems)
skills = {s.name: s for s in inv.skills}
for s in inv.skills:
    skill_md, folder, fields, body = s.skill_md, s.folder, s.fields, s.body
    if fields is None:
        problem(skill_md, "no YAML frontmatter")
        continue

    invocation = fields.get("disable-model-invocation")
    if invocation not in (None, "true", "false"):
        problem(skill_md, f"disable-model-invocation is {invocation!r}, not true or false")

    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        problem(skill_md, f"name {name!r} must be 1-64 lowercase letters, digits, or hyphens")
    if re.search(r"anthropic|claude", name):
        problem(skill_md, f"name {name!r} contains a reserved word")
    if name != s.name:
        problem(skill_md, f"name {name!r} doesn't match its folder {s.name!r}")

    desc = fields.get("description", "")
    if not desc:
        problem(skill_md, "description is empty")
    if len(desc) > 1024:
        problem(skill_md, f"description is {len(desc)} chars, over 1024")
    if re.search(r"<[A-Za-z/][^>]*>", desc):
        problem(skill_md, "description contains an XML tag")

    lines = body.count("\n")
    if lines >= 500:
        problem(skill_md, f"body is {lines} lines, 500 or more")

    for md in sorted(folder.rglob("*.md")):
        if md == skill_md or "template" in md.name:
            continue
        text = md.read_text()
        if text.count("\n") > 100 and "\n## Contents\n" not in text:
            problem(md, "over 100 lines without a '## Contents' list")

    check_guides(skill_md, folder, name, desc, fields, body)

# Two model-invoked descriptions quoting the same trigger compete for it.
seen = {}
for name, s in skills.items():
    if not s.model_invoked or not s.fields:
        continue
    for phrase in re.findall(r'"([^"]+)"', s.fields.get("description", "")):
        key = phrase.lower()
        if key in seen and seen[key] != name:
            problems.append(f'trigger "{phrase}" is in both {seen[key]} and {name}')
        seen.setdefault(key, name)

problems.extend(published_rules.check(REPO, inv.skills))

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("ok")
