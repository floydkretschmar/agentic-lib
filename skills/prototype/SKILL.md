---
name: prototype
description: Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
---

# Prototype

A prototype is throwaway code whose shape follows the question that it answers.

## Pick a branch

Use the prompt and the surrounding code to decide which of two questions the prototype answers. If the user is available, ask them.

- "Does this logic / state model feel right?": Build a backend prototype. 
- "What should this look like?": Build a frontend prototype. 

## Backend prototype
Build a tiny interactive terminal app that runs the state machine through cases that are hard to reason about on paper. Before you write code, describe the state model and the question in one paragraph.

Use the language and the tooling conventions of the host project, and add no new package manager or runtime for the prototype. Put the logic behind a small, pure interface that you can move into the real codebase later.

Build the smallest TUI that exposes the state and allows interaction with the underlying model.

- Do not add tests. A prototype that needs tests is no longer a prototype.
- Do not connect it to the real database. Use an in-memory store unless the question is about persistence.
- Do not generalize for "what if we wanted to support X later". The prototype answers one question.

## UI prototype
Generate several radically different UI variants on a single route, with a floating bottom bar that switches between them. The user flips through the variants in the browser, picks one or combines parts of several, and throws the rest away.

Build 3 variants by default and 5 at most, because more variants stop being radically different and become noise. Variants must differ in structure, such as layout, information hierarchy, or primary affordance, not only in color. If two drafts come out too similar, redo one with explicit guidance

A URL search param and a floating bottom bar allows switch between the different designs. 

Always use the `frontend-design` skill for UI prototyping.

- Do not make variants that differ only in color or copy.
- Do not share layout code between variants, because each variant must be free to throw out the layout.
- Do not connect variants to real mutations. If a variant must change data, point it at a stub. 
- Do not promote the prototype directly to production. 

## Rules that apply to both

1. Keep it throwaway from day one. Put the code next to the module or page that it is for. Name it so that a casual reader sees that it is a prototype. A throwaway UI route follows the existing routing convention of the project, not a new top-level structure.
2. Make it run with one command of the existing task runner of the project, such as `pnpm <name>`, `python <path>`, or `bun <path>`.
3. Keep state in memory. If the question is about persistence, use a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. Write no tests, no abstractions, and no error handling beyond what the prototype needs to run.
5. After every action (logic) or variant switch (UI), print or render the full relevant state.
6. When you are done, fold each validated decision into the real code, so that main keeps only the validated decisions. Commit the prototype itself to a throwaway branch as a primary source. Leave a context pointer to that branch on the implementation issue. Write the question and its verdict in the issue or a commit.
