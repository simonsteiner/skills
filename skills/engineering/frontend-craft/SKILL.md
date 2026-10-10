---
name: frontend-craft
description: >
  Designs and builds frontend UI with a deliberate point of view instead of templated defaults — picks the surface's mode, plans a compact token system, reviews the plan against the brief, builds to a quality floor, and checks the render in bounded passes. Also critiques or audits existing UI and handles bolder, quieter, simpler, or polish requests. Use when building or redesigning a website, landing page, dashboard, app screen, component, form, or settings page; when the user asks for a UI to look less generic, better designed, bolder, or calmer; or when asked to critique, audit, or polish a frontend. Not for backend-only work.
metadata:
  credits:
    - skill: frontend-design
      author: Anthropic
      url: "https://github.com/anthropics/skills/tree/main/skills/frontend-design"
    - skill: impeccable
      author: Paul Bakaus
      url: "https://github.com/pbakaus/impeccable"
---

# Frontend Craft

Work as the design lead of a studio known for giving every client an identity no one mistakes for anyone else's. This client has already rejected proposals that felt templated. Make deliberate, opinionated choices about palette, type, and layout that belong to this brief, and take aesthetic risk where it's earned.

**The brief wins.** Pinned aesthetics, fonts, palettes, eras, or materials are followed exactly, even when they land on a look this skill calls a default. Redirecting a clear brief toward your own taste is failure.

**Refinement preserves; redesign replaces.** A refinement keeps the incumbent identity, behaviour, copy, and everything outside its scope. A redesign keeps product truth, content, function, and constraints, but treats the old look as evidence, not authority — never split the difference by polishing a look you were asked to replace. A section or component added to an established surface inherits that surface; it is never a new identity exercise.

**Read what's already true.** Before designing, read the project's `DESIGN.md` if there is one, then its tokens, components, and representative screens. A coherent identity already in code is authority even with no `DESIGN.md`. Don't create a `DESIGN.md` unless asked.

Pick the entry from what was asked:

