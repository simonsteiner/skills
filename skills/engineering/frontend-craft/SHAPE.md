# Shape a direction

Decide what a feature or surface should be and how it should look, and stop at a confirmed brief. Shaping writes no project code (a throwaway mockup outside the repo is fine): Build picks the brief up once the user chooses a direction.

## 1. Ask, once

Read what's already true first, as SKILL.md says: the `DESIGN.md` if there is one, the tokens and components, and the screens the feature sits beside. Then ask the two or three questions whose answers most change the result, in one round, with the structured question tool when there is one:

- What is it for, and what must it let someone do or understand?
- Who reaches it, in what situation, and what does success look like for them?
- What real content and data does it carry, at its shortest, typical, and longest? Which states matter: first run, empty, loading, error, success, overflow?
- What must stay untouched, and what would make it feel wrong even if it looked polished?

Where the code or the brief already answers one, state the likely answer and invite correction instead of asking. Ask a second round only when the answers expose a material gap. Never ask for CSS values or offer canned aesthetic lanes. Coming from Build, skip what its steps 1 and 2 already settled, and draft the directions from that plan rather than beside it.

## 2. Name the rut

Pick the mode (SKILL.md and MODES.md). Name the version this category always ships for a feature like this, and its predictable opposite. Both are the rut: neither is drafted as a direction, and the first comes back only as the standard option in step 3.

## 3. Draft two or three directions

Directions differ in composition, interaction, or flow, never the same layout in other colours.

- **Inside an established surface**, its world is fixed: type, palette, components, and navigation stay. Directions differ in structure and behaviour, and none introduces a new identity.
- **For a new surface or a replacement**, directions may also differ in world. Derive each from something the audience knows by heart (its publications, places, rituals, graphic traditions), not from the tools it operates, and give each the token plan from Build step 2.

Each direction gets:

- **Thesis:** one sentence on what it bets on.
- **Wireframe:** ASCII, at the proportions it ships, with real content.
- **Flow and states:** how a person moves through it, and what empty, loading, and error look like.
- **Memorable move:** the one place it spends its boldness.
- **Honest risk:** what could go wrong, including that it's familiar when that's true.

Run the calibration review from Build step 3 (the five looks and the similar-prompt test) over each: a direction that would come out the same for an unrelated product in the category gets revised before it's shown.

Add one more option, last and plain: **the category standard, done well.** It's the user's door, not your recommendation, and the other directions are never weakened or inflated beside it. If the user takes it, ask for two or three products it should sit alongside and make their craft level the bar.

### HTML mockups, when the difference only shows rendered

The ASCII wireframe is the default, and enough when directions differ in layout or flow. When they differ in type, colour, density, or world, or the user asks to see them, and you can render HTML, add a mockup:

- **One self-contained file** holding every direction, including the standard option, with a small switcher to flip between them. Real content, and the project's own tokens and fonts when the surface exists.
- **Equal fidelity.** Each direction at the same finish, so none wins by being further along. Static, with just enough interaction to show the memorable move.
- **Outside the project.** It goes in the scratchpad or a preview, never the codebase; shaping still writes no project code.
- **One render check**, desktop and mobile, to confirm it shows what the directions claim; then present it. Feedback feeds the next round of directions, not polish on the mockup.

## 4. Recommend, then let the user choose

Lead with the direction you'd build and say why in one line, then show all of them in full (wireframes, and the mockup when there is one) so they can be compared side by side. The user may pick one, combine parts, or ask for another round. A new round drops every direction already shown; after two rounds without a pick, ask what quality is missing instead of drafting more.

## 5. Write the brief and stop

Write the smallest brief that lets Build start without inventing anything:

- **Job and audience**, with the mode.
- **Chosen direction:** thesis, wireframe, memorable move, the tokens when the world is new, and the mockup's path when there is one.
- **States and content ranges.**
- **Boundaries:** what stays untouched, and the anti-goals.
- **Open decisions** a builder must not settle alone, and binding constraints.

Three to five bullets for a settled feature; the full list only for a new surface or a multi-screen flow. Then stop. When the user asks to build it, follow Build from step 4 with the brief as the confirmed plan.
