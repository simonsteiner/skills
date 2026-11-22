"""The authoring rules every owned skill is held to, checked one skill folder at a time.

From the Agent Skills spec and best practices (https://agentskills.io/specification,
https://agentskills.io/skill-creation/best-practices,
https://agentskills.io/skill-creation/using-scripts):

- frontmatter is valid YAML 1.2 (parsed by ruamel.yaml; duplicate keys rejected) and uses
  only spec fields plus `disable-model-invocation`
- name: 1-64 lowercase letters, digits, hyphens; no leading, trailing or doubled
  hyphen; matches its folder
- description: non-empty string, at most 1024 chars; compatibility, when present, 1-500 chars;
  license and allowed-tools, when present, are non-empty strings
- SKILL.md body under 500 lines and about 5,000 tokens
- bundled files sit at most one level below the skill folder (scripts/, references/, …),
  and output templates (`*template*` files outside scripts/ and evals/) sit in assets/
- every relative link in SKILL.md resolves, and bundled Markdown doesn't link to other
  bundled Markdown (references stay one level deep)
- no vague filler ("handle errors appropriately", "follow best practices"): say what
  the agent would get wrong instead
- one-off `npx` / `bunx` / `uvx` / `pipx run` commands in code pin a version, not a dist-tag
- a bundled script has a shebang, is executable, answers `--help`, never prompts
  (no `read -p`, `/dev/tty`, `input()`, `getpass`), and if Python, imports only stdlib
  (or sibling modules) unless it declares PEP 723 dependencies (`# /// script`); an import
  in an `except ImportError:` fallback (`try: import tomllib` / `except ImportError: import
  tomli`) is optional, so it doesn't count
- a Python script with a PEP 723 `# /// script` block has a `uv run --script` shebang, so
  running it directly installs what the block declares
  (https://docs.astral.sh/uv/guides/scripts/#using-a-shebang-to-create-an-executable-file)

From Anthropic's skill authoring best practices
(https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):

- name has no reserved word ("anthropic", "claude"); description has no XML tags
- reference files over 100 lines open with a "## Contents" list
  (templates are copied out verbatim, so `*template*` files are exempt)
- no Windows-style paths, no time-sensitive "before <Month> <year>" instructions
- no quoted trigger phrase shared by two model-invoked descriptions

From https://github.com/mgechev/skills-best-practices and description-routing guides
(https://convergentskills.com/tools/description-linter/,
https://github.com/William-Yeh/agent-skill-linter):

- description is third person: no "I can…" / "You can use this…" (injected into the
  system prompt), avoids vague filler ("helps with", "various", "general purpose") and
  routing-label prefixes ("Triggers on:", "Use cases:", "When to use:"), and a
  model-invoked one says when to use it, not only what it does
- no README / CHANGELOG / INSTALL files inside a skill folder
- every bundled file is mentioned in SKILL.md (an unreferenced file is never read);
  CREDITS.md and evals/ are exempt

From https://agentskills.io/skill-creation/evaluating-skills: evals/evals.json, when
present, is valid (tooling/evals.py); evals/triggers.json, when present, is valid, sits on a
model-invoked skill, and has prompts that should and shouldn't trigger it (tooling/triggers.py).

From AGENTS.md: disable-model-invocation is YAML boolean `true`, `false`, or absent.

Repo convention:
- no `metadata` field in owned skills (put credits in CREDITS.md, version in plugin.json)
- a command in a code block runs a bundled script as `<skill-dir>/scripts/…` (not `scripts/…`
  or `./scripts/…`): agents run it from the user's repo, where a bare path names that repo's
  scripts, not the skill's.
- no Skill tool call names a user-invoked skill, owned or curated: its description never reaches the model,
  so the call can't fire (docs/invocation.md); the step tells the user to run `/<name>`
- tests live in tests/, never beside the code: no test_*.py, *_test.py, *.test.* or *.spec.*
  file in skills/ or scripts/

lint-skills.py runs check(); tests/tooling/test_authoring_rules.py tests it.
"""

import ast
import os
import re
import sys
from pathlib import Path

from . import evals, third_party, triggers

MAX_BODY_LINES = 500
MAX_BODY_TOKENS = 5000
CHARS_PER_TOKEN = 4  # a rough estimate for English prose; no tokenizer dependency

