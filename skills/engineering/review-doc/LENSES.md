# Lenses

Read in Step 2. Each section below is copied verbatim into one reviewer's brief, so it speaks to the reviewer.

## Contents

- Paraphrase
- Simplicity
- Readiness

## Paraphrase

You have never seen this project's conversations, decisions or plans. You know software; you don't know this project. Read the doc and the files on your reading list.

1. Write two short paragraphs in your own words, 2-5 sentences each: **What this proposes** and **How the existing system works, according to this doc**. Paraphrase; don't quote. A section you can't paraphrase is a **Blocker**: name it and say where you lost the thread. A list of undefined terms won't catch a doc whose terms are all defined but whose parts don't connect; the paraphrase will.
2. Then look for:
   - **Undefined terms**: names specific to this project, team or design, used without a definition in the doc or a link. Not general engineering terms. Check the whole doc first; a term defined only after its first use is a **Nit**.
   - **Unstated prerequisites**: steps that assume setup, permissions, data or side effects the doc never states.
   - **Hand-waves**: "handled automatically", "the usual way", "as discussed", anything that points at knowledge outside the doc without saying what it is or where to find it.
   - **Invisible references**: "the Friday rule", "option B", a meeting, a ticket with no link.

Return the two paragraphs first, then the findings.

## Simplicity

Read the doc and your reading list, and search the repo. The question: is this the simplest design that solves the stated problem, built from what the repo already has?

- **Stated problem.** If you can't tell what problem the doc solves and why it matters now, stop: that's the only finding, a **Blocker**.
- **Root cause.** Does the design fix the problem, or a symptom of it?
- **Reuse.** For each new module, helper, service, table or dependency the doc proposes, search the repo for one that already does the job: `git grep` its verb and noun, and look where shared code lives. A match is **Major**; name the file and symbol.
- **Speculation.** Config, extension points, abstractions or features for requirements the doc doesn't state. Caching, queues, sharding or async work with no measured bottleneck.
- **Altitude.** In a design section, code-level detail (helper names, loop logic) that buries the architecture. Leave detail alone in an implementation plan.
- **Fit.** New logic in the wrong layer or against a pattern the repo already uses (cite the pattern), or a design that blocks a next step the doc names.
- **Alternatives.** A choice with real alternatives and no word on why this one: **Major**. An option rejected because "a maintainer said so", with no link: **Nit**.
- **Risks.** Failure modes, security boundaries, data migrations or scaling limits the design creates and doesn't address.

Each finding names what to cut or what to reuse, not only that something is too much. Each pattern you suggest names its own cost.

## Readiness

You will build this tomorrow, from this doc alone. Read the doc, your reading list, and the code it touches.

- **No decisions left.** Every place where you'd have to make a design choice yourself (a schema, an API shape, an error strategy, a dependency, what happens on an edge case) is a finding: **Major**, or **Blocker** when everything after it depends on the choice.
- **Actionable steps.** "Update the auth service" isn't a step; "add `expires_at` to `Session` in `src/auth/session.ts`" is. Flag the first kind.
- **File list.** The files to create, change or delete, each marked as which. A plan with no file list, or with unmarked paths, is one **Major**, not one per path.
- **Claims about current code.** Check that every file, function, endpoint, table or flag the doc says exists now does exist and does what the doc says. A false claim about current behaviour is a **Blocker**: every later reader inherits it. Files the plan will create aren't findings.
- **Order.** Each phase leaves the code building and its tests passing. A phase that doesn't, or a plan with no order, is **Major**.
- **Tests.** The cases that prove each part works, edge cases included. None named: **Major**.
- **Rollout.** Migration, backward compatibility and rollback, when the change touches stored data or a public interface.
