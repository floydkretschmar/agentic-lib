# Spec review prompt template

<spec-quality-prompt-template>

From the business side only, review whether the delivered behavior gives users what the spec promises: nothing missing, nothing contradicted, nothing extra. A separate technical reviewer covers code quality, test quality, security, performance, and the Implementation Decisions and Testing Decisions of the spec. Leave those out.

Inputs:
- <!--originating spec source as identified-->
- <!--The full diff command and commit list.-->
- Tasks marked "done" in the spec/scheme

Addressed from last review:
<!-- List ALL changes that have been addressed by previous reviews-->

List what the spec requires for the scope under review: its user stories, the acceptance criteria of the phases in scope, the business rules they contain, and its Out of Scope section. For each item, find out what the product now does. Then report:

1. **Missing**: a story or criterion in scope that a user cannot complete, or can complete only in part.
2. **Contradicted**: behavior that differs from what the spec states, such as a rule outcome, limit, calculation, state, permission, sequence, or message.
3. **Broken paths**: an alternate or exception path of a story where the user ends up somewhere other than the spec describes, or at a dead end.
4. **Benefit not delivered**: criteria met to the letter, where the user still does not get the benefit that the story names.
5. **Out of scope**: behavior that a user can observe that no story asks for, or that the Out of Scope section excludes.
6. **Language**: user-facing terms that differ from the terms the spec uses.

Separately, list as open decisions each behavior that the implementation settled where the spec is silent (defaults, limits, rounding, ordering, wording). The user can then accept or correct it.

Output:
## Spec Compliance Review
**Verdict:** PASSED | NEEDS_CHANGES
**Coverage:** <N> of <M> in-scope stories and criteria delivered

[one line summary]

Findings:
- [blocking | suggestion] story or criterion - expected behavior, observed behavior, impact on the user (evidence: file:line)

Open decisions:
- behavior chosen where the spec is silent (evidence: file:line)

</spec-quality-prompt-template>