ALLOWED_FIELDS = frozenset({
    "name", "description", "license", "compatibility", "allowed-tools", "disable-model-invocation",
})
VAGUE = (
    "handle errors appropriately",
    "handle edge cases appropriately",
    "follow best practices",
    "use best practices",
    "as appropriate",
)
VAGUE_DESCRIPTION = ("helps with", "various", "general purpose", "general-purpose")
DESCRIPTION_LABEL = re.compile(r"\b(?:triggers on|use cases|when to use)\s*:", re.IGNORECASE)
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
UNPINNED = re.compile(r"\b(?:npx|bunx|uvx|pipx run)\s+(?:-\S*\s+)*(@?[a-z][\w./-]*(?:[@=]=?\S+)?)")
# a fenced block: ``` or ~~~, three or more, indented or not (list items), closed by a line of
# nothing but at least the same run; a fence line with an info string inside is content (CommonMark)
FENCED = re.compile(r"^[ \t]*(`{3,}|~{3,})[^\n]*\n(.*?)^[ \t]*\1(?:(?<=`)`*|(?<=~)~*)[ \t]*$", re.DOTALL | re.MULTILINE)
BARE_SCRIPT = re.compile(r"(?<![\w/.>-])(?:\./)?(scripts/[\w.-]+)")
CODE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)  # fenced blocks and inline code spans
PROMPTS = re.compile(r"\bread\s+(?:-\w+\s+)*-p\b|/dev/tty|\binput\(|\bgetpass\b")
PEP723_BLOCK = re.compile(r"(?m)^# /// script[ \t]*\r?\n((?:^#[^\n]*\n)*?)^# ///[ \t]*$")
PEP723_DEPS = re.compile(r"""(?m)^dependencies\s*=\s*\[[^\]]*['"]""")
UV_SCRIPT_SHEBANG = re.compile(r"#!.*\buv\s+run\b.*\s--script\b")
IMPORT_ERRORS = frozenset({"ImportError", "ModuleNotFoundError"})
CREDITS = "CREDITS.md"  # upstream notices, exempt from the prose and reference checks
STRAY_TEST = re.compile(r"test_.*\.py|.*_test\.py|.*\.(?:test|spec)\.\w+")


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
        desc = s.fields.get("description")
        if not isinstance(desc, str):
            continue
        for phrase in re.findall(r'"([^"]+)"', desc):
            key = phrase.lower()
            if key in seen and seen[key] != s.name:
                problems.append(f'trigger "{phrase}" is in both {seen[key]} and {s.name}')
            seen.setdefault(key, s.name)
    return problems + _user_invoked_calls(repo, skills) + _stray_tests(repo)


def _user_invoked_calls(repo, skills):
    """A line that mentions the Skill tool and quotes a user-invoked skill's name, owned or curated."""
    user_invoked = {s.name for s in skills if s.fields and not s.model_invoked}
    manifest = third_party.load(repo)
    user_invoked |= {k.name for k in (manifest.curated if manifest else []) if k.invocation == "user"}
    return [
        f"{md.relative_to(repo).as_posix()}:{n}: calls the user-invoked {name} through the Skill tool, "
        f"which can't reach it; tell the user to run `/{name}` instead"
        for s in skills for md in sorted(s.folder.rglob("*.md"))
        if md.name != CREDITS and "evals" not in md.relative_to(s.folder).parts
        for n, name in _skill_tool_names(md) if name in user_invoked
    ]


def _skill_tool_names(md):
    """(line number, name) for every quoted name on a line of `md` that mentions the Skill tool."""
    for n, line in enumerate(md.read_text().splitlines(), 1):
        if "Skill tool" in line:
            yield from ((n, name) for name in re.findall(r'"([a-z0-9-]+)"', line))


def _stray_tests(repo):
    """Test files under skills/ or scripts/, which belong in tests/."""
    return [
        f"{path.relative_to(repo).as_posix()}: tests live in tests/, never beside the code"
        for top in ("skills", "scripts") for path in sorted((repo / top).rglob("*"))
        if path.is_file() and STRAY_TEST.fullmatch(path.name)
    ]


def check_skill(s):
    """(path, problem) pairs for one skill."""
    if s.frontmatter_error is not None:
        return [(s.skill_md, f"invalid YAML frontmatter: {s.frontmatter_error}")]
    if s.fields is None:
        return [(s.skill_md, "no YAML frontmatter")]
    out = [(s.folder / "evals/evals.json", msg) for msg in evals.problems(s)]
    out += [(s.folder / triggers.FILE, msg) for msg in triggers.problems(s)]
    out += [(s.skill_md, msg) for msg in (
        _frontmatter_problems(s) + _name_problems(s) + _description_problems(s)
        + _compatibility_problems(s) + _size_problems(s.body)
    )]
    files = sorted(f for f in s.folder.rglob("*") if f.is_file())
    for f in files:
        out += _bundled_file_problems(s, f)
    out += [(s.skill_md, f"link to {target!r} doesn't resolve") for target in _broken_links(s.folder, s.body)]
    markdown = [f for f in files if f.suffix == ".md"]
    out += _reference_problems(s.skill_md, markdown)
    for md in markdown:
        if md.name != CREDITS:
            text = md.read_text()
            out += [(md, msg) for msg in _prose_problems(text) + _command_problems(s.folder, text)]
    return out


