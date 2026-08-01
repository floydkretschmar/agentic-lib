---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
---

# Domain modeling

Build and sharpen the domain model of the project while you design. Challenge terms, invent edge-case scenarios, and write down the glossary and decisions as soon as you settle them. Use this skill only when you change the model, because any skill can read `docs/PROJECT.md` for vocabulary.

## File structure

Most repos have the following context structure:

```
/
├── docs/
│   ├── EXECUTION.md
│   ├── ISSUE-TRACKER.md
│   ├── PROJECT.md
│   ├── TESTING.md
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
│   └── languages/
│       ├── JAVASCRIPT.md
│       ├── JAVA.md
│       └── ...
└── src/
```

General project context is in `docs/PROJECT.md`.
Testing principles are in `docs/TESTING.md`.
Execution principles for changes to production code are in `docs/EXECUTION.md`.
Rules for each programming language are in `docs/languages/*.md`.

Create a file only when you have something to write in it. Create `PROJECT.md` when you resolve the first term, and `docs/adr/` when you need the first ADR.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `PROJECT.md`, say so immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You say 'account'. Do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When you discuss domain relationships, invent edge-case scenarios that force the user to state the boundaries between concepts precisely.

### Cross-reference with code

When the user states how something works, read the code. If the code contradicts the user, say so: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update PROJECT.md inline

Write each term into `PROJECT.md` as soon as you resolve it, not in a batch later. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`PROJECT.md` is a glossary and nothing else. Keep specs, scratch notes, and implementation details out of it.

### Offer ADRs sparingly

Offer to create an ADR only when all three conditions are true:

1. The decision is costly to reverse.
2. Without context, a future reader will wonder "why did they do it this way?"
3. You picked it from real alternatives for specific reasons.

Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
