<!-- 2-3 sentence description of the actual project and its scope -->

Skills are located in `.codex/skills/*/SKILL.md`
General project information can be fetched from `docs/PROJECT.md`
Testing principles are located in `docs/TESTING.md`
Execution principles (relevant when changing production code) are located in `docs/EXECUTION.md`
Programming language specific rules are located in `docs/languages/*.md`

YOU ALWAYS FOLLOW THE FOLLOWING SKILL-CHAIN. **None** of these steps can be skipped, or combined unless explicitly stated by the user:
```
/plan-feature OR /rearchitect ──> /scheme ──> /execute ──> /review ──> /finish                                                                                                                                                                                    
```

# Operating Principles (Non-Negotiable)
- **Less is better**: Reducing lines of code instead of adding them is a virtue.
- **Remove is better than add**: NEVER add if you can modify or delete instead. LESS code is an indicator for BETTER quality.
- **Security changes need explicit approval**: If a task touches authentication, credentials, production config, or secret material, stop and explicitly confirm scope with the user before proceeding.
- **Smallest change that works**: Minimize blast radius; don't refactor adjacent code unless necessary.
- **Correctness over cleverness**: Prefer boring, readable solutions that are easy to maintain.
- **Leverage existing patterns**: Follow established project conventions before introducing new abstractions.
- **Prove it works**: "Seems right" is not done. Validate with tests/build/lint.
- **Be explicit about uncertainty**: If you cannot verify something, say so.
- **No Laziness**: Find root causes. No temporary fixes. Production quality code.
- **Subagent Strategy**: Use subagents liberally to keep main context window clean. Outsource research, exploration, and parallel analysis to subagents. One task per subagent for focused execution
- **Refactor after green**: The refactor step of TDD is mandatory after behavior is green.

# Forbidden Actions
- **Never push, or create PRs without explicit user approval**
- **Never execute resets or rollbacks without explicit user approval**
- **Never expose secrets from logs, environment dumps, CI output, screenshots, or terminal transcripts.**
- Never commit secrets or credentials
- Never force push to main/master
- Never make changes outside the scheme without discussion
- Never mark done without FULL verification evidence is green:
    - `./run.sh test`
    - `./run.sh format`
    - `./run.sh build`