def _frontmatter_problems(s):
    """Allowed frontmatter keys, disallowed metadata, and optional string fields."""
    fields, out = s.fields, []
    if "metadata" in fields:
        out.append("metadata isn't allowed in owned skills (put credits in CREDITS.md, version in plugin.json)")
    for key in sorted(fields, key=str):
        if key != "metadata" and key not in ALLOWED_FIELDS:
            out.append(f"unknown frontmatter field {key!r} (allowed: {', '.join(sorted(ALLOWED_FIELDS))})")
    for key in ("license", "allowed-tools"):
        if key in fields and (not isinstance(fields[key], str) or not fields[key].strip()):
            out.append(f"{key} must be a non-empty string")
    return out


def _name_problems(s):
    """disable-model-invocation and name, against the spec and the skill's folder."""
    fields, out = s.fields, []
    if "disable-model-invocation" in fields and not isinstance(fields["disable-model-invocation"], bool):
        out.append(f"disable-model-invocation is {fields['disable-model-invocation']!r}, not true or false")
    name = fields.get("name", "")
    if not isinstance(name, str):
        out.append(f"name must be a string, got {type(name).__name__}")
        return out
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        out.append(f"name {name!r} must be 1-64 lowercase letters, digits, or single inner hyphens")
    if re.search(r"anthropic|claude", name):
        out.append(f"name {name!r} contains a reserved word")
    if name != s.name:
        out.append(f"name {name!r} doesn't match its folder {s.name!r}")
    return out


def _description_problems(s):
    """description length, person, trigger cues, and clarity."""
    desc = s.fields.get("description", "")
    if not isinstance(desc, str):
        return [f"description must be a string, got {type(desc).__name__}"]
    out = []
    if not desc.strip():
        out.append("description is empty")
    if len(desc) > 1024:
        out.append(f"description is {len(desc)} chars, over 1024")
    if re.search(r"<[A-Za-z/][^>]*>", desc):
        out.append("description contains an XML tag")
    if re.match(r"(I|You|We)\b", desc) or re.search(r"\b(I can|you can use|I will|I'll)\b", desc, re.IGNORECASE):
        out.append("description isn't third person")
    if s.model_invoked and not re.search(r"\bwhen\b", desc, re.IGNORECASE):
        out.append("model-invoked description never says when to use it")
    out += [
        f'vague description phrase "{phrase}"; name the concrete action and artifact instead'
        for phrase in VAGUE_DESCRIPTION if re.search(rf"\b{re.escape(phrase)}\b", desc, re.IGNORECASE)
    ]
    if label := DESCRIPTION_LABEL.search(desc):
        out.append(f"description uses routing label {label.group(0)!r}; state the trigger condition in plain prose")
    return out


def _compatibility_problems(s):
    """compatibility, when present, is a 1-500 char string."""
    if "compatibility" not in s.fields:
        return []
    compat = s.fields["compatibility"]
    if not isinstance(compat, str) or not 1 <= len(compat.strip()) <= 500:
        return ["compatibility must be 1-500 chars"]
    return []


def _size_problems(body):
    """The SKILL.md body against the line and token limits."""
    out = []
    lines = body.count("\n")
    if lines >= MAX_BODY_LINES:
        out.append(f"body is {lines} lines, {MAX_BODY_LINES} or more")
    tokens = len(body) // CHARS_PER_TOKEN
    if tokens > MAX_BODY_TOKENS:
        out.append(f"body is about {tokens} tokens, over {MAX_BODY_TOKENS}; move reference material out")
    return out


def _bundled_file_problems(s, f):
    """(path, problem) pairs for one file in the skill folder, its scripts/ checks included."""
    out = []
    rel = f.relative_to(s.folder)
    if re.fullmatch(r"(README|CHANGELOG|INSTALL\w*)(\.\w+)?", f.name, re.IGNORECASE):
        out.append((f, "documentation file inside a skill folder"))
    if len(rel.parts) > 2:
        out.append((f, "bundled file is more than one level below the skill folder"))
    if "template" in f.name and rel.parts[0] not in ("assets", "scripts", "evals"):
        out.append((f, "output template outside assets/"))
    if rel.parts[0] == "scripts":
        out.extend(check_script(f))
    if rel.parts[0] == "evals":
        return out  # test cases for the author, never read by the agent
    if f != s.skill_md and f.name != CREDITS and f.name not in s.body and rel.as_posix() not in s.body:
        out.append((f, "bundled file is never mentioned in SKILL.md"))
    return out


