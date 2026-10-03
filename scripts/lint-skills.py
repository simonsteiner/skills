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

From CLAUDE.md:

- skills in engineering/, productivity/, misc/ are linked from README.md and listed in
  .claude-plugin/plugin.json; skills in the other buckets appear in neither
- no curated third-party skill shares a name with an owned skill

    scripts/lint-skills.py      exit 1 and list every problem, or print "ok"
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLISHED = {"engineering", "productivity", "misc"}
UNPUBLISHED = {"personal", "in-progress", "deprecated"}

problems = []


def problem(path, msg):
    problems.append(f"{path.relative_to(REPO)}: {msg}")


def frontmatter(text):
    """Top-level keys of a SKILL.md's YAML frontmatter, folded scalars joined.

    Enough YAML for these files — plain `key: value` and `key: >` blocks — without a
    dependency. Nested maps (metadata:) are kept as their raw indented text.
    """
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fields, key = {}, None
    for line in m.group(1).split("\n"):
        top = re.match(r"([a-z][a-z0-9-]*):\s*(.*)$", line)
        if top:
            key, value = top.groups()
            fields[key] = "" if value in (">", "|", ">-", "|-") else value.strip().strip("'\"")
        elif key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, text[m.end():]


skills = {}
for skill_md in sorted(REPO.glob("skills/*/*/SKILL.md")):
    folder = skill_md.parent
    bucket = folder.parent.name
    fields, body = frontmatter(skill_md.read_text())
    if fields is None:
        problem(skill_md, "no YAML frontmatter")
        continue

    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        problem(skill_md, f"name {name!r} must be 1-64 lowercase letters, digits, or hyphens")
    if re.search(r"anthropic|claude", name):
        problem(skill_md, f"name {name!r} contains a reserved word")
    if name != folder.name:
        problem(skill_md, f"name {name!r} doesn't match its folder {folder.name!r}")

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

    skills[name] = {
        "bucket": bucket,
        "path": skill_md.relative_to(REPO).as_posix(),
        "folder": folder.relative_to(REPO).as_posix(),
        "model_invoked": fields.get("disable-model-invocation") != "true",
        "description": desc,
    }
    if bucket not in PUBLISHED | UNPUBLISHED:
        problem(skill_md, f"bucket {bucket!r} is not one of the buckets in CLAUDE.md")

# Two model-invoked descriptions quoting the same trigger compete for it.
seen = {}
for name, s in skills.items():
    if not s["model_invoked"]:
        continue
    for phrase in re.findall(r'"([^"]+)"', s["description"]):
        key = phrase.lower()
        if key in seen and seen[key] != name:
            problems.append(f'trigger "{phrase}" is in both {seen[key]} and {name}')
        seen.setdefault(key, name)

readme = (REPO / "README.md").read_text()
plugin = set(json.loads((REPO / ".claude-plugin/plugin.json").read_text())["skills"])
for name, s in skills.items():
    linked = f"(./{s['path']})" in readme
    listed = f"./{s['folder']}" in plugin
    if s["bucket"] in PUBLISHED:
        if not linked:
            problems.append(f"README.md doesn't link {name} to ./{s['path']}")
        if not listed:
            problems.append(f".claude-plugin/plugin.json doesn't list ./{s['folder']}")
    elif linked or listed:
        problems.append(f"{name} is in {s['bucket']}/ but appears in README.md or plugin.json")

third_party = json.loads((REPO / "third-party/skills.json").read_text())
for source in third_party["sources"]:
    for curated in source.get("skills", []):
        if curated["name"] in skills:
            problems.append(f"curated skill {curated['name']} from {source['repo']} collides with an owned skill")

if problems:
    print("\n".join(problems))
    sys.exit(1)
print("ok")
