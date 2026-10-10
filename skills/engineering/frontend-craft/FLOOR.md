# Quality floor

Read this after the direction is settled and before any UI edit. Build to it without announcing the checklist. A pinned brief or the committed visual world overrides anything here; your own habit doesn't.

## Verify

Each is a check on the built result, not an intention. Run them together in the batched screenshot round; they share one render.

- **Contrast:** body and placeholder text ≥ 4.5:1, large text ≥ 3:1. On coloured surfaces, tint secondary text from that hue or the foreground — never grey.
- **Depth:** shadows have an offset and a soft blur. Declare elevation once — border *or* shadow; a 1px border under a wide soft shadow is a ghost card. Card radii 12–16px; pills are for small controls.
- **Spacing:** tight groups, generous separation, more space above a heading than below it. Read the computed values.
- **Type:** body measure 65–75ch, display at most 6rem, tracking no tighter than -0.04em (-0.02 to -0.03em usually reads better), balanced headings, obvious scale and weight steps. Run the real copy at every breakpoint and fix what overflows.
- **Motion:** one authored moment, exponential ease-out, from an already-visible default so content never depends on an animation finishing. Blur, backdrop-filter, clip-path, mask, and shadow are in the palette when they stay smooth. `prefers-reduced-motion` gets an intentional alternative that keeps state changes legible, not a global kill.
- **States:** hover, focus, active, disabled, loading, error, empty — plus real content, working controls, visible keyboard focus, and touch targets of at least 44×44px.
- **Browser surfaces:** text selection, the caret, scrollbars, focus rings, underline offset, and tabular numerals ship with browser defaults that belong to no design. Theme them from the palette. It's the cheapest sign a page was built rather than assembled.
- **Responsive:** down to mobile with no horizontal scroll, and at common desktop widths (1280–1600), not only the one you built at.
- **Copy:** the product's own language. Controls name their action; errors name the problem and the recovery.
- **Coverage:** every requirement in the brief is present and findable within seconds.

## Refuse

These are the category's defaults. The brief's own words can earn any of them back; reaching for one when the axis is free means rewriting the element, not softening it.

Page scaffolds:

- Same-size cards of icon + heading + text as the page structure. Nested cards are always wrong.
- The hero-metric template: big number, small label, supporting stats, accent.
- An eyebrow or kicker above a heading. Let the heading carry its own weight.
- Section numbers (`01 / 02 / 03`) unless the sequence is information the reader needs.
- A modal for a task that needs neither interruption nor protected focus.

Surface habits:

- Gradient text. Emphasis comes from weight or size.
- Glass and blur as decoration rather than as a specific effect.
- A coloured `border-left` or `border-right` thicker than 1px on cards, list items, callouts, or alerts.
- Hard offset shadows (`box-shadow: 4px 4px 0`) outside a world that is actually neobrutalist.
- Sparklines, progress rings, and soft rounded rectangles standing in for content.
- Monospace as a costume for "technical" rather than for code, data, or measurement.
- A system display face (Impact, Arial Black, the platform sans) as the display voice of a page with its own identity. Source and self-host a face that fits.
- Emoji or Unicode glyphs standing in for icons. Icons come from one real library or authored SVG, in one stroke and weight.
- Sketch-style SVG illustration, doodles, and `feTurbulence` grain. Real illustration or none — crisp vector geometry, diagrams, and animated linework are fine.
- Striped or gridded backgrounds with no canvas, map, or blueprint in the subject to justify them. Backgrounds are surfaces, textured only from the subject's world.
- Neutrals by reflex — pure `#000` / `#fff`, flat greys, or the stock near-black `#0B0B0B` / `#111`. Derive neutrals from the palette's hue.
- Bounce or elastic easing.

The floor holds the mechanics; it never picks the direction. With every check green, spend the surface on the committed world — and when torn between refined and committed, commit.
