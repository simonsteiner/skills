"""The authoring rules every owned skill is held to, checked one skill folder at a time.

From the Agent Skills spec and best practices (https://agentskills.io/specification,
https://agentskills.io/skill-creation/best-practices,
https://agentskills.io/skill-creation/using-scripts):

- name: 1-64 lowercase letters, digits, hyphens; no leading, trailing or doubled
  hyphen; matches its folder
- description: non-empty, at most 1024 chars; compatibility, when present, 1-500 chars
- SKILL.md body under 500 lines and about 5,000 tokens
- bundled files sit at most one level below the skill folder (scripts/, references/, …),
  and output templates (`*template*` files outside scripts/ and evals/) sit in assets/
- every relative link in SKILL.md resolves, and bundled Markdown doesn't link to other
  bundled Markdown (references stay one level deep)
- no vague filler ("handle errors appropriately", "follow best practices"): say what
  the agent would get wrong instead
- one-off `npx` / `bunx` / `uvx` / `pipx run` commands in code pin a version, not a dist-tag
- a bundled script has a shebang, is executable, answers `--help`, and never prompts
  (no `read -p`, `/dev/tty`, `input()`, `getpass`): agents run in non-interactive shells

From Anthropic's skill authoring best practices
(https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

- name has no reserved word ("anthropic", "claude"); description has no XML tags
- reference files over 100 lines open with a "## Contents" list
  (templates are copied out verbatim, so `*template*` files are exempt)
- no Windows-style paths, no time-sensitive "before <Month> <year>" instructions
- no quoted trigger phrase shared by two model-invoked descriptions

From https://github.com/mgechev/skills-best-practices:

- description is third person: no "I can…" / "You can use this…" (injected into the
  system prompt), and a model-invoked one says when to use it, not only what it does
- no README / CHANGELOG / INSTALL files inside a skill folder
- every bundled file is mentioned in SKILL.md (an unreferenced file is never read);
  CREDITS.md and evals/ are exempt

From AGENTS.md: disable-model-invocation is `true`, `false`, or absent.

Repo convention: a command in a code block runs a bundled script as
`<skill-dir>/scripts/…` (not `scripts/…` or `./scripts/…`): agents run it from the
user's repo, where a bare path names that repo's scripts, not the skill's.

lint-skills.py runs check(); tests/tooling/test_authoring_rules.py tests it.
"""

import os
import re
from pathlib import Path

MAX_BODY_LINES = 500
MAX_BODY_TOKENS = 5000
CHARS_PER_TOKEN = 4  # a rough estimate for English prose; no tokenizer dependency

VAGUE = (
    "handle errors appropriately",
    "handle edge cases appropriately",
    "follow best practices",
    "use best practices",
    "as appropriate",
)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
UNPINNED = re.compile(r"\b(?:npx|bunx|uvx|pipx run)\s+(?:-{1,2}[\w-]+(?:=\S+)?\s+)*(@?[a-z][\w./-]*(?:[@=]=?\S+)?)")
# a fenced block: ``` or ~~~, three or more, indented or not (list items), closed by a line of
# nothing but at least the same run; a fence line with an info string inside is content (CommonMark)
FENCED = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n(.*?)^[ \t]*\1(?:(?<=`)`*|(?<=~)~*)[ \t]*$", re.DOTALL | re.MULTILINE)
BARE_SCRIPT = re.compile(r"(?<![\w/.>-])(?:\./)?(scripts/[\w.-]+)")
CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)  # fenced blocks and inline code spans
PROMPTS = re.compile(r"\bread\s+(?:-\w+\s+)*-p\b|/dev/tty|\binput\(|\bgetpass\b")


def check(repo, skills):
    """Every authoring problem across `skills`, as "<path>: <problem>" lines."""
    problems = []
    for s in skills:
        problems.extend(f"{path.relative_to(repo).as_posix()}: {msg}" for path, msg in check_skill(s))

    # Two model-invoked descriptions quoting the same trigger compete for it.
    seen = {}
    for s in skills:
        if not s.model_invoked or not s.fields:
            continue
        for phrase in re.findall(r'"([^"]+)"', s.fields.get("description", "")):
            key = phrase.lower()
            if key in seen and seen[key] != s.name:
                problems.append(f'trigger "{phrase}" is in both {seen[key]} and {s.name}')
            seen.setdefault(key, s.name)
    return problems


