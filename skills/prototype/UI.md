# UI prototype

Generate several radically different UI variants on a single route, with a floating bottom bar that switches between them. The user flips through the variants in the browser, picks one or combines parts of several, and throws the rest away.

If the question is about logic or state, use [LOGIC.md](LOGIC.md) instead.

## When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."
- Any case where the user otherwise spends a day picking between three vague mockups in their head.

## Two sub-shapes, strongly prefer sub-shape A

A UI prototype is much easier to judge inside the app, with the real header, sidebar, data, and density. On an empty route of its own, every variant looks fine. Use sub-shape A whenever an existing page near the feature can host the variants, and sub-shape B only when none can.

### Sub-shape A: adjustment to an existing page (preferred)

Render the variants on the existing route, and select them with a `?variant=` URL search param. The data fetching, params, and auth of the route stay, and only the rendering changes.

This also applies to a new part of an existing page, such as a dashboard section, a card on the settings screen, or a step in an existing flow. Mount its variants inside the host page.

### Sub-shape B: a new page (last resort)

Use this only when no existing page can host the prototype. Examples are a new top-level section of the app, or a flow that fits in no existing page.

Create a throwaway route in the existing routing convention of the project, not in a new top-level structure. Name it so that it shows it is a prototype, for example with the word `prototype` in the path or filename. Use the same `?variant=` pattern.

## Process

### 1. State the question and pick N

Build 3 variants by default and 5 at most, because more variants stop being radically different and become noise.

Write the plan in one line, in a file next to the prototype or in a comment at the top of the file:

> "Three variants of the settings page, switchable via `?variant=`, on the existing `/settings` route."

### 2. Generate radically different variants

Each variant keeps to these constraints:

- The purpose of the page and the data it has access to.
- The component library or styling system of the project (for example TailwindCSS, shadcn, MUI, or plain CSS).
- A clear exported component name, for example `VariantA`, `VariantB`, `VariantC`.

Variants must differ in structure, such as layout, information hierarchy, or primary affordance, not only in color. If two drafts come out too similar, redo one with explicit guidance such as "do not use a card grid".

### 3. Wire them together

Create a single switcher component on the route:

```tsx
// pseudo-code — adapt to the project's framework
const variant = searchParams.get('variant') ?? 'A';
return (
  <>
    {variant === 'A' && <VariantA {...data} />}
    {variant === 'B' && <VariantB {...data} />}
    {variant === 'C' && <VariantC {...data} />}
    <PrototypeSwitcher variants={['A','B','C']} current={variant} />
  </>
);
```

For sub-shape A, keep the existing data fetching above the switcher, so that only the rendered subtree changes per variant.

For sub-shape B, the throwaway route under `/prototype/<name>` mounts the same switcher.

### 4. Build the floating switcher

The switcher is a small fixed-position bar at the bottom center of the screen with three parts:

- The left arrow cycles to the previous variant and wraps around.
- The variant label shows the current variant key and, if the variant exports a name, that name too, for example `B — Sidebar layout`.
- The right arrow cycles to the next variant and wraps around.

Behavior:

- An arrow click updates the URL search param through the router of the framework, such as `router.replace` on Next or `navigate` on React Router. A reload or a shared link then shows the same variant.
- The `←` and `→` keys also cycle, except when an `<input>`, `<textarea>`, or `[contenteditable]` element has focus.
- The bar looks different from the page, so that nobody takes it for part of the design. A high-contrast pill with a subtle shadow works.
- Production builds hide the bar. Gate it on `process.env.NODE_ENV !== 'production'` or an equivalent condition, so that a stray prototype merge cannot ship it to users.

Put the switcher in one shared component where the project keeps shared UI, so that both sub-shapes use the same bar.

### 5. Hand it over

Give the user the URL and the `?variant=` keys. Feedback such as "I want the header from B with the sidebar from C" names the design that they want.

### 6. Capture the answer and clean up

Write down which variant won and why. Put it in a commit message, an architecture decision record, an issue, or a `NOTES.md` next to the prototype. Use the `NOTES.md` if you work unattended and the user did not respond yet. Then:

- For sub-shape A, delete the losing variants and the switcher, and fold the winner into the existing page.
- For sub-shape B, promote the winning variant to a real route, and delete the throwaway route and the switcher.

## Anti-patterns

- Do not make variants that differ only in color or copy.
- Do not share layout code between variants, because each variant must be free to throw out the layout. A shared `<Header>` is fine, but a shared `<Layout>` is not.
- Do not connect variants to real mutations. If a variant must change data, point it at a stub. The question is how the page looks, not whether the backend works.
- Do not promote the prototype directly to production. The variant code has no tests and minimal error handling, so rewrite it when you fold it in.
