"""The CLAUDE.md listing rules for owned skills, checked against the files that list them.

- every published skill (engineering/, productivity/, misc/) has one entry in the
  top-level README.md and one in .claude-plugin/plugin.json; nothing else does
- every skill has one entry in its bucket's README.md
- an entry is a list item `- **[name](path/to/SKILL.md)** — …` linking the skill's name
  to its SKILL.md, under the `User-invoked` or `Model-invoked` heading its frontmatter
  calls for
- every curated and archived skill in third-party/skills.json, and every source, says why

lint-skills.py runs check(); test_published_rules.py tests it.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

GROUPS = ("User-invoked", "Model-invoked")


@dataclass(frozen=True)
class Entry:
    name: str
    target: str
    group: str | None  # the User-/Model-invoked heading it sits under, if any
    line: int


def entries(text):
    """The skill entries in a Markdown list: `- **[name](target)**` items.

    Text inside HTML comments and fenced code blocks is not an entry.
    """
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    found, group, fenced = [], None, False
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith("```"):
            fenced = not fenced
        if fenced:
            continue
        heading = re.match(r"#+\s+(.*?)\s*$", line)
        if heading:
            group = heading.group(1) if heading.group(1) in GROUPS else None
            continue
        item = re.match(r"[-*]\s+\*\*\[([^\]]+)\]\(([^)\s]+)\)\*\*", line)
        if item:
            found.append(Entry(item.group(1), item.group(2), group, n))
    return found


def check_list(path, listed, expected, repo):
    """`listed`: the entries in one file. `expected`: {target: skill} it must hold, exactly."""
    problems, seen = [], set()
    where = path.relative_to(repo).as_posix()
    for e in listed:
        skill = expected.get(e.target)
        if skill is None:
            problems.append(f"{where}:{e.line}: {e.name} links {e.target}, which is no skill this file lists")
            continue
        if e.target in seen:
            problems.append(f"{where}:{e.line}: {skill.name} is listed twice")
        seen.add(e.target)
        if e.name != skill.name:
            problems.append(f"{where}:{e.line}: link text {e.name!r} isn't the skill's name {skill.name!r}")
        group = GROUPS[skill.model_invoked]
        if e.group != group:
            problems.append(f"{where}:{e.line}: {skill.name} is {group} but listed under {e.group or 'no group heading'}")
    for target, skill in expected.items():
        if target not in seen:
            problems.append(f"{where}: no entry linking {skill.name} to {target}")
    return problems


def check(repo, skills):
    """Every listing-rule problem for `skills` (an inventory) under `repo`, as messages."""
    problems = []

    readme = repo / "README.md"
    published = {f"./{s.skill_md.relative_to(repo).as_posix()}": s for s in skills if s.published}
    listed = [e for e in entries(readme.read_text()) if e.target.startswith("./skills/")]
    problems += check_list(readme, listed, published, repo)

    for bucket in sorted({s.bucket for s in skills}):
        bucket_readme = repo / "skills" / bucket / "README.md"
        if not bucket_readme.exists():
            problems.append(f"skills/{bucket}/README.md is missing")
            continue
        expected = {f"./{s.name}/SKILL.md": s for s in skills if s.bucket == bucket}
        problems += check_list(bucket_readme, entries(bucket_readme.read_text()), expected, repo)

    plugin = set(json.loads((repo / ".claude-plugin/plugin.json").read_text())["skills"])
    folders = {f"./{s.folder.relative_to(repo).as_posix()}" for s in skills if s.published}
    problems += [f".claude-plugin/plugin.json doesn't list {f}" for f in sorted(folders - plugin)]
    problems += [f".claude-plugin/plugin.json lists {f}, which is no published skill" for f in sorted(plugin - folders)]

    manifest = repo / "third-party/skills.json"
    if manifest.exists():
        for source in json.loads(manifest.read_text())["sources"]:
            if not str(source.get("why", "")).strip():
                problems.append(f"third-party/skills.json: source {source['repo']} doesn't say why")
            for kind in ("skills", "archived"):
                for k in source.get(kind, []):
                    if not str(k.get("why", "")).strip():
                        problems.append(f"third-party/skills.json: {kind} entry {k['name']} from {source['repo']} doesn't say why")
    return problems
