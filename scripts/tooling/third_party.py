"""The curated third-party skills: third-party/skills.json and what installing it means.

The one reader of the manifest the tooling shares. It resolves each source's agent list
(a source's own `agents`, else the top-level one), plans the `npx skills add` calls and
the links into universal agents' directories, and compares a home directory against the
manifest. Everything that touches a home directory takes it as an argument, so tests run
against a throwaway one.

scripts/sync-third-party.py is the command line; see its docstring for the modes.
"""

import json
import os
import posixpath
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_FILE = "SKILL.md"


def _stdout(msg):
    # Flushed: the npx calls write straight to the terminal between these lines.
    print(msg, flush=True)


def _stderr(msg):
    print(msg, file=sys.stderr, flush=True)

# The per-agent skill directories the skills.sh CLI wires up, relative to the home
# directory. Used only to report drift and to link universal agents; installs go
# through the CLI, which owns the real agent-to-path map, so an agent missing here just
# goes unreported, never uninstalled.
AGENT_DIRS = {
    "claude-code": ".claude/skills",
    "github-copilot": ".copilot/skills",
    "gemini-cli": ".gemini/skills",
    "antigravity": ".gemini/config/skills",
    "codex": ".codex/skills",
}

# skills.sh treats these agents as "universal": a global install writes the store and
# never touches the agent's own directory. Whether each agent also reads the store
# varies by agent and version, so the sync links every curated skill into their
# directories itself; a symlink into the store is current whichever path is read
# (docs/adr/0003).
UNIVERSAL = ("codex", "github-copilot", "gemini-cli", "antigravity")

# Findings that mean the home directory disagrees with the manifest. The rest report
# installs from other channels, which may be deliberate.
FAILING = {"missing", "conflict", "archived", "drift", "invocation"}

# A curated skill's `invocation` in skills.json: who can start it (GLOSSARY.md).
INVOCATIONS = ("model", "user")
# `disable-model-invocation: true` in a SKILL.md's frontmatter, read without a YAML parser
# so the sync scripts stay stdlib-only. YAML 1.2 spells the boolean true, True or TRUE.
FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---", re.DOTALL)
USER_INVOKED = re.compile(r"^disable-model-invocation:[ \t]*(?:true|True|TRUE)[ \t]*(?:#.*)?$", re.MULTILINE)


@dataclass(frozen=True)
class Curated:
    name: str
    repo: str
    agents: tuple
    why: str
    path: str = ""  # the skill's folder in its repo
    invocation: str = ""  # "model" or "user", as skills.json records it; "" when it doesn't


@dataclass(frozen=True)
class Source:
    repo: str
    why: str
    agents: tuple
    skills: tuple  # Curated
    archived: tuple  # Curated, retired: kept with the reason, no longer installed


@dataclass(frozen=True)
class Manifest:
    sources: tuple

    @property
    def curated(self):
        return [k for s in self.sources for k in s.skills]

    @property
    def archived(self):
        return [k for s in self.sources for k in s.archived]


def text(value):
    """A free-text field: a missing or non-string value reads as empty."""
    return value if isinstance(value, str) else ""


def load(repo=REPO):
    """The manifest under `repo`, or None when it has none."""
    path = repo / "third-party/skills.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    sources = []
    for s in data["sources"]:
        # Empty when neither the source nor the manifest names agents; lint and the sync refuse it.
        agents = tuple(s.get("agents", data.get("agents", ())))

        def entries(kind, s=s, agents=agents):
            return tuple(Curated(k["name"], s["repo"], agents, text(k.get("why")), text(k.get("path")),
                                 text(k.get("invocation"))) for k in s.get(kind, []))

        sources.append(Source(s["repo"], text(s.get("why")), agents, entries("skills"), entries("archived")))
    return Manifest(tuple(sources))


@dataclass(frozen=True)
class Home:
    """Where the skills.sh CLI installs, under one home directory."""

    root: Path

    @property
    def store(self):
        return self.root / ".agents/skills"

    @property
    def lock(self):
        return self.root / ".agents/.skill-lock.json"

    def agent_dir(self, agent):
        return self.root / AGENT_DIRS[agent]


@dataclass(frozen=True)
class Link:
    name: str
    agent: str
    dir: Path


def wanted_links(manifest, home):
    """Every link into a universal agent's directory the manifest wants."""
    return [
        Link(k.name, agent, home.agent_dir(agent))
        for k in manifest.curated
        for agent in k.agents
        if agent in UNIVERSAL
    ]


def install_commands(manifest):
    """One `npx skills add` per source with something curated.

    A source with nothing curated is skipped: with no --skill flag the CLI would install
    every skill in the repo. One --skill / --agent flag per value; the CLI reads a
    comma-separated list as a single name.
    """
    commands = []
    for s in manifest.sources:
        if not s.skills:
            continue
        cmd = ["npx", "--yes", "skills@latest", "add", s.repo, "--global", "--yes"]
        for k in s.skills:
            cmd += ["--skill", k.name]
        for agent in s.agents:
            cmd += ["--agent", agent]
        commands.append((s, cmd))
    return commands


