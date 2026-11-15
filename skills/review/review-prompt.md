# Review prompt template

<review-prompt-template>

Your task is to confirm two things:
1. Does the delivered behavior give users what the spec promises: nothing missing, nothing contradicted, nothing extra.
2. Identify any defects, risk, and code quality issues in the implemented change

Inputs:
- [ originating spec source as identified ]
- [ The full diff command and commit list ]
- Tasks marked "done" in the spec/scheme

Addressed from last review:
[ List ALL changes that have been addressed by previous reviews ]

## Spec review
List what the spec requires for the scope under review. For each item, find out what the product now does. Then report:

1. **Missing**: a story or criterion in scope that a user cannot complete, or can complete only in part.
2. **Contradicted**: behavior that differs from what the spec states, such as a rule outcome, limit, calculation, state, permission, sequence, or message.
3. **Broken paths**: an alternate or exception path of a story where the user ends up somewhere other than the spec describes, or at a dead end.
4. **Benefit not delivered**: criteria met to the letter, where the user still does not get the benefit that the story names.
5. **Out of scope**: behavior that a user can observe that no story asks for, or that the Out of Scope section excludes.
6. **Language**: user-facing terms that differ from the terms the spec uses.

Separately, list as open decisions each behavior that the implementation settled where the spec is silent (defaults, limits, rounding, ordering, wording). The user can then accept or correct it.

## Code quality review
The measures below tell you where to look. Report only what you can show in the code.

1. **Correctness**: logic errors, unhandled edge cases (empty, missing, boundary, duplicate, repeated or concurrent calls), and regressions in existing callers of changed code. Judge against what the code evidently intends. The business reviewer decides whether that intent matches the user stories.
2. **Error handling**: failures that are swallowed, leave partial state, or surface nowhere, catch blocks that are broader than the failure they expect, and fallback defaults that hide a missing required value.
3. **Data integrity**: transaction boundaries, partial writes, migrations that lose or orphan data, incompatible changes to persisted formats or public contracts.
4. **Security**: missing authorization on new paths, injection (SQL, command, path, markup), unvalidated input crossing a trust boundary, secrets in code or logs, weak or home-made cryptography, unvetted new dependencies.
5. **Performance and resources**: queries inside loops, unbounded result sets, loops or retries, missing timeouts, unreleased handles, races on shared state.
6. **Test quality**: every new behavior has a test through a public interface, and that test fails if the behavior breaks. Tests do not mock internal collaborators, every test has meaningful assertions, and no test is coupled to implementation detail. Database or domain invariants do not change without integration-test coverage.
7. **Complexity**: units that a reader cannot understand in one read. Look closer at units over about 30 lines, over 10 branch points, nested deeper than 3 levels, or with more than 4 parameters.
8. **Duplication**: the same logic shape, roughly 6 lines or more, in more than one place in the change, or code that re-implements something that the codebase already has.
9. **Speculative generality**: internal abstractions, parameters, configuration, flags, or extension points that no requirement in the spec needs.
10. **Dead code**: code that is unused, code that only tests reach, code that this phase added but did not wire into production, and scaffolding that remains after its phase.
11. **Naming**: names that mislead about what a function does or a value holds.
12. **Refactoring**: concrete refactorings still open after green that can remove code or deepen a module.

Return a summary of your findings following the exact [review-result-template.md](review-result-template.md).

</review-prompt-template>
