---
name: execute
description: Use when an existing feature scheme and spec is supposed to be implemented.
---

# Execute skill
Execute an implementation scheme until all phases are complete.

1. Gather context
2. Loop until ALL phases in the spec are done (review and manual testing PASSED):
   1. Execute current phase
   2. Current phase review
   3. Manual testing of current phase
3. Final review
4. Full manual regression test and a check for flaky tests

## Quality gates
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
- The manual QA passes

### Step 1: Gather context
Start from the conversation context. Then:

1. Read the spec file and the scheme file
2. Read tasks/todo.md with the phase checklist from the scheme
3. Read `docs/*.md`, `docs/languages/*.md` and `docs/adr/*.md` for project conventions
4. Run all tests and the build as a baseline. If a test or the build fails, STOP and report

### Step 2: Implementation loop
To add an addendum, add the issues to tasks/todo.md after the current phase. Then continue the implementation loop.

### Step 2.I: Execute current phase
Implement the current phase using test driven development (read the `tdd` skill before writing any code):

1. List the required behaviors, including unhappy paths.
2. Write one test for one behavior through the public interface. Assert on what the caller gets back. (RED)
3. Run it. It must fail because the behavior is missing, not because of a typo.
4. Write the least code that makes it pass. (GREEN)
5. Run the suite until green.
6. Find and refactor all refactor candidates, then run the tests again and make sure the full baseline is green. You change structure only. (REFACTOR)
7. Repeat until all required behaviors are implemented.

Execute the task completely according to the spec and scheme. If you encounter any blocking issue that you cannot resolve by yourself, stop and ask the user for feedback.

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

In parallel, have a new subagent check the test suites for flaky tests. The subagent must:

1. Run the integration and end-to-end tiers at least 10 times on the load of the CI runner
2. Runs each test that failed once again with `--repeat-each` (Playwright) or in a loop (Vitest), with and without the change of the branch, to find out how often it fails and whether the branch caused it.
3. Reports each flaky test with its file and line, the failure message, how often it failed, and the conditions. 

Summarize the findings of both subagents in `tasks/qa-review.md` with the template [summary-template.md](../review/summary-template.md). 

- If regression testing returns `REVIEW: PASSED`, report to the user that the feature is fully implemented.
- If regression testing returns `REVIEW: NEEDS_CHANGES`, add an addendum.