def sync(manifest, home, run=subprocess.run, log=_stdout, err=_stderr):
    """Install every source, then link universal agents. Returns what failed.

    A failing source doesn't stop the others, and the links are made either way.
    """
    failed = []
    for s, cmd in install_commands(manifest):
        log(f"==> {s.repo}: {','.join(k.name for k in s.skills)}")
        # stdin from /dev/null: the CLI would otherwise wait on a prompt it can't show.
        try:
            ok = run(cmd, stdin=subprocess.DEVNULL).returncode == 0
        except OSError as e:  # npx missing or not executable
            err(f"error: cannot run {cmd[0]}: {e.strerror}")
            ok = False
        if not ok:
            failed.append(f"install from {s.repo}")
    failed += link(manifest, home, log, err)
    return failed


def link(manifest, home, log=_stdout, err=_stderr):
    """Link each curated skill into the universal agents its source lists. Returns what failed.

    Refuses to replace anything that isn't already the link: a real directory there is a
    stale copy from another channel, and deleting it is the user's call.
    """
    failed = []
    for want in wanted_links(manifest, home):
        source = home.store / want.name
        destination = want.dir / want.name
        if not (source / SKILL_FILE).is_file():
            err(f"error: cannot link '{want.name}' into {want.agent}; no installed skill at {source}.")
            failed.append(f"link {want.name} into {want.agent}")
            continue
        if destination.exists() or destination.is_symlink():
            if os.path.realpath(destination) == os.path.realpath(source):
                continue
            err(f"error: refusing to replace '{destination}'; it isn't a link to the curated copy in the store.")
            err("       If it's a stale copy from another channel, move it aside and re-run the sync.")
            failed.append(f"link {want.name} into {want.agent}")
            continue
        want.dir.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(source)
        log(f"linked {want.name} into {want.agent}")
    return failed


@dataclass(frozen=True)
class Finding:
    kind: str
    name: str
    detail: str = ""

    @property
    def fails(self):
        return self.kind in FAILING

    def __str__(self):
        return f"{self.kind:<9} {self.name}{' ' + self.detail if self.detail else ''}"


def check(manifest, home, owned):
    """How `home` differs from the manifest, as findings. `owned`: owned skill names.

    Raises FileNotFoundError when nothing has been installed yet (no lock file).
    """
    lock = json.loads(home.lock.read_text())["skills"]
    return (_install_findings(manifest, lock) + _lock_findings(manifest, lock)
            + _unmanaged_findings(manifest, home, lock, owned) + _copy_findings(manifest, home)
            + _link_findings(manifest, home) + _invocation_findings(manifest, home))


def _install_findings(manifest, lock):
    """Each curated skill: ok, missing from the lock file, or installed from another source."""
    found = []
    for k in manifest.curated:
        installed = lock.get(k.name, {}).get("source")
        if not installed:
            found.append(Finding("missing", k.name, f"(from {k.repo})"))
        elif installed != k.repo:
            found.append(Finding("conflict", k.name, f"installed from {installed}, manifest says {k.repo}"))
        else:
            found.append(Finding("ok", k.name))
    return found


def _lock_findings(manifest, lock):
    """Installed from a remote source but absent from the manifest: curate it deliberately
    or remove it. Archived ones get their own line, since the manifest says they go."""
    found = []
    curated = {k.name for k in manifest.curated}
    archived = {k.name for k in manifest.archived}
    for name, entry in lock.items():
        if name in archived:
            found.append(Finding("archived", name, f"is still installed; remove it with: npx skills remove -g {name}"))
        elif entry.get("source") and entry.get("sourceType") == "github" and name not in curated:
            found.append(Finding("uncurated", name, f"(installed from {entry['source']})"))
    return found


def _unmanaged_findings(manifest, home, lock, owned):
    """Sitting in the store or an agent's directory with nothing managing it: absent from
    the lock file, uncurated, and not owned here. That's how another channel's install
    shows up (a plugin marketplace, or a hand copy) as a frozen snapshot with no
    upgrade path (docs/adr/0003). The store is scanned too: a store entry whose lock
    record is gone is unmanaged in exactly the sense that matters."""
    known = set(lock) | {k.name for k in manifest.curated} | set(owned)
    dirs = [home.store] + [home.agent_dir(a) for a in AGENT_DIRS]
    unmanaged = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for name in sorted(os.listdir(d)):
            if name not in known and (d / name / SKILL_FILE).exists():
                unmanaged.setdefault(name, []).append(str(d))
    return [Finding("unmanaged", name, f"(in {len(where)}: {', '.join(where)})") for name, where in unmanaged.items()]


def _copy_findings(manifest, home):
    """A curated skill can hold different content in the store and in an agent directory.
    Only an agent copy older than the store is actionable: an agent that missed an
    update. The reverse is a vestigial store entry: the CLI installs new skills straight
    into the agent directory and never refreshes an old store copy, so those get one
    summary line. Universal agents' directories are checked link by link instead."""
    found = []
    vestigial = 0
    for agent in AGENT_DIRS:
        if agent in UNIVERSAL:
            continue
        d = home.agent_dir(agent)
        for k in manifest.curated:
            there, here = d / k.name / SKILL_FILE, home.store / k.name / SKILL_FILE
            if not there.exists() or not here.exists() or there.read_bytes() == here.read_bytes():
                continue
            if there.stat().st_mtime < here.stat().st_mtime:
                found.append(Finding("drift", k.name, f"({d} is older than the store; re-sync from a plain terminal)"))
            else:
                vestigial += 1
    if vestigial:
        found.append(Finding("note", str(vestigial), f"store copies under {home.store} are older than what the agents load, and unused"))
    return found


