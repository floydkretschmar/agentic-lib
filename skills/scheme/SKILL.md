---
name: scheme
description: Use when the user wants to break down a spec, create an implementation plan or plan phases from a spec.
---

# Scheme skill

Turn a spec into a multi-phase implementation plan with tracer-bullet vertical slices and write it to a Markdown file in `./docs/schemes/`.

## Process

### Step 1: Gather context

Start from the conversation context. Then:

1. Read the relevant spec file
2. Read `docs/adr/*.md` for project conventions

### Step 2: Explore the codebase (optional)

If you have not explored the codebase yet, explore it to understand the current state of the code. Phase titles and descriptions must use the terms of the project's domain glossary and respect the ADRs for the area that you change.

Look for prefactoring (refactoring before the change) that makes the implementation easier.

### Step 3: Identify durable architectural decisions

Before you slice, identify the high-level decisions that are unlikely to change during implementation:

- Route structures / URL patterns
- Database schema shape
- Key data models
- Authentication / authorization approach
- Third-party service boundaries

Put these decisions in the plan header, so that every phase can reference them.

### Step 4: Draft task breakdown as vertical slices

Breakdown down the spec into a set of tasks. Each task has to be a vertical slice.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests), NOT a horizontal slice of one layer
- A reviewer can demo or test a completed slice on its own
- Each slice fits in a single fresh context window
- Any prefactoring must come first

</vertical-slice-rules>

Consider the following approaches when creating the vertical slices:
- Workflow steps: Break a long process into individual steps (for example, instead of "Checkout," use "Enter Shipping," "Enter Payment," "Confirm").
- Business rules: Separate stories by constraint, such as payment methods (credit card vs. PayPal) or user types (guest vs. registered).
- Happy vs. unhappy path: Create one story for the ideal scenario and separate stories for error handling or alternative paths.
- Data types/variations: Start with a simple version of data input, then add complex data types in later stories.
- Extract a spike: Build the riskiest, most uncertain part first.

### Step 5: Quiz the user

Present the proposed breakdown as a numbered list. For each phase, show:

- **Title**: short descriptive name
- **Blocked by**: which other phase (if any) must complete first
- **What it delivers**: the end-to-end behavior that this phase makes work

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Does each phase depend only on the phases that really block it?
- Do you want to merge or split any phases?

Iterate until the user approves the breakdown.

### Step 6: Write the scheme file

Write the scheme file `docs/schemes/YYYY-MM-DD-<feature-name>.md` with the EXACT template from [scheme-template.md](scheme-template.md), and replace only its placeholders.

### Step 7: Scheme review

Spawn a fresh review-agent to review the scheme with the exact prompt in [reviewer-prompt.md](reviewer-prompt.md), and replace only its placeholders.

### Step 8: Incorporate feedback

If the reviewer returns `NEEDS_CHANGES`:
1. Use /grilling to clarify strategic questions
2. Update the scheme. Strongly prefer edits that shorten or modify existing specifications over adding new ones
3. Run a fresh reviewer
4. Repeat until the verdict is `PASSED`