- **Build or redesign** a surface — [Build](#build).
- **Refine** something that exists (bolder, quieter, simpler, polish, copy) — [Refine](#refine).
- **Critique or audit** — read [REVIEW.md](REVIEW.md) and follow it. Don't fix anything until the user picks what to address.

---

## Build

### 1. Ground it in the subject and pick the mode

If the brief doesn't say what the product is, who it's for, and what this surface must do, propose one concrete answer for each and confirm it. The subject's industry, materials, and vernacular are where distinctive choices come from — a toy for 8–11-year-olds and a dashboard for financial analysts look nothing alike. Use real content throughout.

Pick the **mode** from the surface, not the product — it decides how far the design may reach:

- **Persuade** — the visitor decides and acts: landing, marketing, pricing. Design is the product.
- **Operate** — the visitor completes a task: app UI, dashboards, admin, settings. Familiarity and scanability outrank expression.
- **Read** — the visitor understands something: docs, articles, changelogs. The frame carries the identity; the reading column stays calm.
- **Experience** — the visitor is inside the work: portfolios, galleries. The work leads from the first viewport.

A tool's landing page is Persuade; a fashion house's docs are Read. Read [MODES.md](MODES.md) for what each mode allows before planning. Where a mode's rules conflict with the general guidance here or in FLOOR.md — motion and typefaces on an Operate surface, say — the mode wins.

### 2. Plan a token system

Brainstorm a compact plan before code:

- **Colour** — a strategy first (Restrained: tinted neutrals plus one accent; Committed: one saturated colour on 30–60% of the surface; Full palette: 3–4 named roles; Drenched: the surface *is* the colour), then 4–6 named hex values. Light or dark comes from the use scene — who, where, under what light — never from the category.
- **Type** — one or two families and their roles. If two, make them clearly distinct. Choose them like objects from the subject's world, not the faces you'd reach for on any project. A clear scale with deliberate weights, widths, and spacing.
- **Layout** — a one-sentence concept per option and an ASCII wireframe to compare them, with alignment guidance.
- **Principles** — what makes this surface unmistakably this product's, and the one memorable move it spends its boldness on.

### 3. Review the plan against the brief

AI-generated design clusters around a few looks regardless of subject:

1. Warm cream ground (near `#F4F1EA`), high-contrast serif display, terracotta or clay accent (often near `#D97757` — Anthropic's own accent, so on a user's brief it reads as a tell).
2. Near-black ground with one acid-green or vermilion accent.
3. Broadsheet layout: hairline rules, zero radius, dense newspaper columns.
4. The SaaS card kit: content chopped into identical rounded cards, one radius on everything, the same soft grey shadow, gradient washes as decoration.
5. Template chrome: a tracked-out ALL-CAPS eyebrow above every heading, `A · B · C` meta strings, `WORD — fragment` labels, `#0B0B0B` standing in for black, monospace for small labels, `→` appended to every link.

Each is legitimate when the brief asks for it. Where an axis is free, landing on one means you weren't deciding. Work through a similar prompt in your head: if you'd arrive at the same plan for a different product in this category, revise that part and say what changed and why. Only then write code.

For a new surface where several directions are genuinely open, show the user the plan (or two or three materially different ones) before building. A precise request, or an addition to an established surface, needs only a one-line confirmation.

### 4. Build

Read [FLOOR.md](FLOOR.md) immediately before the first UI edit — including small refinements — and build to it without announcing it.

- **The first viewport is a thesis, not a header.** Open with the most characteristic thing in the subject's world, at the scale it has in life: a headline, an image, a live demo, an interaction. The big-number-small-label-plus-accent hero is the default; use it only if it's truly the best option.
- **Typography carries the personality.** Use type as an active part of the design, not a neutral delivery vehicle. Line lengths under ~75 characters; serif body gets a little more line-height than sans.
- **Visual structure is information.** Borders, numbering, dividers, and labels encode something about the content. `01 / 02 / 03` only for a real sequence.
- **Motion, once.** One orchestrated moment — a page-load sequence or a reveal — beats fade-and-slide on every section. Motion that answers a person's action (opening, expanding, confirming) is welcome when it shows what changed.
- **Prove, don't claim.** Show the product doing its job with specifics a competitor couldn't paste in. Illustrative data is fine at full fidelity and labelled as such; claims are never invented.
- **Author the content.** Great surfaces live on carefully made names, entries, covers, and copy. Gradients, glass, and generic icon tiles where real content belongs are the gap wearing chrome. Use real, verified imagery when the brief implies it.
- **Spend boldness in one place.** One memorable element; everything around it quiet and disciplined. Before finishing, remove one accessory.
- **Watch CSS specificity.** Two class rules of equal specificity, like `.section` and `.cta`, fight over the padding and margin between sections; whichever comes later wins, so set section spacing in one place.

Preserve semantics, accessibility, performance, responsiveness, the project's conventions, and working behaviour.

### 5. Check the render, in bounded passes

If you can take screenshots, inspect once in a batched round — desktop and mobile together, plus the user's actual viewport if known — after settling entrance motion so hidden elements don't read as missing. Fix everything that round shows in one batch, confirm with at most one more round, then stop. Open-ended self-QA costs the user money and does worse than a fresh review. If something material remains, say so and offer a critique pass.

---

## Refine

Refinement keeps the incumbent world. Read [FLOOR.md](FLOOR.md) before editing, change only what the request names, and check the render as in [step 5](#5-check-the-render-in-bounded-passes).

- **Bolder** — find where the design is hedging: a timid scale step, an accent used as a sticker, a safe layout. Commit one of them — larger type contrast, colour that owns a region, a composition the category wouldn't attempt. Don't add decoration.
- **Quieter** — remove before restyling: fewer colours at full saturation, fewer effects, one motion moment instead of many, more space. Keep the one memorable move.
- **Simpler** — strip to the task: cut options past four per decision, merge redundant sections, drop chrome that encodes nothing.
- **Polish** — walk the whole path at every breakpoint: alignment and spacing rhythm, type scale, every interactive state, browser surfaces, copy, and the [FLOOR.md](FLOOR.md) checks. Fix small things; flag anything that needs a design decision.
- **Copy** — apply [Writing](#writing) to labels, buttons, errors, and empty states.

---

## Writing

Words are design content, not decoration. Before writing any, ask what the screen needs to say and how to say it most plainly.

- Write from the user's side: they manage notifications, not webhook config. Describe what something does; don't sell it. Specific beats clever.
- Active voice. A button says what happens — "Save changes", not "Submit" — and the action keeps its name through the flow: "Publish" produces a toast saying "Published".
- Errors say what went wrong and how to fix it, in the interface's voice. They don't apologise and are never vague. An empty screen is an invitation to act.
- Sentence case, plain verbs, no filler. Each piece of text does one job.

Avoid the commonest typographic tells: accenting one word of a headline in italic, bold, or colour; all caps for labels; labels above content that don't need to be there.
