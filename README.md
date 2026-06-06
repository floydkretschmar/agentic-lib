# Agentic Lib

Agentic Lib is a language-agnostic starting point for agentic software workflows. It provides reusable Codex skill instructions for chaining discovery, planning, implementation, and review while keeping context small through progressive disclosure.

The core workflow is:

```text
plan-feature -> scheme -> execute -> review -> finish
```

Use this repository as a lightweight operating system for AI-assisted delivery: establish the problem, turn it into testable slices, execute those slices with fresh context, review the result, and finish with final verification before calling it done.

## Why This Exists

Agentic coding tends to fail when too much context is loaded too early, when planning and execution blur together, or when verification becomes optional. This project keeps those concerns separate:

- `plan-feature` captures the user problem and writes a spec.
- `scheme` turns the spec into tracer-bullet implementation phases.
- `execute` runs each phase with focused subagents and verification.
- `review` checks scope, quality, tests, security, and refactoring.
- `finish` is the mandatory final gate for verification, documentation, archival, and PR preparation.

The repository is intentionally small. The value is in the workflow contracts, not a language-specific framework.

## Progressive Disclosure

This project is built around [progressive disclosure](https://docs.claude-mem.ai/progressive-disclosure): show what exists first, then fetch details only when they are relevant.

In practice, that means:

- Start with indexes, summaries, and skill descriptions.
- Read full specs, schemes, prompts, or source files only when the task calls for them.
- Keep each phase scoped so agents can work with fresh, focused context.
- Make verification evidence explicit instead of relying on memory or intent.

The goal is to preserve attention for the current task. Context is treated as a budget, not a dumping ground.

## Repository Layout

```text
.codex/
  agents/              Agent profiles used by the workflow
  hooks/               Local policy hooks and tests
  skills/              Reusable skill instructions
docs/
  PROJECT.md           Project architecture notes
  TESTING.md           Testing principles
  EXECUTION.md         Execution principles
  languages/           Language-specific conventions
run.sh                 Unified test, format, and build entry point
```

## Language Instructions

Language-specific conventions live in `docs/languages/`, such as `docs/languages/JAVASCRIPT.md`. Add a new small Markdown file there when a project needs rules for another language, and keep it focused on conventions that agents must follow while changing that language.

## Skill Chain

### 1. Plan Feature

`plan-feature` starts from a user problem, explores the codebase, interviews for missing decisions, and writes a spec in `docs/specs/`.

Use it when the problem is still being shaped.

### 2. Scheme

`scheme` converts an approved spec into vertical slices. Each slice should be independently valuable, testable, and wired through the real system.

Use it when the feature is understood and needs an implementation plan.

### 3. Execute

`execute` implements the scheme one phase at a time. It uses fresh subagents to avoid context pollution and requires verification before completion.

Use it when the scheme is approved and implementation should begin.

### 4. Review

`review` runs independent checks for spec compliance and implementation quality, then writes a review artifact.

Use it after implementation work and before declaring the branch complete.

### 5. Finish

`finish` is a fundamental part of the skill chain. It performs final verification, captures documentation and archival updates, and prepares the branch for PR handoff.

Use it after review passes. A branch is not complete until `finish` has run successfully.

## Supporting Skills

- `tdd`: Red-green-refactor workflow for behavior-first implementation.
- `rearchitect`: Finds opportunities to deepen shallow modules and improve testability.
- `frontend-design`: Builds polished frontend interfaces when UI work is in scope.

## Verification

All work should be validated through the repository entry point:

```sh
./run.sh test
./run.sh format
./run.sh build
```

These commands are the shared contract for proving that a change is ready. Individual projects can fill in the language-specific implementation behind each command.

## Design Principles

- Less is better than more.
- Remove before adding.
- Keep changes small and boring.
- Prefer behavior tests over implementation-detail tests.
- Use fresh context for distinct phases of work.
- Read progressively: index first, details on demand.
- Do not mark work complete without verification evidence.

## Getting Started

1. Read `docs/PROJECT.md` for the current project shape.
2. Read only the skill needed for the current task from `.codex/skills/*/SKILL.md`.
3. For new feature work, start with `plan-feature`.
4. For an approved spec, continue with `scheme`.
5. For an approved scheme, run `execute`.
6. After implementation, run `review`.
7. After review passes, run `finish` for final verification and handoff preparation.

This keeps the workflow language-agnostic while still giving agents enough structure to work reliably.
