# Integrating microsoft/apm and microsoft/agentrc

Exploration of whether [microsoft/apm](https://github.com/microsoft/apm) (Agent Package Manager) and [microsoft/agentrc](https://github.com/microsoft/agentrc) are candidates for curation in simonsteiner/skills.

## Quick Summary

Both are **complementary tooling**, not skills repositories. Neither natively ships skills in SKILL.md format, but:

- **apm**: Distributes agent configuration (instructions, skills, prompts, MCP servers, plugins) via manifest-driven package management. Does ship **reusable skills** that can be extracted and curated.
- **agentrc**: Analyzes codebases and generates agent instruction files. Ships **4 built-in skills** for instruction generation that follow the SKILL.md format.

Both work **with** the skills.sh model rather than as part of it. The right integration path depends on your use case.

---

## What They Are

### microsoft/apm — Agent Package Manager

**Purpose:** A distributed, reproducible dependency manager for AI agent context (like npm for agent config).

**Key idea:** One `apm.yml` file declares an agent's dependencies — instructions, skills, prompts, plugins, MCP servers — and `apm install` reproduces the setup everywhere.

**Example apm.yml:**
```yaml
name: my-project
version: 1.0.0
dependencies:
  apm:
    - anthropics/skills/skills/frontend-design
    - github/awesome-copilot/plugins/context-engineering
    - github/awesome-copilot/agents/api-architect.agent.md
  mcp:
    - name: io.github.github/github-mcp-server
      transport: http
```

**Supported targets:** Copilot, Claude Code, Cursor, OpenCode, Codex, Gemini, Windsurf, Kiro.

**Structure:**
- Root `/apm.yml` and `/apm.lock.yaml` for manifest and lockfile.
- `/packages/` contains reusable sub-packages (e.g., `apm-issue-autopilot`, `apm-contributor-dashboard`).
- Each package has its own `apm.yml` and `SKILL.md` files.
- `.apm/` directory for configuration and extensions.

**First-party skills found:**
- `apm-issue-autopilot` — intake-to-merge issue orchestrator.
- `batch-bug-shepherd` — batch bug triage and PR shepherding.
- `shepherd-driver` — single-PR drive-to-merge convergence loop.
- `apm-review-panel` — PR review panel (transitive dependency).
- `apm-triage-panel` — issue triage rubric (transitive dependency).
- `pr-description-skill` — anchored PR description generation.
- `apm-guide` — teaches agents how to use APM.
- `apm-contributor-dashboard` — interactive GitHub dashboard for Copilot CLI.

All follow the `SKILL.md` pattern with detailed documentation, boundary contracts, composition instructions, and eval fixtures.

### microsoft/agentrc — Context Engineering

**Purpose:** Analyze a repository and generate agent instruction files tailored to its codebase.

**Key commands:**
- `agentrc readiness` — score a repo's AI-readiness across 9 pillars (style, build, testing, docs, dev-env, code-quality, observability, security, AI tooling).
- `agentrc instructions` — generate `.github/copilot-instructions.md` from codebase analysis.
- `agentrc eval` — evaluate whether instructions improve agent responses.
- `agentrc init` — interactive setup for a repository.

**Generated files:**
- `.github/copilot-instructions.md` — root repo instructions.
- `.instructions.md` — area-scoped instructions (for monorepos).
- `AGENTS.md` — lean hub file with links to detailed instruction files.
- `.vscode/mcp.json` — MCP server configuration.
- `.vscode/settings.json` — VS Code settings for AI-assisted development.
- `agentrc.eval.json` — test cases to measure instruction quality.

**Built-in skills (all in `plugin/skills/`):**
- `root-instructions` — generate root `.github/copilot-instructions.md` by analyzing the codebase.
- `area-instructions` — generate scoped `.instructions.md` for a specific area.
- `nested-hub` — generate a lean `AGENTS.md` hub file with recommended topics.
- `nested-detail` — generate a deep-dive instruction file on a specific topic.

All are **SKILL.md format** with YAML frontmatter (name, description) and Copilot SDK integration.

**Works with:** GitHub, Azure DevOps, monorepos, multi-root VS Code workspaces.

**Works with APM:** The `.instructions.md` format is shared. AgentRC generates content; APM distributes it across teams.

---

## Integration Paths

### Path 1: Curate APM Skills (Most Aligned with Your Model)

APM ships 5+ reusable first-party skills that follow SKILL.md format. You could curate them like you do Cloudflare's:

**Entry in `third-party/skills.json`:**
```json
{
  "repo": "microsoft/apm",
  "agents": ["claude-code"],
  "why": "Microsoft's Agent Package Manager. Curated for three high-impact orchestrator skills and the shared review/triage panels they depend on. See docs/adr/0002.",
  "skills": [
    {
      "name": "batch-bug-shepherd",
      "path": "packages/batch-bug-shepherd",
      "why": "Batch bug triage and PR shepherding. Composes apm-triage-panel + shepherd-driver. See .agents/skills/ for transitive deps."
    },
    {
      "name": "apm-issue-autopilot",
      "path": "packages/apm-issue-autopilot",
      "why": "Intake-to-merge issue orchestrator. Full composition chain: apm-triage-panel -> shepherd-driver -> apm-review-panel. Entrypoint for queue automation."
    },
    {
      "name": "pr-description-skill",
      "path": "packages/pr-description-skill",
      "why": "Anchored PR body generation from diff. Evals prove it writes clearer, more information-dense descriptions than baseline Copilot."
    },
    {
      "name": "apm-guide",
      "path": "packages/apm-guide",
      "why": "Teaches agents how to use APM itself. Useful for any agent workflow involving package management or config distribution."
    }
  ]
}
```

**Pros:**
- Follows your existing curation model (referenced, not vendored).
- No duplication of effort — upstream maintains the source.
- Leverages skills.sh CLI's existing `apm install` compatibility.
- The skills are **mature, battle-tested** (Microsoft's own repo uses them).
- Comes with eval fixtures showing quality improvements.

**Cons:**
- APM's transitive dependency model is complex (shepherd-driver composes apm-review-panel, etc.). Your sync script would need to handle multi-level paths.
- APM's skills are **domain-specific** (issue/PR automation) — less breadth than Cloudflare's.
- Upstream moving fast (v0.10.0 currently) — breakage risk is higher than stable repos.

---

### Path 2: Curate AgentRC Skills (Smaller Surface Area)

AgentRC ships 4 built-in skills for instruction generation. All are in `plugin/skills/` with SKILL.md frontmatter:

**Entry in `third-party/skills.json`:**
```json
{
  "repo": "microsoft/agentrc",
  "agents": ["claude-code"],
  "why": "AgentRC: context engineering for AI agents. Curated for the 4 built-in instruction-generation skills. See plugin/skills/ for details.",
  "skills": [
    {
      "name": "root-instructions",
      "path": "plugin/skills/root-instructions",
      "why": "Generate .github/copilot-instructions.md by analyzing codebase structure, tech stack, conventions. First step in instruction generation."
    },
    {
      "name": "area-instructions",
      "path": "plugin/skills/area-instructions",
      "why": "Generate .instructions.md for a specific area of a codebase. Used in monorepos and multi-module projects."
    },
    {
      "name": "nested-hub",
      "path": "plugin/skills/nested-hub",
      "why": "Generate AGENTS.md hub file with recommended topics for detail files. Orchestrates the nested instruction hierarchy."
    },
    {
      "name": "nested-detail",
      "path": "plugin/skills/nested-detail",
      "why": "Generate deep-dive instruction file on a specific topic. Works with nested-hub to build comprehensive instruction sets."
    }
  ]
}
```

**Pros:**
- All 4 skills are **cohesive** (form a workflow: hub → details).
- No transitive complexity (each is self-contained).
- SKILL.md frontmatter is clean and lightweight.
- Active maintenance (under development, recent commits).
- Smaller repo surface → lower maintenance burden.

**Cons:**
- **Narrower scope**: instruction generation only. Not as broadly applicable as APM or Cloudflare.
- **Young project** (experimental; breaking changes expected per README).
- Depends on Copilot SDK (`github/copilot-sdk`) — adds a dependency.

---

### Path 3: Document APM/agentrc as Companion Tooling (No Curation)

Rather than curating skills, document how to use APM and agentrc **alongside** your skills:

**New file: `docs/integrations/apm-agentrc-workflow.md`**
```markdown
# Using your skills with APM and AgentRC

## The Workflow

1. **Generate repo context** with agentrc:
   ```bash
   agentrc init /path/to/repo
   agentrc instructions --repo /path/to/repo
   ```
   This generates `.github/copilot-instructions.md` and area-specific files.

2. **Package it with APM** for team distribution:
   ```bash
   apm init my-team-standards
   # Edit apm.yml to include your instructions, shared skills, MCP servers
   ```

3. **Install your skills** once the repo context is ready:
   ```bash
   apm install simonsteiner/skills --skill address-review-findings
   ```

## Why This Order

- AgentRC tells you **what your repo needs** (codebase-specific guidance).
- APM lets you **distribute that guidance** (team-wide portability).
- Your skills **execute** within that context (optimized for your team's standards).

## Example: Full Stack

```yaml
# apm.yml in your repo
name: my-project
version: 1.0.0
dependencies:
  apm:
    - simonsteiner/skills/skills/engineering/conventional-commit
    - simonsteiner/skills/skills/engineering/sync-and-branch
    - your-team/standards  # APM package with agentrc-generated instructions
```

Then:
```bash
apm install
# Installs skills from simonsteiner/skills + your team's shared context
```
```

**Pros:**
- Low coupling — each tool owns its domain.
- No maintenance burden (tools are external).
- Positions skills as **part of a larger ecosystem** rather than competing with APM.

**Cons:**
- No integration (just documentation).
- Users need to understand three tools instead of one.

---

### Path 4: Wrap APM/agentrc as a User-Invoked Skill (Most Ambitious)

Create a skill that wraps or orchestrates APM/agentrc workflow:

```
skills/engineering/repo-readiness-checkpoint/
├── SKILL.md                 # Invokes agentrc + apm + your review skills
├── assets/agentrc-config.json
├── templates/apm-template.yml
└── scripts/bootstrap.sh
```

**Pros:**
- Makes repo preparation **first-class** in your workflow.
- Users have one entry point instead of juggling multiple tools.

**Cons:**
- **High maintenance cost** — you're wrapping external tools; upstream changes break you.
- Couples your skills to APM/agentrc versions.
- Only worthwhile if you have strong opinions about *how* agentrc/apm should run.

---

## Recommendation

**Start with Path 1 + Path 3 combined:**

1. **Curate APM skills** into `third-party/skills.json` — they're mature, reusable, and well-documented.
2. **Add a companion integration guide** in `docs/integrations/apm-agentrc-workflow.md` explaining how to use APM + agentrc to prepare a repo, then install your skills.

This gives you:
- Immediate value from APM's orchestration skills.
- Clear positioning in a broader ecosystem (you're not competing with APM; you're complementary).
- A documented workflow that helps users understand the full picture.

**Path 2 (AgentRC skills) is lower priority** — the project is young and narrower in scope. Revisit after it reaches v1.0.0 stable.

---

## Technical Details for Curation

### APM Skill Paths

Skills are in `packages/` and `.agents/skills/`. The sync script needs to handle:

```
microsoft/apm/packages/batch-bug-shepherd/
  ├── apm.yml
  ├── SKILL.md
  ├── assets/
  ├── scripts/
  └── ... (support files)
```

APM uses `apm.yml` for package metadata and declares transitive dependencies. The skills.sh CLI may need special handling for composite dependencies.

### AgentRC Skill Paths

Skills are flat under `plugin/skills/`:

```
microsoft/agentrc/plugin/skills/root-instructions/
  ├── SKILL.md  (with YAML frontmatter)
  └── ... (no other files)
```

Path resolution is simpler: just `plugin/skills/root-instructions`, `plugin/skills/area-instructions`, etc.

### Lockfile & Version Pinning

APM publishes `apm.lock.yaml` for full provenance. AgentRC is version-agnostic (no lockfile). Your sync script (`scripts/sync-third-party.sh`) should:

1. Pin APM to a specific release (not rolling main branch).
2. Let AgentRC float (or pin to latest release tag).
3. Document in `third-party/README.md` why each choice.

---

## Codebase Analysis

### microsoft/apm Structure

```
apm/
├── apm.yml                         # Root manifest declaring skills
├── apm.lock.yaml                   # Lockfile (provenance + hashes)
├── packages/
│   ├── apm-issue-autopilot/        # Orchestrator skill
│   │   ├── apm.yml
│   │   ├── SKILL.md
│   │   ├── assets/
│   │   └── evals/fixtures
│   ├── batch-bug-shepherd/         # Orchestrator skill
│   ├── shepherd-driver/            # Drives a single PR to mergeability
│   ├── apm-review-panel/           # Review panel (composed by others)
│   ├── apm-triage-panel/           # Triage panel (composed by others)
│   ├── pr-description-skill/       # Anchored PR body generation
│   ├── apm-guide/                  # Teaches APM usage
│   ├── apm-contributor-dashboard/  # Copilot CLI canvas extension
│   └── ...
├── .agents/skills/                 # Symlinks or copies of above
├── docs/                           # Extensive documentation
├── src/                            # Python CLI source
└── scripts/                        # Build, test, dev scripts
```

Key observation: APM uses **local-path dependencies** (`./packages/...` in apm.yml). Consumers can reference external paths or git sources.

### microsoft/agentrc Structure

```
agentrc/
├── plugin/skills/                  # Built-in skills directory
│   ├── root-instructions/
│   │   └── SKILL.md               # Yaml frontmatter + markdown
│   ├── area-instructions/
│   ├── nested-hub/
│   └── nested-detail/
├── packages/
│   └── core/
│       ├── src/services/skills.ts  # Skill directory resolution
│       └── ...
├── src/
│   ├── commands/                   # CLI commands (readiness, instructions, eval)
│   └── services/
├── docs/                           # CLI docs, guides, examples
└── examples/                       # Sample configs and policies
```

Key observation: Skills are resolved via `getBuiltinSkillsDir()` from the Copilot SDK. No manifest file needed for skills — just SKILL.md with frontmatter.

---

## Related ADRs & Docs

- **ADR 0001** (fork-and-pare-down): Why you hard-forked and don't track upstream Mattpocock skills.
- **ADR 0002** (curate-third-party): Your decision to curate vs vendor third-party skills.
- **ADR 0003** (multi-agent deployment): Why you curate Cloudflare skills across multiple agents (Claude, Copilot, etc.).

---

## Next Steps

1. **Decide on Path 1 vs Path 3** (or both).
2. **If Path 1:** Open an issue to discuss APM's transitive dependency model with your sync script.
3. **If Path 3:** Draft `docs/integrations/apm-agentrc-workflow.md` with examples.
4. **Monitor agentrc** releases — revisit for Path 2 curation once v1.0.0 is stable.
5. **Test sync script** with APM paths to ensure `skills.sh` CLI can resolve local-path dependencies.

---

## References

- APM README: https://github.com/microsoft/apm/blob/main/README.md
- APM Manifesto: https://github.com/microsoft/apm/blob/main/MANIFESTO.md
- AgentRC README: https://github.com/microsoft/agentrc/blob/main/README.md
- AgentRC Concepts: https://github.com/microsoft/agentrc/blob/main/docs/concepts.md
- Open standards: AGENTS.md, Agent Skills (agentskills.io), MCP

