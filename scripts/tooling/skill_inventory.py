"""The owned skills: every skills/<bucket>/<name>/SKILL.md in this repo.

The one definition of "owned skill" (GLOSSARY.md) the tooling shares: which buckets
exist and which are published, what a skill's name is, and the rules that make the set
unusable: an unknown bucket, two skills with one name, an owned skill that a curated
one (third-party/skills.json) would overwrite in the global store.

A skill's name is its folder's name; lint-skills.py checks the frontmatter `name`
against it. Frontmatter is parsed lazily with ruamel.yaml (YAML 1.2, duplicate keys
rejected), so scripts that only need folder names stay stdlib-only.
"""

import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from . import third_party

REPO = Path(__file__).resolve().parents[2]
PUBLISHED = ("engineering", "productivity", "misc")
UNPUBLISHED = ("personal", "in-progress", "deprecated")
FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(?:(.*?)\r?\n)?---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


def _load_yaml(raw, line_offset=0):
    """Parse YAML 1.2 frontmatter safely, rejecting duplicate keys."""
    try:
        from ruamel.yaml import YAML, YAMLError
    except ModuleNotFoundError as err:
        raise RuntimeError(
            "ruamel.yaml is required to parse SKILL.md frontmatter; run via `uv run --locked --no-build`"
        ) from err
    yaml = YAML(typ="safe", pure=True)
    try:
        return yaml.load(raw), None
    except YAMLError as err:
        problem = getattr(err, "problem", None)
        mark = getattr(err, "problem_mark", None)
        if problem and mark is not None:
            return None, f"{problem} (line {mark.line + 1 + line_offset}, col {mark.column + 1})"
        return None, problem or str(err).splitlines()[0]


def frontmatter(text):
    """(fields, body, error) for a SKILL.md's YAML frontmatter.

    No `---` fence returns `(None, text, None)`. Invalid YAML or a non-mapping
    root returns `(None, body, error)`.
    """
    m = FRONTMATTER.match(text)
    if not m:
        return None, text, None
    body = text[m.end():]
    data, error = _load_yaml(m.group(1) or "", line_offset=1)
    if error is not None:
        return None, body, error
    if not isinstance(data, dict):
        return None, body, "frontmatter must be a YAML mapping"
    return data, body, None


@dataclass
class Skill:
    name: str
    bucket: str
    folder: Path

    @property
    def skill_md(self):
        return self.folder / "SKILL.md"

    @cached_property
    def _parsed(self):
        return frontmatter(self.skill_md.read_text())

    @property
    def fields(self):
        return self._parsed[0]

    @property
    def body(self):
        return self._parsed[1]

    @property
    def frontmatter_error(self):
        return self._parsed[2]

    @property
    def published(self):
        return self.bucket in PUBLISHED

    @property
    def active(self):
        return self.bucket != "deprecated"

    @property
    def model_invoked(self):
        return (self.fields or {}).get("disable-model-invocation") is not True


@dataclass(frozen=True)
class Inventory:
    skills: list
    problems: list


def inventory(repo=REPO):
    """Every owned skill under `repo`, sorted by path, and what's wrong with the set."""
    skills, problems, seen = [], [], {}
    for skill_md in sorted(repo.glob("skills/*/*/SKILL.md")):
        folder = skill_md.parent
        skill = Skill(folder.name, folder.parent.name, folder)
        skills.append(skill)
        where = skill_md.relative_to(repo).as_posix()
        if skill.bucket not in PUBLISHED + UNPUBLISHED:
            problems.append(f"{where}: bucket {skill.bucket!r} is not one of the buckets in AGENTS.md")
        if skill.name in seen:
            problems.append(f"{where}: skill name {skill.name!r} is also owned by {seen[skill.name]}")
        seen.setdefault(skill.name, where)

    # A curated and an owned skill would fight over one name in the global store, and
    # whichever synced last would silently win (docs/adr/0002).
    manifest = third_party.load(repo)
    for curated in manifest.curated if manifest else []:
        if curated.name in seen:
            problems.append(
                f"curated skill {curated.name} from {curated.repo} collides with "
                f"the owned skill at {seen[curated.name]}"
            )
    return Inventory(skills, problems)
