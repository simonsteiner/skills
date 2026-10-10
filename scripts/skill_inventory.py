#!/usr/bin/env python3
"""The owned skills: every skills/<bucket>/<name>/SKILL.md in this repo.

The one definition of "owned skill" (GLOSSARY.md) the tooling shares — which buckets
exist and which are published, what a skill's name is, and the rules that make the set
unusable: an unknown bucket, two skills with one name, an owned skill that a curated
one (third-party/skills.json) would overwrite in the global store.

A skill's name is its folder's name; lint-skills.py checks the frontmatter `name`
against it.

    scripts/skill_inventory.py           print "<name><TAB><bucket><TAB><folder>" per owned skill
    scripts/skill_inventory.py --active  the same, without deprecated/ (what dev-linking installs)

Either form exits 1 and prints the problems to stderr instead when the set has any.
"""

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLISHED = ("engineering", "productivity", "misc")
UNPUBLISHED = ("personal", "in-progress", "deprecated")


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


@dataclass(frozen=True)
class Skill:
    name: str
    bucket: str
    folder: Path
    fields: dict | None  # None: SKILL.md has no frontmatter
    body: str

    @property
    def skill_md(self):
        return self.folder / "SKILL.md"

    @property
    def published(self):
        return self.bucket in PUBLISHED

    @property
    def active(self):
        return self.bucket != "deprecated"

    @property
    def model_invoked(self):
        return (self.fields or {}).get("disable-model-invocation") != "true"


@dataclass(frozen=True)
class Inventory:
    skills: list
    problems: list


def inventory(repo=REPO):
    """Every owned skill under `repo`, sorted by path, and what's wrong with the set."""
    skills, problems, seen = [], [], {}
    for skill_md in sorted(repo.glob("skills/*/*/SKILL.md")):
        folder = skill_md.parent
        fields, body = frontmatter(skill_md.read_text())
        skill = Skill(folder.name, folder.parent.name, folder, fields, body)
        skills.append(skill)
        where = skill_md.relative_to(repo).as_posix()
        if skill.bucket not in PUBLISHED + UNPUBLISHED:
            problems.append(f"{where}: bucket {skill.bucket!r} is not one of the buckets in CLAUDE.md")
        if skill.name in seen:
            problems.append(f"{where}: skill name {skill.name!r} is also owned by {seen[skill.name]}")
        seen.setdefault(skill.name, where)

    # A curated and an owned skill would fight over one name in the global store, and
    # whichever synced last would silently win (docs/adr/0002).
    manifest = repo / "third-party/skills.json"
    if manifest.exists():
        for source in json.loads(manifest.read_text())["sources"]:
            for curated in source.get("skills", []):
                if curated["name"] in seen:
                    problems.append(
                        f"curated skill {curated['name']} from {source['repo']} collides with "
                        f"the owned skill at {seen[curated['name']]}"
                    )
    return Inventory(skills, problems)


def main(argv):
    if argv not in ([], ["--active"]):
        print("Usage: scripts/skill_inventory.py [--active]", file=sys.stderr)
        return 2
    inv = inventory()
    if inv.problems:
        print("\n".join(inv.problems), file=sys.stderr)
        return 1
    for s in inv.skills:
        if s.active or not argv:
            print(f"{s.name}\t{s.bucket}\t{s.folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
