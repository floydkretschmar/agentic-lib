---
name: plan
description: Use when the user wants to do any work in this project or when the user wants to build anything.
---

# Building workflow

### Step 1: Gain surface level understanding

Start from the question "What is the user trying to do?". Are they trying to fix a bug? Do they want to extend an existing feature? Are they trying to refactor existing code to make it more maintainable? Ask the most important questions that you need to understand their intent.

### Step 2: Explore the codebase

Explore the repository using codebase-researcher-agents to make sure that the assertions in the conversation are correct, and to understand the current state of the codebase. Check existing documentation such as ADRs or other project documentation.

### Step 3: Interview the user for deeper

If the user wants to do anything bigger than a small bugfix or layout adjustment use the `interview` skill to get a deeper understanding.

### Step 4: Explore the web

If the user refers to external information that you do not know, such as products, web pages, or design patterns, use web-researcher-agents to verify relevant information. Never guess from your internal memory when concrete apis, contracts and verifiable information is concerned.

### Step 5: Create a spec
Have at least one architect-agents produce a complete design approach for implementing the requested feature. If the user plans a big change, have at least two architect-agents create radically different design approaches. Scale the number of agents and approaches with the complexity of the feature. Each subagent must sketch the modules it wants to create or modify and the public interfaces where the feature will be tested. They should prefer existing public interfaces to new ones, and use as few public interfaces as possible, ideally one.

Critically evaluate the resulting designs based on your understanding. If multiple designs have been proposed, compare all all of them and synthesize one approach from the best aspects of each. Ask the user if these modules and this approach match their expectations.

When you fully understand the problem and the solution, write the spec file `docs/specs/YYYY-MM-DD-<feature-name>.md` with the template [spec-template.md](spec-template.md).

### Step 6: Identify durable architectural decisions

Identify the high-level decisions that are unlikely to change during implementation according to the architectural approach you have decided on:

- Route structures / URL patterns
- Database schema shape
- Key data models
- Authentication / authorization approach
- Third-party service boundaries

Put these decisions in the plan header, so that every phase can reference them.

### Step 7: Draft the implementation plan

Breakdown down the spec into a set of tasks. Each task has to be a vertical slice.

**Important:** If the user wants a small change, having a SINGLE task is not just accepted, but desired. Do not break work down just for the sake of breaking it down.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests), NOT a horizontal slice of one layer
- A reviewer can demo or test a completed slice on its own
- Any prefactoring must come first

</vertical-slice-rules>

Consider the following breakdown approaches when creating the vertical slices:

- Workflow steps: Break a long process into individual steps (for example, instead of "Checkout," use "Enter Shipping," "Enter Payment," "Confirm").
- Business rules: Separate stories by constraint, such as payment methods (credit card vs. PayPal) or user types (guest vs. registered).
- Happy vs. unhappy path: Create one story for the ideal scenario and separate stories for error handling or alternative paths.
- Data types/variations: Start with a simple version of data input, then add complex data types in later stories.
- Extract a spike: Build the riskiest, most uncertain part first.

### Step 8: Quiz the user

Present the proposed breakdown as a numbered list. For each phase, show:

- **Title**: short descriptive name
- **Blocked by**: which other phase (if any) must complete first
- **What it delivers**: the end-to-end behavior that this phase makes work

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Do you want to merge or split any phases?

Iterate until the user approves the breakdown.

### Step 9: Write the implementation plan file

Write the implementation plan file `docs/implementation-plans/YYYY-MM-DD-<feature-name>.md` with the EXACT template from [implementation-plan-template.md](implementation-plan-template.md), and replace only its placeholders.

### Step 10: Implementation plan review

Spawn a fresh review-agent to review both the spec and the implementation plan with the exact prompt in [reviewer-prompt.md](reviewer-prompt.md), and replace only its placeholders.

### Step 11: Incorporate feedback

If the reviewer returns `NEEDS_CHANGES`:
1. Use the `interview` to clarify strategic questions that the reviewer might have brought up
2. Update the implementation plan. Strongly prefer edits that shorten or modify existing specifications over adding new ones
3. Run a fresh reviewer
4. Repeat until the verdict is `PASSED`