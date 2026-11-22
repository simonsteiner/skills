"""The rules a skill's bundled scripts (its scripts/ folder) are held to.

From https://agentskills.io/skill-creation/using-scripts:

- a bundled script has a shebang, is executable, answers `--help`, never prompts
  (no `read -p`, `/dev/tty`, `input()`, `getpass`), and if Python, imports only stdlib
  (or sibling modules) unless it declares PEP 723 dependencies (`# /// script`); an import
  in an `except ImportError:` fallback (`try: import tomllib` / `except ImportError: import
  tomli`) is optional, so it doesn't count
- a Python script with a PEP 723 `# /// script` block has a `uv run --script` shebang, so
  running it directly installs what the block declares
  (https://docs.astral.sh/uv/guides/scripts/#using-a-shebang-to-create-an-executable-file)

authoring_rules.py runs check_script() on every file under a skill's scripts/;
tests/tooling/test_script_rules.py tests it.
"""

import ast
import os
import re
import sys

PROMPTS = re.compile(r"\bread\s+(?:-\w+\s+)*-p\b|/dev/tty|\binput\(|\bgetpass\b")
PEP723_BLOCK = re.compile(r"(?m)^# /// script[ \t]*\r?\n((?:^#[^\n]*\n)*?)^# ///[ \t]*$")
PEP723_DEPS = re.compile(r"""(?m)^dependencies\s*=\s*\[[^\]]*['"]""")
UV_SCRIPT_SHEBANG = re.compile(r"#!.*\buv\s+run\b.*\s--script\b")
IMPORT_ERRORS = frozenset({"ImportError", "ModuleNotFoundError"})


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
