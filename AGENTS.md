You always use `/unslop`.

The project tracks its issues in GitHub, as `docs/ISSUE-TRACKER.md` describes.
Defined shared terminology can be found under `docs/GLOSSARY.md`.
When you change user-facing surfaces, use the prototype under `prototypes/` as the design reference
When you make or propose any change, make sure to follow the ADRs in `docs/adr/*`

# Operating principles (non-negotiable)
- **Less is better.** Reduce lines of code instead of adding them.
- **Remove is better than add.** NEVER add if you can modify or delete instead.
- **Security changes need explicit approval.** If a task touches authentication, credentials, production configuration, or secret material, stop and explicitly confirm the scope with the user.
- **Smallest change that works.** Do not refactor adjacent code unless it is necessary. The exception, which the project encourages, is a boy scout change: a small and LOCALIZED fix, refactor or alignment with a general project rule. Tell the user about it.
- **Correctness over cleverness.** Prefer boring, readable solutions that are easy to maintain.
- **Use existing patterns.** Follow the conventions of the project before you introduce new abstractions.
- **Prove it works.** Run the tests, the build and lint, because "seems right" is not done.
- **Be explicit about uncertainty.** If you cannot make sure that something is true, say so.
- **No laziness.** Find the root cause and write a production-quality fix, never a temporary one.
- **Refactor after green.** After the behavior is green, always do the refactor step of TDD with the /tdd skill.

# Forbidden actions
- **Never push or create PRs without explicit user approval.**
- **Never execute resets or rollbacks without explicit user approval.**
- **Never expose secrets from logs, environment dumps, CI output, screenshots, or terminal transcripts.**
- Never commit secrets or credentials.
- Never force push to main/master.
- Never make changes outside the scheme without discussion, except for a boy scout change as defined above.
- Never mark a task done until FULL verification evidence is green:
  - `./run.sh lint`
  - `./run.sh test`
  - `./run.sh build`

## Boy scout rule
Fix an inconsistency, regression, bug or departure from a general project rule even outside the task, if it is small, localized and easy. Do the same for small and localized refactors.

## Coding conventions
- Prefer explicit code over overly compact code
- Always remove all dead and redundant code, abstractions and configuration.
- Keep exactly one canonical port path for each responsibility, and remove parallel and dead abstractions.
- Never use default values anywhere. Require an explicit value, and fail fast when it is missing.
- Never write comments. The code must be self-explanatory through the naming of variables, functions and interfaces alone.
- Configuration lives in a dedicated configuration file. A hostname, a port, a URL or any other parameterized value is never a literal or a constant in code.
- Use proper error handling patterns, and avoid try/catch where you can
- Limit unnecessary complexity and nesting
- Do not nest ternary operators. For multiple conditions, prefer switch statements or if/else chains
- Replace sensitive values with `***REDACTED***`, and never paste raw credentials.

## Testing rules
- Never export a function just to test it: Functionality is tested at the public interface, nowhere else.
- Every test must include meaningful assertions and follow the Arrange-Act-Assert pattern.
- Cover a new case with a change to an existing test, for example a new parameter, instead of a new test.
- Remove duplicate tests, including partial duplicates of the same logic spread across multiple tests.
- Extract shared setup or fixture logic into a single fixture file next to the test files, and reuse it. Fixtures have to stay local in a module, so do not centralize them or cross-reference them across modules.
- A test that passes at its first run proves nothing yet. Break the line of production code for one run, see the test fail, and restore the line.
- Write test that prevent race conditions and flakiness. Wait for all the values a step needs in one condition before asserting the next step.
- Never add dedicated tests for a cleanup-only change that changes no user-visible behavior, such as dead-code removal, catalog pruning, or unused-import deletion.

## Naming conventions
A name says exactly what a thing is or does in and the reader must understand it in one read. Long names are preferable to short ones if they can be understood without parsing the surrounding context.

- A function name says what the function does or what it returns: `shouldUpdatePrimaryCurrency`, not `primaryFollows`.
- A parameter or a variable names its role and its noun: `previousAccount`, not `previous`.
- A variable that holds an id names its entity: `transactionId`, not `id`.
- A collection takes the plural of what it holds: `transactions`, not `rows`.
- A port method starts with a verb from one family and states its scope: `find`, `findAllThatMatch`, `findEarliestTransactionDateForAccount`.
