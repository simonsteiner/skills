# Critique and audit

Review a frontend without changing it. A **critique** judges the design — specificity, hierarchy, usability. An **audit** checks the implementation — accessibility, performance, theming, responsiveness. "Review this UI" gets both; a request naming one gets that one. Report, then let the user pick what to fix.

## Contents

- [Set up](#set-up)
- [Critique](#critique)
- [Audit](#audit)
- [Report](#report)

## Set up

1. **Resolve the target** to concrete source files, and a URL if it runs. Prefer the source path; ports drift.
2. **Pick the mode** (Persuade, Operate, Read, Experience — see SKILL.md). The bar differs: a dashboard isn't marked down for a quiet hero, a landing page isn't marked down for lacking keyboard shortcuts.
3. **Look at it.** If a browser or screenshot tool is available, capture desktop and mobile once, after entrance motion settles. Judge the render, not only the code.
4. **Judge before you measure.** Form the critique's specificity verdict before running mechanical checks, so a list of detected tells doesn't anchor the judgment. With a sub-agent tool, run the audit in a separate sub-agent and merge afterwards.

## Critique

- **Specificity verdict — start here.** Is the composition, interaction, and visual language grounded in this product, or could an unrelated product in the category use it unchanged? Name the defaults it landed on (SKILL.md's five calibration looks, the scaffolds in FLOOR.md) and the missed chances for character.
- **Heuristics.** Score Nielsen's ten usability heuristics 0–4 each (4 is genuinely excellent; most real interfaces total 20–32 of 40). On Persuade and Experience surfaces, efficiency and help may be `n/a` with a one-line reason — then total against the applicable maximum, never `/40` over a partial set.
- **Cognitive load.** Check eight things: a single focus for the primary task; information chunked in groups of four or fewer; related items grouped; an obvious hierarchy; one decision at a time; four or fewer visible options per decision; nothing to remember from a previous screen; complexity disclosed progressively. 0–1 failures is low load, 2–3 moderate, 4+ high.
- **Personas.** Walk the primary action as the two or three that fit, and name exactly which elements fail them:
  - *Power user* — skips onboarding, wants keyboard shortcuts, batch actions, and no needless confirmations.
  - *First-timer* — reads literally; needs labelled icons, no jargon, a clear next step, and confirmation that things worked.
  - *Assistive-tech user* — keyboard and screen reader; needs heading structure, labels, visible focus, and nothing conveyed by colour or hover alone.
  - *On the move* — small screen, one thumb, flaky network; needs reachable targets, short forms, and graceful loading.
  - *Sceptical evaluator* — deciding whether to trust this; needs real proof, honest claims, and visible pricing or next steps.
- **Emotional journey.** Where are the high-stakes moments, and are they reassured? Does the end land (peak–end rule)?

## Audit

Score each dimension 0–4 (0 broken, 2 partial, 4 excellent):

1. **Accessibility** — contrast (4.5:1 body, 3:1 large); keyboard reachability, focus visibility, and tab order; semantic HTML and heading hierarchy; labels and ARIA on interactive elements; alt text; form labels and error messages; `prefers-reduced-motion` handled with an intentional alternative.
2. **Performance** — layout reads and writes in loops; animating layout properties or unbounded blur and shadow; unoptimised or eagerly loaded images; `will-change` left on at rest; heavy or unused imports; needless re-renders. For loading and Core Web Vitals depth, call the Skill tool with "web-perf" if it's installed.
3. **Theming** — hard-coded colours outside the tokens; broken or missing dark mode; tokens used inconsistently; values that don't update on theme switch.
4. **Responsive** — fixed widths, horizontal scroll, touch targets under 44×44px, gestures that fail under touch or swallow page scroll, layouts that break when text size increases.
5. **Integrity** — the FLOOR.md checks and refusals, verified in context: repeated shortcuts, design-system drift, placeholder or decorative content, structure interchangeable with an unrelated product. Call out what's a false positive.

## Report

Write the whole report, then ask what to address — the question comes last. In order:

1. **Verdict** — specificity first (critique) and integrity (audit), each pass/fail with evidence.
2. **Scores** — the heuristics table and/or the audit table, with the key finding per row and the total.
3. **What's working** — two or three specific things worth keeping, and why.
4. **Priority issues** — three to five, ordered, each tagged:
   - **P0** blocks the task — fix now.
   - **P1** causes real difficulty or a WCAG AA failure — fix before release.
   - **P2** annoying, with a workaround — next pass.
   - **P3** polish, no real user impact.

   For each: what, where (file and line), why it matters, and the concrete fix. Unsure between two levels? If a user would contact support about it, it's at least P1. Don't drown the list in P3s.
5. **Persona red flags** and **minor observations**, briefly.
6. **The question** — which issues to fix, in what order. Fixes then follow SKILL.md's Refine section.
