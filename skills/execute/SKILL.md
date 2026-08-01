---
name: execute
description: Execute an implementation scheme with a subagent for each phase until completion. Use it after a scheme exists and the user is ready to start implementation.
---

# Execute skill
Execute an implementation scheme with a fresh subagent for each phase until all phases are complete.

## Phases
Follow these steps:

1. Gather context
2. Loop until ALL phases in the spec are done (review and manual testing PASSED):
   1. Execute current phase
   2. Current phase review
   3. Manual testing of current phase
3. Final review
4. Full manual regression test and a check for flaky tests

## The execute philosophy
A fresh subagent for each phase prevents context pollution. Each iteration:
1. Starts with a fresh context that holds nothing from previous phases
2. Works on ONE phase only
3. Reports back a status: DONE, BLOCKED, or ERROR

## Quality gates

Each subagent must:
- Touch only ONE phase
- Follow TDD (test first) with the /tdd skill
- Update tasks/todo.md

You cannot mark a phase complete until:
- All tasks of the phase are checked off
- The full test suite passes
- Lint is clean
- The build succeeds
- The spec compliance review passes
- The code quality review passes

### Step 1: Gather context

Start from the conversation context. Then:

1. Read the spec file and the scheme file
2. Read tasks/todo.md with the phase checklist from the scheme
3. Read `docs/*.md`, `docs/languages/*.md` and `docs/adr/*.md` for project conventions
4. Run all tests and the build as a baseline. If a test or the build fails, STOP and report

### Step 2: Implementation loop
To add an addendum, add the issues to tasks/todo.md after the current phase. Then continue the implementation loop.

### Step 2.I: Execute current phase

For EACH incomplete phase, give a fresh subagent the EXACT prompt in [execution-prompt.md](execution-prompt.md) and replace ONLY its placeholders. The subagent executes the phase with TDD.

Choose the subagent by task:
- frontend-agent: user-facing tasks that are heavy on UI and UX
- backend-agent: backend or server tasks that mainly involve system-to-system interaction

After each subagent completes:
- If it reports `STATUS: DONE`, proceed to Step 2.II.
- If it reports `STATUS: BLOCKED`, report the blocker to the user and ask how to proceed.

### Step 2.II: Review current phase

When ONE phase is complete, invoke /review for a full review of that phase. FOLLOW THE EXACT INSTRUCTIONS IN THE REVIEW SKILL.

- If the review returns `REVIEW: PASSED`, proceed to Step 2.III.
- If the review returns `REVIEW: NEEDS_CHANGES`, decide whether the issues are a regression within the overall spec scope:
  - If they are a regression, add an addendum.
  - If they are outside the spec scope, proceed to the completion output.

### Step 2.III: Manual testing of current phase
After you mark a phase complete, have a new qa-agent test the phase manually as the scheme describes. The qa-agent ALWAYS uses the browser to make sure that the result is visually correct.

- If manual testing fails, add an addendum.
- If manual testing succeeds, commit all changes of the current phase with a descriptive commit message.

Then continue the implementation loop with the next phase, or with Step 3 when all phases are done.

### Step 3: Final review

Invoke /review for a final full review of THE ENTIRE BRANCH, not of the changes since the last PR or another checkpoint. FOLLOW THE EXACT INSTRUCTIONS IN THE REVIEW SKILL.

- If the review returns `REVIEW: PASSED`, proceed to Step 4.
- If the review returns `REVIEW: NEEDS_CHANGES`, report the findings to the user. Then handle them as in Step 2.II.

### Step 4: Full manual regression test and a check for flaky tests

Have a new qa-agent manually test the entire application scope and prove that the change introduced no visual or feature regressions.

In parallel, have a new subagent check the test suites for flaky tests. A flaky test passes and fails on the same code. The subagent:
1. Runs the integration and end-to-end tiers at least 10 times on the load of the CI runner: it limits the test process and the local Docker containers to the CPU count of the runner, and uses the worker count of the pipeline.
2. Runs each test that failed once again with `--repeat-each` (Playwright) or in a loop (Vitest), with and without the change of the branch, to find out how often it fails and whether the branch caused it.
3. Reports each flaky test with its file and line, the failure message, how often it failed, and the conditions. 

Summarize the findings in `tasks/regression-review.md` with the template [summary-template.md](../review/summary-template.md). List each flaky test as a finding, and report the flaky tests to the user.

- If regression testing returns `REVIEW: PASSED`, report to the user that the feature is fully implemented. Include a summary of ALL review and regression findings and their fixes.
- If regression testing returns `REVIEW: NEEDS_CHANGES`, add an addendum.
