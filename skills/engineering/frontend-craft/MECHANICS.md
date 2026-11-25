# Implementation lens

What a screenshot can't show. FLOOR.md checks the render; this lens reads the source: markup attributes, CSS properties, how state and data flow. Walk it over the files that implement the surface, cite every finding as `file:line`, and skip groups the surface doesn't have. Each group scores under the REVIEW.md audit dimension in its heading, unless a bullet names another. The brief, the mode, and the project's own conventions win where they conflict.

## Forms (Accessibility)

- Every control has a `<label>` (wrapping, or `for`) whose hit area includes the control; checkbox and radio rows have no dead zone between box and text.
- Fields carry a meaningful `name`, an `autocomplete` token, and the right `type` and `inputmode`. Spellcheck is off for emails, usernames, and codes.
- Paste is never blocked.
- Submit stays enabled until the request starts, then shows progress. Errors render inline beside their field, and focus moves to the first one.
- Leaving with unsaved changes asks first (`beforeunload` or a router guard).

## Agent-ready forms (Integrity)

Only when the user asks for agent access or the project already uses WebMCP: the API is in early preview, and browsers without it ignore the attributes, so no feature detection is needed. The browser builds each tool's input schema from the form's labels, `name`s, and types, so the Forms group above comes first.

- A self-contained form carries `toolname` (a specific verb and object, like `search-flights`) and a `tooldescription` that says what it does and when to use it, without listing the fields.
- `toolparamdescription` only explains a value the label doesn't, with an example; on a radio group it goes on the `<fieldset>`.
- `toolautosubmit` only on reads and reversible actions (search, filter, add to cart, save a draft). Never on deleting, paying, sending to other people, publishing, or account and permission changes: the person confirms those.
- The submit handler answers the agent: when `event.agentInvoked`, it passes validation errors and the result to `event.respondWith()` instead of only rendering them.
- Agent activity is visible through `:tool-form-active` and `:tool-submit-active`, styled with the surface's own tokens.
- Forms with dependent fields, custom controls, or several steps don't get the attributes; they need the imperative API or a framework's own hook. Call the Skill tool with "modern-web-guidance" if it's installed and retrieve its WebMCP guides before writing either.

## Focus and semantics (Accessibility)

- No `outline: none` without a `:focus-visible` replacement. Style `:focus-visible`, not `:focus`; `:focus-within` for compound controls.
- Sticky headers and overlays never cover the focused element: `scroll-padding-top` on the scroller, `scroll-margin-top` on anchor targets.
- A skip link to the main content precedes repeated navigation.
- Actions are `<button>`, navigation is `<a>`; never a click handler on a `<div>` or `<span>`. Icon-only buttons have an accessible name; decorative icons are `aria-hidden`. Async results (toasts, validation) reach a polite live region.

## Motion (Performance)

- Transitions list their properties; never `transition: all`.
- Animations can be interrupted: input mid-transition reverses from where it is, not after it finishes.
- SVG transforms go on a `<g>` with `transform-box: fill-box`, so `transform-origin` means what it says.
- Motion that autoplays for more than five seconds alongside other content has a pause, stop, or hide control (Accessibility).

## Media and long lists (Performance)

- `<img>` has `width` and `height` (or an aspect-ratio box), so loading doesn't shift the layout.
- Below the fold: `loading="lazy"`. The largest image above the fold: `fetchpriority="high"`, never lazy.
- Short loops are muted `playsinline` video with a still fallback, not animated GIFs. Meaningful media has captions or a transcript (Accessibility).
- Lists that can grow past a few hundred rows virtualise or use `content-visibility: auto`.

## Theming

- `color-scheme` on `<html>` matches the theme, so scrollbars and form controls follow it; `<meta name="theme-color">` matches the page background.
- Native `<select>` gets explicit background and text colours; Windows dark mode won't infer them.

## Touch and viewport (Responsive)

- The viewport meta never sets `user-scalable=no` or `maximum-scale=1`.
- Modals, drawers, and sheets set `overscroll-behavior: contain`, so scrolling them never scrolls the page.
- Full-bleed layouts pad with `env(safe-area-inset-*)`.
- Every drag, swipe, or pinch action has a tap and keyboard equivalent; text selection is off during a drag.
- `autofocus` only on desktop, for a single primary input.

## State, content, and locale (Integrity)

- State a person would share or come back to (filters, tabs, pagination, open panels) lives in the URL.
- Destructive actions are undoable or confirmed: prefer undo; never irreversible in one click.
- Text containers survive the shortest, typical, and longest real input: `min-width: 0` on flex children that truncate, wrapping or clamping for user content, and an empty state for empty strings and arrays.
- `…` not `...`; a non-breaking space inside `10 MB` and `⌘ K`.
- Dates, times, numbers, and currency go through `Intl.DateTimeFormat` and `Intl.NumberFormat`, never hand-built strings, and render the same on server and client.
- Language comes from `Accept-Language` or `navigator.languages`, not IP. Brand names, code, and identifiers carry `translate="no"`.
