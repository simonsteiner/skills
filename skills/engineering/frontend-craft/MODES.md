# Modes

The mode names what the visitor's success looks like on this surface, and decides how far the visual world may reach into it. Choose it per surface, not per product.

## Contents

- [Persuade and Experience](#persuade-and-experience)
- [Operate](#operate)
- [Read](#read)

## Persuade and Experience

The design is what the visitor judges, so the world may own and structure the page.

- **Persuade:** the opening makes the offer intelligible and desirable, exposes a clear action, and shows something only this product can prove. The action is the one the category's visitors came for, in its working form — an airline's route-and-dates search, a clinic's open slots, a store's add to cart — not a decorative link to it elsewhere.
- **Experience:** the work itself leads from the first viewport; the interface recedes.
- **The world carries the page; it isn't a picture of it.** A facade, a shutter, or a book can be what the page is built on. A viewport painted whole as a poster with no working parts is a picture, not a website. Wherever the world puts navigation, copy, or an action, it must still read as a link, as text, as plainly clickable.
- **Commit the material.** The world's material is the ground and the major surfaces, and its type sets the headlines. A world reduced to an accent on a neutral template is the category default with a sticker on it. Equally, a split hero (copy one side, product the other, badge row under it) or a centred headline over a row of cards is the template whatever colour it's painted.
- **When the world is an object, it keeps its real form:** one object, one scale, one point of view. A book opens to two pages on one gutter, never a third panel.
- Typefaces want a point of view. These are training-data defaults that mean you stopped looking: Fraunces, Playfair Display, Cormorant, Lora, Crimson, Newsreader, Syne, Space Grotesk, Space Mono, IBM Plex, Inter as display, DM Sans, DM Serif, Outfit, Plus Jakarta Sans, Instrument Sans. Use one only for a reason no other face could satisfy.
- Bolder colour strategies (Committed, Drenched) are permitted; take them when the brief allows. Colour commits at page scale — fields that own regions, not accents scattered over a neutral ground.

## Operate

The visitor came to get a job done. The page is first a working product of its category; the world serves it.

- **The world lends four things only:** type, palette, density, and one signature move. Never the layout, the navigation model, or the controls. Name the signature move concretely — service health drawn as a transit map, a schedule set in a timetable's column rhythm.
- **No costumes.** A world taken from a tool the audience operates (terminal, scope, cockpit) comes back as type, palette, density, and a move — never a function-key bar, an instrument bezel, or ruled ledger paper standing in for a table. If an engineer couldn't build it from the platform's standard components, it's a picture of the tool.
- **Earned familiarity is the bar.** A category-fluent user should trust every control immediately. The failure mode is strangeness without purpose: over-decorated buttons, mismatched form controls, display fonts on labels, invented affordances.
- **Typography:** one well-tuned sans is often right. Fixed rem scale, not fluid; ratio 1.125–1.2 between steps. Prose still 65–75ch; tables can run wider.
- **Colour:** Restrained is the floor, but colour still does real jobs — a coloured rail or header, a tinted ground, state colours, data series, selection. A grey screen with one accent is the default without the polish, not restraint. The accent marks primary actions, current selection, and state only. A second neutral layer separates sidebars and toolbars from content.
- **Components:** every interactive one has default, hover, focus, active, disabled, loading, and error states. Skeletons for loading, not spinners in content. Empty states teach the interface. Same button shape, form vocabulary, and icon style everywhere — if "Save" looks different in two places, one is wrong.
- **Overlays escape their container.** A dropdown inside `overflow: hidden` gets clipped; use `<dialog>`, the popover API, `position: fixed`, or a portal. Exhaust inline and progressive options before a modal.
- **Motion:** 150–250 ms, conveying state change, feedback, loading, or reveal — nothing else. No orchestrated page-load sequence; users want the task, not the show.
- **Permissions:** system fonts, standard navigation (top bar + side nav, breadcrumbs, tabs, command palette), density, and consistency over surprise.
- **Real content:** the product's name, plausible data with units, real labels, and at least one state worth seeing — an alert, a degraded service, an empty filter result. A headline number that moves over time shows its recent history.
- **Self-check:** with the name covered, does it read as a product of its category, could the visitor do the task, and is it at least as clean as the category's best and more distinctive?

## Read

The visitor came to understand something. The page is first a document of its kind, framed by the world.

- **The world owns the frame and serves the column.** The frame is the masthead, the navigation rail, the ground, the title and section openers, and how code, tables, and callouts are set — there the palette, type, and signature move commit fully. The reading column stays calm: a reading face, real contrast, about 60–75 characters at ~16px, nothing performing behind the text.
- **Wayfinding stays standard.** The reader always knows where they are and where to go next: navigation and position, a title and opening that answer or frame the question, contents, section headings, next and previous. The world never replaces navigation with something a reader has to learn.
- **Borrow from publishing traditions:** reference books, type specimens, timetables, field guides, technical manuals, scholarly apparatus, a newspaper's wayfinding.
- **Standard forms for hard content.** Code, tables, notes, and figures sit in the forms readers know, set in the world's type and palette. Monospace is for code and parameters, never the running text or headings.
- **Self-check:** can a reader find and read the answer comfortably? Cover the name — could this be any other product's docs? If so, push the frame further into the world. If it reads as an artifact before a document, pull the world back out of the column.
