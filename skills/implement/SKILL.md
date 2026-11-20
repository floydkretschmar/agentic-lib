---
name: implement
description: Use it after an implementation plan exists and the user is ready to start implementation.
---

# Execute skill
Execute an implementation plan until all phases are complete. Follow these steps:

1. Gather context
2. Implement one phase at a time until ALL phases in the implementation plan are done
3. Final review
4. Full manual regression test

### Quality gates

- Touch only ONE phase
- Follow TDD (test first) with the /tdd skill

You cannot mark a phase complete until:
- All tasks of the phase are checked off
- The full test suite passes
- Lint is clean
- The build succeeds

### Step 1: Gather context

Start from the conversation context. Then:

1. Read the spec file and the implementation plan file
2. Read `docs/adr/*.md` for project conventions
3. Run all unit tests and the build as a baseline.

### Step 2: Implementation

Execute each incomplete phase with TDD using the `tdd` skill. Commit your changes after each phase using the commit title "Phase [N]: [One line change description]" and the body of the commit naming the most important changes in bullet points.

### Step 3: Implementation review gate

Invoke /review for a final full review and manual quality control gate of the entire branch, not only of the changes since the last PR or another checkpoint. FOLLOW THE EXACT INSTRUCTIONS IN THE REVIEW SKILL.

- If the review returns `**Verdict:** PASSED`, proceed to Step 4.
- If the review returns `**Verdict:** NEEDS_CHANGES`, decide whether the issues are a regression within the overall spec scope:
    - If they are a blocking finding, add them under `Review findings` in the implementation plan. 
    - If they are a code quality finding, judge if they qualify as a boy scout commit. If they do, add them under `Review findings` in the implementation plan.
    - If they are a finding that require a decision by the user, collect them until the repeated review cycle is passing and present them in bulk as described below.
    - Everything else is to be ignored.

Then go back to Step 2 and fix all the findings you have added under `Review findings`.

After the review has fully passed, walk me through the collected open decision step by step:
1. What is the exact issue that needs a decision?
2. Was it introduced in this change and what was the behavior previously?
3. What could be a mitigation?
4. What would that mitigation cost in code?

If the open decisions have lead to additional implementation work, the full step 3 review gate runs again.

### Step 4: Completion output

Report the finalization of all changes. Output a fitting PR title and description for the changes of the branch for the user to review.