def _link_findings(manifest, home):
    """Every universal agent's directory must hold a link into the store, not a copy."""
    found = []
    for want in wanted_links(manifest, home):
        destination = want.dir / want.name
        if os.path.realpath(destination) == os.path.realpath(home.store / want.name):
            continue
        if destination.is_symlink() or not destination.exists():
            detail = f"({want.agent} is missing the link {destination}; run the sync)"
        else:
            detail = f"({destination} is a stale copy, not a link into the store; move it aside, then run the sync)"
        found.append(Finding("drift", want.name, detail))
    return found


def _gh_token():
    """The gh CLI's token for github.com, or None when gh is missing or logged out."""
    try:
        done = subprocess.run(["gh", "auth", "token", "--hostname", "github.com"],
                              capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def invocation(skill_md):
    """"user" when a SKILL.md's frontmatter sets disable-model-invocation: true, else "model"."""
    m = FRONTMATTER.match(skill_md.read_text())
    return "user" if m and USER_INVOKED.search(m.group(1)) else "model"


def _invocation_findings(manifest, home):
    """A curated skill whose installed copy is invoked differently from what skills.json says.

    Upstream can flip a skill between model- and user-invoked; the manifest's record, the
    third-party catalog's grouping and the lint's Skill-tool check would then be wrong.
    Reads the store's copy, else the first agent directory that has one.
    """
    found = []
    for k in manifest.curated:
        if not k.invocation:
            continue  # lint reports the missing field
        copies = [d / k.name / SKILL_FILE for d in [home.store] + [home.agent_dir(a) for a in AGENT_DIRS]]
        installed = next((c for c in copies if c.is_file()), None)
        if installed is None:
            continue  # missing is _install_findings' to report
        actual = invocation(installed)
        if actual != k.invocation:
            found.append(Finding("invocation", k.name,
                                 f"(skills.json says {k.invocation}-invoked; the installed copy is {actual}-invoked; "
                                 "update skills.json and run scripts/build-catalog.py)"))
    return found


def github_folders(repo):
    """{folder path: git tree SHA} for every folder on `repo`'s default branch ("" is the root).

    One GitHub API call; a token lifts the anonymous rate limit of 60 calls an hour:
    GH_TOKEN or GITHUB_TOKEN when set, else the gh CLI's login when there is one. Raises OSError when GitHub can't be reached, ValueError when the
    answer isn't a complete tree.
    """
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/git/trees/HEAD?recursive=1",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "skills-sync-third-party"},
    )
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or _gh_token()
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("truncated") or "tree" not in data:
        raise ValueError("GitHub returned an incomplete tree")
    return {"": data["sha"]} | {e["path"]: e["sha"] for e in data["tree"] if e.get("type") == "tree"}


def outdated(manifest, home, folders=github_folders):
    """Curated skills whose folder upstream has changed since they were installed.

    The skills.sh lock file records each install's `skillFolderHash`, the git tree SHA of
    the skill's folder at the commit it installed, so comparing it with the folder's SHA on
    the default branch today says whether a sync would change anything. Skills that aren't
    installed from their curated source are left to check(). Findings: `outdated` (changed
    or gone upstream) and `unknown` (the source couldn't be read).
    """
    lock = json.loads(home.lock.read_text())["skills"]
    found, trees = [], {}
    for k in manifest.curated:
        entry = lock.get(k.name, {})
        if entry.get("source") != k.repo:
            continue
        if k.repo not in trees:
            try:
                trees[k.repo] = folders(k.repo)
            except (OSError, ValueError) as e:
                trees[k.repo] = e
        tree = trees[k.repo]
        if isinstance(tree, Exception):
            found.append(Finding("unknown", k.name, f"(couldn't read {k.repo}: {tree})"))
            continue
        folder = posixpath.dirname(entry.get("skillPath", ""))
        upstream = tree.get(folder)
        if upstream is None:
            found.append(Finding("outdated", k.name, f"({k.repo} no longer has {folder or 'a root skill'}/)"))
        elif upstream != entry.get("skillFolderHash"):
            since = (entry.get("updatedAt") or entry.get("installedAt") or "?")[:10]
            found.append(Finding("outdated", k.name, f"({k.repo} changed it since the install of {since}; run the sync)"))
    return found


def listing(manifest):
    """The curated list with the reason for each skill, as lines."""
    lines = []
    for s in manifest.sources:
        lines += ["", f"{s.repo}: {s.why}"]
        lines += [f"  {k.name:<30} {k.why}" for k in s.skills]
        lines += [f"  {k.name + ' (archived)':<30} {k.why}" for k in s.archived]
    return lines
