"""The AGENTS.md listing rules for owned skills, checked against the files that list them.

- the skill catalog (README.md, every bucket README, .claude-plugin/plugin.json) is what
  scripts/build-catalog.py renders from the skills (tooling/catalog.py), and every
  model-invoked description has the summary the catalog lists
- README.md links no unpublished skill (personal/, in-progress/, deprecated/), anywhere
- every curated and archived skill in third-party/skills.json, and every source, says why,
  and every curated skill records its invocation: "model" or "user"

lint-skills.py runs check(); tests/tooling/test_published_rules.py tests it.
"""

import re

from . import catalog, third_party


def prose(text):
    """(line number, line) for every line outside HTML comments and fenced code blocks."""
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group().count("\n"), text, flags=re.DOTALL)
    fence = None
    for n, line in enumerate(text.split("\n"), 1):
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if marker and (fence is None or marker.group(1).startswith(fence)):
            fence = None if fence else marker.group(1)
            continue
        if fence is None:
            yield n, line


def links(text):
    """(line number, target) for every Markdown link outside comments and code fences."""
    return [(n, target) for n, line in prose(text) for target in re.findall(r"\]\(([^)\s]+)", line)]


def check(repo, skills):
    """Every listing-rule problem for `skills` (an inventory) under `repo`, as messages."""
    problems = catalog.problems(skills, repo) + catalog.stale(skills, repo)

    readme = repo / "README.md"
    unpublished = {s.folder.relative_to(repo).as_posix(): s for s in skills if not s.published}
    for n, target in links(readme.read_text()) if readme.exists() else []:
        if skill := unpublished.get(re.sub(r"^\./|/SKILL\.md$|/$", "", target)):
            problems.append(f"README.md:{n}: {skill.name} is in {skill.bucket}/ but README.md links it")

    return problems + check_manifest(repo)


def check_manifest(repo):
    """Every source and curated skill in third-party/skills.json says why it's there."""
    problems = []
    manifest = third_party.load(repo)
    for source in manifest.sources if manifest else []:
        if not source.why.strip():
            problems.append(f"third-party/skills.json: source {source.repo} doesn't say why")
        if source.skills and not source.agents:
            problems.append(f"third-party/skills.json: source {source.repo} has no agents, nor does the manifest")
        for kind, curated in (("skills", source.skills), ("archived", source.archived)):
            problems += [
                f"third-party/skills.json: {kind} entry {k.name} from {source.repo} doesn't say why"
                for k in curated if not k.why.strip()
            ]
        problems += [
            f'third-party/skills.json: skills entry {k.name} from {source.repo} needs "invocation": "model" or "user"'
            for k in source.skills if k.invocation not in third_party.INVOCATIONS
        ]
    return problems
