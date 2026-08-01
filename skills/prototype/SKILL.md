---
name: prototype
description: Build a throwaway prototype to answer a design question. Use when the user wants to sanity-check whether a state model or logic feels right, or explore what a UI should look like.
---

# Prototype

A prototype is throwaway code whose shape follows the question that it answers.

## Pick a branch

Use the prompt and the surrounding code to decide which of two questions the prototype answers. If the user is available, ask them.

- "Does this logic / state model feel right?" Use [LOGIC.md](LOGIC.md). Build a tiny interactive terminal app that runs the state machine through cases that are hard to reason about on paper.
- "What should this look like?" Use [UI.md](UI.md). Generate several radically different UI variants on a single route. A URL search param and a floating bottom bar switch between them.

The two branches produce very different artifacts, so the wrong branch wastes the whole prototype. If the question is ambiguous and you cannot reach the user, let the surrounding code decide. A backend module means logic, and a page or component means UI. State the assumption at the top of the prototype.

## Rules that apply to both

1. Keep it throwaway from day one. Put the code next to the module or page that it is for. Name it so that a casual reader sees that it is a prototype. A throwaway UI route follows the existing routing convention of the project, not a new top-level structure.
2. Make it run with one command of the existing task runner of the project, such as `pnpm <name>`, `python <path>`, or `bun <path>`.
3. Keep state in memory. If the question is about persistence, use a scratch DB or a local file with a clear "PROTOTYPE — wipe me" name.
4. Write no tests, no abstractions, and no error handling beyond what the prototype needs to run.
5. After every action (logic) or variant switch (UI), print or render the full relevant state.
6. When you are done, fold each validated decision into the real code, so that main keeps only the validated decisions. Commit the prototype itself to a throwaway branch as a primary source. Leave a context pointer to that branch on the implementation issue. Write the question and its verdict in the issue or a commit.