def _broken_links(folder, body):
    """The relative links in SKILL.md to a bundled file that doesn't exist."""
    links = re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+\.(?:md|sh|py|json|ya?ml))", body)
    return [target for target in links if not (folder / target).exists()]


def _reference_problems(skill_md, markdown):
    """(path, problem) pairs for the reference files: one level deep, and a contents list when long."""
    out = []
    names = {f.name for f in markdown if f != skill_md}
    for md in markdown:
        text = md.read_text()
        if md != skill_md:
            for target in re.findall(r"\]\((?!https?:|#)([^)#\s]+\.md)", text):
                if Path(target).name in names:
                    out.append((md, f"links to bundled {target!r}; references should be one level deep from SKILL.md"))
        if md != skill_md and "template" not in md.name and text.count("\n") > 100 and "\n## Contents\n" not in text:
            out.append((md, "over 100 lines without a '## Contents' list"))
    return out


def _prose_problems(text):
    """Windows paths, time-sensitive and vague instructions in one Markdown file."""
    out = []
    if re.search(r"\b(scripts|references|assets)\\\w", text):
        out.append("Windows-style path (use forward slashes)")
    if re.search(rf"\b(before|after|until|as of)\s+({MONTHS})\s+20\d\d", text, re.IGNORECASE):
        out.append("time-sensitive instruction; move it to an 'old patterns' section")
    out += [f'vague instruction "{phrase}"; say what the agent would get wrong instead'
            for phrase in VAGUE if phrase in text.lower()]
    return out


def _command_problems(folder, text):
    """Commands in one Markdown file: bundled scripts run by a bare path, unpinned one-off packages."""
    out = []
    for block in FENCED.finditer(text):
        for path in sorted(set(BARE_SCRIPT.findall(block[2]))):
            if (folder / path).is_file():
                out.append(f"code block runs {path!r}; write <skill-dir>/{path}, agents run it from the user's repo")
    for pkg in UNPINNED.findall("\n".join(CODE.findall(text))):
        if not re.search(r"@\d|==\d", pkg):
            out.append(f"unpinned one-off command for {pkg!r}; pin a version (pkg@1.2.3)")
    return out


def _has_pep723_dependencies(text):
    """Whether `text` has a closed `# /// script` block declaring at least one dependency."""
    for block in PEP723_BLOCK.finditer(text):
        lines = [line[2:] if line.startswith("# ") else line[1:] for line in block.group(1).splitlines()]
        body = "\n".join(line for line in lines if not line.lstrip().startswith("#"))
        if PEP723_DEPS.search(body):
            return True
    return False


def _catches_import_error(handler):
    """Whether an `except` clause catches ImportError (alone, or in a tuple)."""
    names = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(isinstance(n, ast.Name) and n.id in IMPORT_ERRORS for n in names)


def _import_fallbacks(tree):
    """The import nodes inside an `except ImportError:` clause: optional, tried only when the first import fails."""
    return {
        node
        for t in ast.walk(tree) if isinstance(t, ast.Try)
        for handler in t.handlers if handler.type is not None and _catches_import_error(handler)
        for node in ast.walk(handler) if isinstance(node, (ast.Import, ast.ImportFrom))
    }


def _python_import_problems(f, text):
    """Bundled Python scripts stay stdlib-only unless they declare PEP 723 dependencies."""
    try:
        tree = ast.parse(text, filename=str(f))
    except SyntaxError as err:
        return [(f, f"bundled Python script has a syntax error: {err.msg}")]
    if _has_pep723_dependencies(text):
        return []
    local = {p.stem for p in f.parent.glob("*.py")} | {
        p.name for p in f.parent.iterdir() if p.is_dir() and (p / "__init__.py").exists()
    }
    fallbacks = _import_fallbacks(tree)
    imported = set()
    for node in ast.walk(tree):
        if node in fallbacks:
            continue
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module.split(".")[0])
    third_party = sorted(imported - sys.stdlib_module_names - local)
    return [(f, f"bundled Python script imports non-stdlib module {mod!r} without PEP 723 dependencies")
            for mod in third_party]


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
    if f.suffix == ".py":
        if PEP723_BLOCK.search(text) and not UV_SCRIPT_SHEBANG.match(text):
            out.append((f, "bundled Python script has a PEP 723 block but no `uv run --script` shebang"))
        out.extend(_python_import_problems(f, text))
    return out
