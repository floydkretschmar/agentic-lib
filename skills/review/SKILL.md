---
name: review
description: Use it after implementation to make sure that the new state of the codebase meets the expected quality standards.
---

## Review skill
Run an independent code review and manual quality control gate.

### Step 1: Pin the fixed point

The fixed point is the ref that the user gave, for example a commit SHA, a branch name, a tag, `main`, or `HEAD~5`. If the user gave none, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD`. The three dots compare against the merge-base. Also note the list of commits with `git log <fixed-point>..HEAD --oneline`.

Before you continue, make sure that the fixed point resolves (`git rev-parse <fixed-point>`) and that the diff is not empty. 

### Step 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (for example `#123`, `Closes #45`, or GitLab `!67`). Fetch them with the workflow in `docs/ISSUE-TRACKER.md`.
2. A path the user passed as an argument.
3. A spec file under `docs/` or `specs/` that matches the branch name or the feature.
4. If you find nothing, ask the user where the spec is. If the user says that no spec exists, the spec compliance subagent skips its review and reports "no spec available".

### Step 3: Spawn parallel subagents
Spawn two parallel subagents in parallel to execute review as well as manual QA and regression testing.

#### Step 3a: Full code review
Have review-agent review the code with the prompt in [review-prompt.md](review-prompt.md) word for word. Replace only the placeholders.

#### Step 3b: Full manual regression test
Have a new qa-agent manually test the entire application scope and prove that the change introduced no visual or feature regressions. Use the manual testing steps defined in the implementation plans `Manual verification` as the absolute minimal baseline, but engage in rigorous explorative edge case testing as well. The qa-agent must return a summary of their findings following the exact [review-result-template.md](review-result-template.md).

### Step 4: Consolidate results
Consolidate both agents results into one review result that follows [review-result-template.md](review-result-template.md). If either reviewer reports `NEEDS_CHANGES`, the final verdict is `NEEDS_CHANGES`. Return the consolidated review result.