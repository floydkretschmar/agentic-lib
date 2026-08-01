---
name: review
description: Verify implementation quality with parallel subagents for a full review. Use it after implementation to make sure that the new state of the codebase meets the expected quality standards.
---

# Review skill

Run an independent code review with two fresh subagents.

## Purpose
Give every change set, even a small diff, a separate review gate.

## The review philosophy

Two parallel subagents cover these aspects of implementation quality:

1. **Spec compliance.** Does the code match the spec?
2. **Code quality.** Does it follow project conventions?
3. **Test coverage.** Do the tests cover the edge cases?
4. **Security.** Are there obvious vulnerabilities?
5. **Refactoring.** Does the change include the right amount of cleanup refactoring?

The spec compliance subagent covers aspect 1, and the code quality subagent covers aspects 2 to 5.

Summarize the findings in one consolidated report with actionable feedback. Automatically fix all blocking issues.

## The review process

### Step 1: Pin the fixed point

The fixed point is the ref that the user gave, for example a commit SHA, a branch name, a tag, `main`, or `HEAD~5`. If the user gave none, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD`. The three dots compare against the merge-base. Also note the list of commits with `git log <fixed-point>..HEAD --oneline`.

Before you continue, make sure that the fixed point resolves (`git rev-parse <fixed-point>`) and that the diff is not empty. A bad ref or an empty diff must fail here, not inside two parallel subagents.

### Step 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (for example `#123`, `Closes #45`, or GitLab `!67`). Fetch them with the workflow in `docs/ISSUE-TRACKER.md`.
2. A path the user passed as an argument.
3. A spec file under `docs/` or `specs/` that matches the branch name or the feature.
4. If you find nothing, ask the user where the spec is. If the user says that no spec exists, the spec compliance subagent skips its review and reports "no spec available".

### Step 3: Spawn two fresh review subagents in parallel

#### 3a. Spec/scope compliance review

Have business-agent review the implementation against the spec with the prompt in [spec-quality-prompt.md](spec-quality-prompt.md) WORD FOR WORD. Replace only the placeholders.

#### 3b. Code quality / risk review

Have review-agent review the code with the prompt in [code-quality-prompt.md](code-quality-prompt.md) WORD FOR WORD. Replace only the placeholders.

### Step 4: Consolidate and persist review artifact

Write one review summary to `tasks/review.md` with [summary-template.md](summary-template.md) and return it. The summary follows these rules:
- If either reviewer reports `NEEDS_CHANGES`, the final verdict is `NEEDS_CHANGES`
- Order the findings by severity first
- Include concrete file and line references for actionable issues
