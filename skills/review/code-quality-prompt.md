# Code quality review prompt template

<code-quality-prompt-template>
Review the implemented change for defects, risk, and code quality. Do not audit whether the user stories and acceptance criteria are delivered, because a separate business reviewer does that. In the spec, you own the Implementation Decisions and the Testing Decisions.

Inputs:
- <!--originating spec source as identified-->
- <!--The full diff command and commit list.-->
- Tasks marked "done" in the spec/scheme

Addressed from last review:
<!-- List ALL changes that have been addressed by previous reviews-->

The measures below tell you where to look. Report only what you can show in the code.

1. **Correctness**: logic errors, unhandled edge cases (empty, missing, boundary, duplicate, repeated or concurrent calls), and regressions in existing callers of changed code. Judge against what the code evidently intends. The business reviewer decides whether that intent matches the user stories.
2. **Error handling**: failures that are swallowed, leave partial state, or surface nowhere, catch blocks that are broader than the failure they expect, and fallback defaults that hide a missing required value.
3. **Data integrity**: transaction boundaries, partial writes, migrations that lose or orphan data, incompatible changes to persisted formats or public contracts.
4. **Security**: missing authorization on new paths, injection (SQL, command, path, markup), unvalidated input crossing a trust boundary, secrets in code or logs, weak or home-made cryptography, unvetted new dependencies.
5. **Performance and resources**: queries inside loops, unbounded result sets, loops or retries, missing timeouts, unreleased handles, races on shared state.
6. **Test quality**: every new behavior has a test through a public interface, and that test fails if the behavior breaks. Tests do not mock internal collaborators, every test has meaningful assertions, and no test is coupled to implementation detail. Database or domain invariants do not change without integration-test coverage (see docs/TESTING.md).
7. **Complexity**: units that a reader cannot understand in one read. Look closer at units over about 30 lines, over 10 branch points, nested deeper than 3 levels, or with more than 4 parameters.
8. **Duplication**: the same logic shape, roughly 6 lines or more, in more than one place in the change, or code that re-implements something that the codebase already has.
9. **Module design**:
   - Shallow modules and middle men: an interface nearly as large as what it hides, or a unit that mostly delegates.
   - Feature envy and message chains: code that works on another object's data more than its own, or depends on `a.b().c()` navigation.
   - Data clumps and primitive obsession: values that always travel together, or a primitive that stands in for a domain concept.
   - Repeated switches: the same conditional on the same type in several places.
   - Shotgun surgery and divergent change: one logical change scattered across many files, or one module edited for unrelated reasons.
   - Refused bequest: an implementer that ignores or overrides most of what it inherits.
   - Parallel abstractions that model the same responsibility.
10. **Speculative generality**: internal abstractions, parameters, configuration, flags, or extension points that no requirement in the spec needs.
11. **Dead code**: code that is unused, code that only tests reach, code that this phase added but did not wire into production, and scaffolding that remains after its phase.
12. **Naming**: names that mislead about what a function does or a value holds.
13. **Refactoring**: concrete refactorings still open after green that can remove code or deepen a module.
14. **Technical decisions and conventions**: departures from the spec's Implementation Decisions and Testing Decisions or the scheme's architectural decisions, and rules in docs/EXECUTION.md and docs/languages/*.md that the change breaks.

Output:
## Code Quality Review
**Verdict:** PASSED | NEEDS_CHANGES

[one line summary]

Findings:
- [blocking | suggestion] file:line - issue, its consequence, and the smallest fix

</code-quality-prompt-template>
