You always use `/simple-english` and `/unslop`.

The project tracks its issues in GitHub, as `docs/ISSUE-TRACKER.md` describes.
General project information is in `docs/PROJECT.md`.
Testing principles are in `docs/TESTING.md`.
When you change production code, apply the execution principles in `docs/EXECUTION.md`.
Rules for each programming language are in `docs/languages/*.md`.

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
- **Subagent strategy.** Use subagents liberally for research, exploration, and parallel analysis, to keep the main context window clean. Give each subagent one task so that it stays focused.
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

`./run.sh format` applies the formatting and lint rules, and `./run.sh lint` makes sure that the code follows them. Only `lint` is a gate, because `format` rewrites the files and so always succeeds.
