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
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _stdout(msg):
    # Flushed: the npx calls write straight to the terminal between these lines.
    print(msg, flush=True)


def _stderr(msg):
    print(msg, file=sys.stderr, flush=True)

# The per-agent skill directories the skills.sh CLI wires up, relative to the home
# directory. Used only to report drift and to link universal agents — installs go
# through the CLI, which owns the real agent-to-path map, so an agent missing here just
# goes unreported, never uninstalled.
AGENT_DIRS = {
    "claude-code": ".claude/skills",
    "github-copilot": ".copilot/skills",
    "gemini-cli": ".gemini/skills",
    "antigravity": ".gemini/antigravity/skills",
    "codex": ".codex/skills",
}

# skills.sh treats these agents as "universal": a global install writes the store and
# never touches the agent's own directory. Whether each agent also reads the store
# varies by agent and version, so the sync links every curated skill into their
# directories itself — a symlink into the store is current whichever path is read
# (docs/adr/0003).
UNIVERSAL = ("codex", "github-copilot", "gemini-cli", "antigravity")

# Findings that mean the home directory disagrees with the manifest. The rest report
# installs from other channels, which may be deliberate.
FAILING = {"missing", "conflict", "archived", "drift"}


@dataclass(frozen=True)
class Curated:
    name: str
    repo: str
    agents: tuple
    why: str


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


def load(repo=REPO):
    """The manifest under `repo`, or None when it has none."""
    path = repo / "third-party/skills.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    sources = []
    for s in data["sources"]:
        agents = tuple(s.get("agents", data.get("agents", [])))

        def entries(kind, s=s, agents=agents):
            return tuple(Curated(k["name"], s["repo"], agents, k.get("why", "")) for k in s.get(kind, []))

        sources.append(Source(s["repo"], s.get("why", ""), agents, entries("skills"), entries("archived")))
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
    every skill in the repo. One --skill / --agent flag per value — the CLI reads a
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
        if run(cmd, stdin=subprocess.DEVNULL).returncode != 0:
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
        if not (source / "SKILL.md").is_file():
            err(f"error: cannot link '{want.name}' into {want.agent}; no installed skill at {source}.")
            failed.append(f"link {want.name} into {want.agent}")
            continue
        if destination.exists() or destination.is_symlink():
            if os.path.realpath(destination) == os.path.realpath(source):
                continue
            err(f"error: refusing to replace '{destination}' — it isn't a link to the curated copy in the store.")
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
    found = []

    for k in manifest.curated:
        installed = lock.get(k.name, {}).get("source")
        if not installed:
            found.append(Finding("missing", k.name, f"(from {k.repo})"))
        elif installed != k.repo:
            found.append(Finding("conflict", k.name, f"installed from {installed}, manifest says {k.repo}"))
        else:
            found.append(Finding("ok", k.name))

    # Installed from a remote source but absent from the manifest: curate it deliberately
    # or remove it. Archived ones get their own line, since the manifest says they go.
    curated = {k.name for k in manifest.curated}
    archived = {k.name for k in manifest.archived}
    for name, entry in lock.items():
        if name in archived:
            found.append(Finding("archived", name, f"is still installed — remove it with: npx skills remove -g {name}"))
        elif entry.get("source") and entry.get("sourceType") == "github" and name not in curated:
            found.append(Finding("uncurated", name, f"(installed from {entry['source']})"))

    # Sitting in the store or an agent's directory with nothing managing it: absent from
    # the lock file, uncurated, and not owned here. That's how another channel's install
    # shows up — a plugin marketplace, or a hand copy — as a frozen snapshot with no
    # upgrade path (docs/adr/0003). The store is scanned too: a store entry whose lock
    # record is gone is unmanaged in exactly the sense that matters.
    known = set(lock) | curated | set(owned)
    dirs = [home.store] + [home.agent_dir(a) for a in AGENT_DIRS]
    unmanaged = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for name in sorted(os.listdir(d)):
            if name not in known and (d / name / "SKILL.md").exists():
                unmanaged.setdefault(name, []).append(str(d))
    for name, where in unmanaged.items():
        found.append(Finding("unmanaged", name, f"(in {len(where)}: {', '.join(where)})"))

    # A curated skill can hold different content in the store and in an agent directory.
    # Only an agent copy older than the store is actionable — an agent that missed an
    # update. The reverse is a vestigial store entry: the CLI installs new skills straight
    # into the agent directory and never refreshes an old store copy, so those get one
    # summary line. Universal agents' directories are checked link by link below.
    vestigial = 0
    for agent in AGENT_DIRS:
        if agent in UNIVERSAL:
            continue
        d = home.agent_dir(agent)
        for k in manifest.curated:
            there, here = d / k.name / "SKILL.md", home.store / k.name / "SKILL.md"
            if not there.exists() or not here.exists() or there.read_bytes() == here.read_bytes():
                continue
            if there.stat().st_mtime < here.stat().st_mtime:
                found.append(Finding("drift", k.name, f"({d} is older than the store — re-sync from a plain terminal)"))
            else:
                vestigial += 1
    if vestigial:
        found.append(Finding("note", str(vestigial), f"store copies under {home.store} are older than what the agents load, and unused"))

    # Every universal agent's directory must hold a link into the store, not a copy.
    for want in wanted_links(manifest, home):
        destination = want.dir / want.name
        if os.path.realpath(destination) == os.path.realpath(home.store / want.name):
            continue
        if destination.is_symlink() or not destination.exists():
            detail = f"({want.agent} is missing the link {destination} — run the sync)"
        else:
            detail = f"({destination} is a stale copy, not a link into the store — move it aside, then run the sync)"
        found.append(Finding("drift", want.name, detail))
    return found


def listing(manifest):
    """The curated list with the reason for each skill, as lines."""
    lines = []
    for s in manifest.sources:
        lines += ["", f"{s.repo} — {s.why}"]
        lines += [f"  {k.name:<30} {k.why}" for k in s.skills]
        lines += [f"  {k.name + ' (archived)':<30} {k.why}" for k in s.archived]
    return lines
