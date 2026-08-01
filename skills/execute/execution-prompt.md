# Execution prompt template

<execution-prompt-template>
You execute ONE phase from an implementation scheme. Follow the instructions in the scheme file for your task exactly.
Do no manual testing. Run only the automated baseline verification.

## Your task
<paste the specific review change from todo.md>

## Context
spec file: <path to spec>
scheme file: <path to scheme>
Working directory: <current directory>
context: `docs/*.md`, `docs/languages/*.md`, `docs/adr/*.md`

## TDD process (MANDATORY)
You MUST follow Test-Driven Development as the tdd skill describes:

1. Write a test for the current slice
2. Run the test and make sure that it fails (RED)
3. Implement a small feature slice. Run the same test again to make sure that the slice is correct (GREEN)
4. After all tests pass, identify all refactor candidates and refactor them aggressively (REFACTOR)
5. Run the baseline verification to make sure that the refactor is correct

## Additional instructions
- Read `docs/*.md`, `docs/languages/*.md`, `docs/adr/*.md` for project conventions and learned rules
- After the commit, mark the review change complete in tasks/todo.md
- Keep a `TDD Slice Log` in tasks/todo.md with RED and GREEN proof for each behavior

## Stop-the-line rule
If ANYTHING unexpected happens:
- STOP immediately
- DO NOT try to fix it without understanding it
- Report what happened, the error output, and the recommended action

Also STOP immediately if:
- You wrote implementation before demonstrating RED
- You batch-created multiple tests before implementation (horizontal slicing)
- You changed database or domain constraints without adding or updating integration tests

## Output
End your response with exactly one of:
- "STATUS: DONE" if you completed the review change with TDD (the test exists and passes) and know of NO defects or regressions
- "STATUS: BLOCKED: <reason>" if you cannot proceed and need help
- "STATUS: ERROR: <description>" if something failed

</execution-prompt-template>
