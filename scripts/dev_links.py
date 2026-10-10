"""Dev-mode links from a home directory's skill dirs straight into this repo's skills.

The local equivalent of `npx skills add <repo>`, for live edits while developing skills
here. It mirrors the layout skills.sh produces, so a dev link and a skills.sh install
are interchangeable (never additive — no skill is linked twice):

    ~/.agents/skills/<name>            canonical store; a symlink to skills/<bucket>/<name>
    ~/.claude/skills/<name>            Claude Code's entry, a relative symlink into the
      -> ../../.agents/skills/<name>   store — exactly as skills.sh creates it

scripts/link-skills.py is the command line.
"""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Status:
    kind: str  # ok, missing, dead
    name: str
    detail: str = ""

    @property
    def fails(self):
        return self.kind != "ok"

    def __str__(self):
        return f"{self.kind:<9} {self.name}{' ' + self.detail if self.detail else ''}"


def claude_entry(name):
    return f"../../.agents/skills/{name}"


def dead_links(skills, home, repo):
    """Store links into this repo whose skill is gone — deleted, renamed, or moved to
    deprecated/. Linking only ever adds, so these would otherwise linger."""
    live = {str(s.folder) for s in skills}
    prefix = f"{repo / 'skills'}{os.sep}"
    if not home.store.is_dir():
        return []
    return [
        link
        for link in sorted(home.store.iterdir())
        if link.is_symlink() and os.readlink(link).startswith(prefix) and os.readlink(link) not in live
    ]


def check(skills, home, repo, command="scripts/link-skills.py"):
    """What isn't linked, and what's linked but gone, as statuses."""
    claude = home.agent_dir("claude-code")
    found = []
    for s in skills:
        if os.path.realpath(claude / s.name) == str(s.folder):
            found.append(Status("ok", s.name))
        else:
            found.append(Status("missing", s.name, f"(not linked into {claude} — run {command})"))
    for link in dead_links(skills, home, repo):
        found.append(Status("dead", link.name, f"({link} -> {os.readlink(link)} — run {command})"))
    return found


class LinkError(Exception):
    pass


def link(skills, home, repo, log=print):
    """Link every skill into the store and Claude Code, then prune dead links.

    A real directory where a link belongs is replaced: it's a prior `npx skills add`
    copy, and the dev link is meant to take over.
    """
    claude = home.agent_dir("claude-code")
    # A destination that is itself a link into this repo would get the per-skill links
    # written back into the working copy.
    for d in (home.store, claude):
        resolved = Path(os.path.realpath(d))
        if d.is_symlink() and (resolved == repo or repo in resolved.parents):
            raise LinkError(
                f"{d} is a symlink into this repo ({resolved}).\n"
                f'Remove it (rm "{d}") and re-run; the script will recreate it as a real dir.'
            )
    home.store.mkdir(parents=True, exist_ok=True)
    claude.mkdir(parents=True, exist_ok=True)

    for s in skills:
        replace(home.store / s.name, s.folder)
        replace(claude / s.name, claude_entry(s.name))
        log(f"dev-linked {s.name} -> {s.folder}")

    for dead in dead_links(skills, home, repo):
        dead.unlink()
        entry = claude / dead.name
        # Only Claude Code's own relative link into the store, nothing else by that name.
        if entry.is_symlink() and os.readlink(entry) == claude_entry(dead.name):
            entry.unlink()
        log(f"pruned {dead.name}")


def replace(path, target):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()
    path.symlink_to(target)
