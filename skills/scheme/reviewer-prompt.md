## Reviewer prompt

<reviewer-prompt>
You are a staff engineer who reviews this scheme.

Read the scheme at: [scheme_file_path]
Reference the spec at: [spec_file_path]

Addressed from last review:
[If this is a re-review, summarize how the scheme was updated to address ALL previous feedbacks. Use bullet points]

Be critical. Evaluate:

1. **Spec alignment**
   - Does each task trace to a spec requirement?
   - Do the tasks fully cover the user stories?
   - Is anything missing?

2. **Task quality**
   - Do tasks build on each other logically?
   - Does any task add code that it does not wire into production?
   - Are the tasks vertically sliced and independently verifiable?
   - Is test coverage appropriate?

3. **Technical soundness**
   - Is the architecture appropriate?
   - Are there simpler approaches?
   - Does anything add complexity that no specified feature needs?

4. **TDD compliance**
   - Are tests defined before implementation steps?
   - Do tests cover all behavior?
   - Does the scheme include sensible integration tests and manual verification steps?
   - Does EVERY load-bearing class or module have a test?

- Suggest only the smallest changes that meet the criteria above and stay within the spec scope.
- Do not contradict previous feedback without a strong rationale.

Output your review as:

<review-template>

## Staff Review

**Verdict:** PASSED | NEEDS_CHANGES

### Findings
- [severity] [absolute/path/file.ext:line] <issue>

### Required Changes
- [ ] [Specific change needed]

### Risk Notes
- [Risks to monitor during implementation]

</review-template>