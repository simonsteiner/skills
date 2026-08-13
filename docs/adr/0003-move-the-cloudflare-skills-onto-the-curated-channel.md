# The Cloudflare skills move from the plugin marketplace onto the curated channel

## Context

[ADR 0002](./0002-curate-third-party-skills-instead-of-vendoring.md) set up `third-party/skills.json` as the source of truth for skills I don't own, with `--check` to catch drift. It then reported everything clean — while eleven Cloudflare skills were loading in every session, unaccounted for.

They had come in through a completely different channel: `cloudflare/skills` was registered as a **Claude Code plugin marketplace** (a git clone under `~/.claude/plugins/marketplaces/cloudflare`), and the skills had also been copied as plain directories into four agent dirs — `~/.claude/skills`, `~/.copilot/skills`, `~/.gemini/skills`, `~/.gemini/antigravity/skills`. No plugin was ever enabled, so those copies are what actually load.

Nothing managed them. They were absent from the skills.sh lock file, so `--check` — which only read that lock — couldn't see them. They were frozen at an upstream commit from 2026-07-24 with no upgrade path, and had been for weeks. Upstream had already deleted `sandbox-sdk` and split it into `sandbox-stable` / `sandbox-next` / `sandbox-migrate-to-next`; the local copy of a skill that no longer exists was still being offered to the model.

## Decision

**Curate them like everything else, and teach `--check` to see this class of drift.**

- Added `cloudflare/skills` to the manifest with the eleven skills, `sandbox-sdk` replaced by `sandbox-stable`.
- Added a per-source `agents` override. The top-level list stays `claude-code`; this one source is curated into all four agents that already carried it, so curating Cloudflare doesn't push the other skills into agents that never had them.
- Left `commands/build-agent.md`, `commands/build-mcp.md`, and `rules/workers.mdc` behind. Only the plugin channel installs those, and taking the plugin back would reintroduce the second channel this ADR exists to remove.
- Extended `--check` with two reports: `unmanaged` (a skill in an agent directory that the lock, the manifest, and this repo all disown) and `drift` (a curated skill whose content differs between an agent directory and the store).

## Consequences

- **`--check` now sees what it previously couldn't**, and immediately found `sandbox-sdk` still sitting in four directories — the corpse of the upstream rename, left there because nothing ever managed it. Cleaning it up is a deliberate deletion, not something the sync does.
- **Losing the two `/build-*` commands and the Workers rule** is the price of one channel. If they turn out to matter, the honest options are to install the plugin *as well* and accept two update paths, or copy their content into a skill this repo owns.
- **Multi-agent syncs must be run from a plain terminal.** The CLI installs to whichever agent it detects itself running under, so a sync from inside Claude Code updates only the store and Claude Code — the other three agents keep their old copies until it's re-run outside. The script header says this; nothing enforces it.
- **The store is not the source of truth.** The CLI wires some agents up by symlink and others by copy, and doesn't always refresh both: right after a successful sync, `~/.claude/skills/code-review` held current upstream content while `~/.agents/skills/code-review` was still on a July copy. `drift` therefore reports the disagreement and names the older file rather than assuming a winner.
- **The registered marketplace is now inert but still present.** It's a stale git clone that no longer explains anything on disk; removing it is a separate cleanup.
