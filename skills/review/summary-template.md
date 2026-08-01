# Review summary template

<review-summary-template>

# Review Report

**Date:** YYYY-MM-DD HH:MM (local)
**Base Branch:** <main|master|...>
**Commit Range:** <base>...HEAD

## Diff Scope
- Files changed: <N>
- Key areas:
  - [path or module]
  - [path or module]
- User-story Coverage: <N> of <M> in-scope stories and criteria delivered

## Spec/Scope Review
**Verdict:** PASSED | NEEDS_CHANGES

### Findings
- [severity] [absolute/path/file.ext:line] <issue>

## Code Quality/Risk Review
**Verdict:** PASSED | NEEDS_CHANGES

### Findings
- [severity] [absolute/path/file.ext:line] <issue>

## Final Verdict
REVIEW: PASSED | REVIEW: NEEDS_CHANGES: <summary>

### Required Changes
- [ ] [Specific change needed]

### Open decisions
- [ ] [Specific question to be clarified]

</review-summary-template>