def check_skill(s):
    """(path, problem) pairs for one skill."""
    skill_md, folder, fields, body = s.skill_md, s.folder, s.fields, s.body
    if fields is None:
        return [(skill_md, "no YAML frontmatter")]
    out = []

    def problem(path, msg):
        out.append((path, msg))

    invocation = fields.get("disable-model-invocation")
    if invocation not in (None, "true", "false"):
        problem(skill_md, f"disable-model-invocation is {invocation!r}, not true or false")

    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        problem(skill_md, f"name {name!r} must be 1-64 lowercase letters, digits, or single inner hyphens")
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
    if re.match(r"(I|You|We)\b", desc) or re.search(r"\b(I can|you can use|I will|I'll)\b", desc, re.IGNORECASE):
        problem(skill_md, "description isn't third person")
    if s.model_invoked and not re.search(r"\bwhen\b", desc, re.IGNORECASE):
        problem(skill_md, "model-invoked description never says when to use it")
    if "compatibility" in fields and not 1 <= len(fields["compatibility"]) <= 500:
        problem(skill_md, "compatibility must be 1-500 chars")

    lines = body.count("\n")
    if lines >= MAX_BODY_LINES:
        problem(skill_md, f"body is {lines} lines, {MAX_BODY_LINES} or more")
    tokens = len(body) // CHARS_PER_TOKEN
    if tokens > MAX_BODY_TOKENS:
        problem(skill_md, f"body is about {tokens} tokens, over {MAX_BODY_TOKENS}; move reference material out")

    files = sorted(f for f in folder.rglob("*") if f.is_file())
    for f in files:
        rel = f.relative_to(folder)
        if re.fullmatch(r"(README|CHANGELOG|INSTALL\w*)(\.\w+)?", f.name, re.IGNORECASE):
            problem(f, "documentation file inside a skill folder")
        if len(rel.parts) > 2:
            problem(f, "bundled file is more than one level below the skill folder")
        if "template" in f.name and rel.parts[0] not in ("assets", "scripts", "evals"):
            problem(f, "output template outside assets/")
        if rel.parts[0] == "scripts":
            out.extend(check_script(f))
        if rel.parts[0] == "evals":
            continue  # test cases for the author, never read by the agent
        if f != skill_md and f.name != "CREDITS.md" and f.name not in body and rel.as_posix() not in body:
            problem(f, "bundled file is never mentioned in SKILL.md")

    for target in re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+\.(?:md|sh|py|json|ya?ml))", body):
        if not (folder / target).exists():
            problem(skill_md, f"link to {target!r} doesn't resolve")

    markdown = [f for f in files if f.suffix == ".md"]
    names = {f.name for f in markdown if f != skill_md}
    for md in markdown:
        text = md.read_text()
        if md != skill_md:
            for target in re.findall(r"\]\((?!https?:|#)([^)#\s]+\.md)", text):
                if Path(target).name in names:
                    problem(md, f"links to bundled {target!r}; references should be one level deep from SKILL.md")
        if md != skill_md and "template" not in md.name and text.count("\n") > 100 and "\n## Contents\n" not in text:
            problem(md, "over 100 lines without a '## Contents' list")

    instructions = [(f, f.read_text()) for f in markdown if f.name != "CREDITS.md"]
    for md, text in instructions:
        if re.search(r"\b(scripts|references|assets)\\\w", text):
            problem(md, "Windows-style path (use forward slashes)")
        if re.search(rf"\b(before|after|until|as of)\s+({MONTHS})\s+20\d\d", text, re.IGNORECASE):
            problem(md, "time-sensitive instruction; move it to an 'old patterns' section")
        for phrase in VAGUE:
            if phrase in text.lower():
                problem(md, f'vague instruction "{phrase}"; say what the agent would get wrong instead')
        for block in FENCED.finditer(text):
            for path in sorted(set(BARE_SCRIPT.findall(block[2]))):
                if (folder / path).is_file():
                    problem(md, f"code block runs {path!r}; write <skill-dir>/{path}, agents run it from the user's repo")
        for pkg in UNPINNED.findall("\n".join(CODE.findall(text))):
            if not re.search(r"@\d|==\d", pkg):
                problem(md, f"unpinned one-off command for {pkg!r}; pin a version (pkg@1.2.3)")
    return out


def check_script(f):
    """(path, problem) pairs for one file under a skill's scripts/."""
    try:
        text = f.read_text()
    except UnicodeDecodeError:
        return [(f, "bundled script isn't text")]
    out = []
    if not text.startswith("#!"):
        out.append((f, "bundled script has no shebang"))
    if not os.access(f, os.X_OK):
        out.append((f, "bundled script isn't executable"))
    if "--help" not in text:
        out.append((f, "bundled script doesn't answer --help"))
    if PROMPTS.search(text):
        out.append((f, "bundled script prompts for input; take it from flags, env or stdin"))
    return out
