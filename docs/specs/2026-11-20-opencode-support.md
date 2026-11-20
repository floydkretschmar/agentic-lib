## Problem Statement

The agent setup in this repository works for Claude Code and Codex. A developer who uses opencode gets the project rules from `AGENTS.md`, but no project subagents, no protection from the safety hook, no rtk command rewriting and no context-mode. The developer has to build that setup by hand, and it drifts from the setup of the other two tools.

## Solution

The repository ships an opencode V2 configuration next to the Claude Code and Codex configurations. In opencode, a developer gets the same skills, the same five read-only subagents on Anthropic models, the same safety rules for shell commands and file edits, rtk rewriting of shell commands, and the context-mode plugin. The safety rules stay in the one Python hook that Codex already uses.

## User Stories

1. As an opencode user, I want the repository's skills to load in opencode, so that I can use the same workflow as in Claude Code and Codex.
2. As an opencode user, I want the project skills to win over global skills with the same id, so that the project defines its own workflow.
3. As an opencode user, I want the five project subagents in opencode, so that `/plan`, `/review` and the other skills can delegate to them.
4. As an opencode user, I want the subagents to run on the same Anthropic models and effort levels as in Claude Code, so that results are comparable between tools.
5. As an opencode user, I want the subagents to be unable to edit files, so that they stay read-only like in the other tools.
6. As an opencode user, I want destructive shell commands blocked with the hook's reason, so that the agent cannot run `git reset --hard`, `rm -rf`, `sudo` or `curl | sh`.
7. As an opencode user, I want edits and writes to `.git`, `.ssh`, `.env`, key files and paths outside the project blocked, so that the agent cannot damage secrets or repository internals.
8. As an opencode user, I want edits to ordinary project files allowed when opencode passes an absolute path inside the project, so that the guard does not block normal work.
9. As an opencode user, I want a tool call blocked when the safety hook fails, times out or returns unreadable output, so that a broken guard never lets a call through.
10. As an opencode user, I want rtk to rewrite allowed shell commands, so that command output costs fewer tokens.
11. As an opencode user, I want a shell command to run unchanged when rtk fails, so that rtk problems never stop work.
12. As an opencode user, I want the safety hook to judge the command the model wrote, before rtk rewrites it, so that a rewrite cannot hide a dangerous command from the guard.
13. As an opencode user, I want context-mode loaded as an opencode plugin, so that I get the same context savings as in Codex.
14. As a Codex user, I want patches that move a file onto a sensitive path blocked, so that a `Move to` line cannot bypass the guard.
15. As a maintainer, I want the plugin's commands and timeouts in the opencode configuration file, so that no command or timeout is a literal in code.
16. As a maintainer, I want `./run.sh test` to run the plugin tests next to the hook tests, so that one command verifies both.
17. As a maintainer, I want `./run.sh setup-environment` to check that the installed rtk supports opencode, so that a too-old rtk fails at setup and not in a session.
18. As a new user, I want the README to describe the opencode setup and its requirements, so that I can set it up without reading the configuration files.

## Implementation Decisions

- **Target version.** opencode V2 (2.3.x) with the V2 configuration keys (`plugins`, `agents` frontmatter with `permissions`), the V2 plugin shape (default export with `id` and `setup`) and the V2 tool names (`shell`, `edit`, `write`, `patch`).
- **Configuration file.** One opencode configuration file inside the `.opencode` folder, next to the plugins and agents, in the same way that Codex keeps its configuration inside `.codex`. It lists two plugins in this order: the project pre-tool-use plugin with its options, then `context-mode`. It has no MCP, permissions, instructions or skills entries.
- **Pre-tool-use plugin.** One local plugin, stored as a folder so that its tests and fixture are not loaded as plugins. Its public interface is its default export, `{ id, setup(context) }`. `setup` reads four required options (safety hook command, safety hook timeout, rtk rewrite command, rtk rewrite timeout) and fails if one is missing or has the wrong type. It then registers one `execute.before` tool hook. The plugin runs both commands in the project directory from the plugin context and has no dependencies beyond Node built-ins.
- **Hook sequence for each tool call.**

  ```
  tool call ──> mapped tool? ──no──> pass through
                    │ yes
                    v
       read input field (missing => block)
                    │
                    v
       edit/write: make path project-relative if inside the project
                    │
                    v
       safety hook ──deny / error / timeout / bad output──> block with reason
                    │ allow
                    v
       shell call? ──no──> pass through
                    │ yes
                    v
       rtk rewrite ──failure / empty answer──> run original command
                    │ rewritten
                    v
       run rewritten command
  ```

- **Tool mapping to the hook payload.** Every payload has the event name `PreToolUse`, a tool name and a tool input. `shell` and `bash` map to `Bash` with the command. `patch` maps to `apply_patch` with the patch text as the command. `edit` maps to `Edit` and `write` maps to `Write`, each with the normalized path as `file_path`. All other tools, including MCP tools, pass through unchecked.
- **Path contract.** The plugin owns opencode's path semantics. It resolves a path against the project directory from the plugin context. A path inside the project goes to the hook as a relative path. A path outside it goes as an absolute path, which the hook denies under its existing rule.
- **Safety hook.** The hook stays the single source of the rules and stays reachable only through `run.sh safety-hook`. It gains a branch that checks the `file_path` of `Edit` and `Write` calls with the existing sensitive-path rule. It reuses the existing input reader and the existing patch denial path instead of adding parallel functions. The patch path reader also reads `Move to` targets. Both changes are approved by the user as security changes.
- **rtk contract.** The plugin calls the rtk rewrite command with `--agent`, the agent name and the original command as one argument. rtk answers with JSON that holds a `command`, or with an empty object. Verified with rtk 1.2.1.
- **Subagents.** Five V2 agent files with mode `subagent`, a permission rule that denies the `edit` action for every resource, and the same prompt body as the Claude Code agent. Models: architect `anthropic/claude-fable-5-2#high`; qa and review `anthropic/claude-opus-5-5#high`; codebase researcher and web researcher `anthropic/claude-opus-5-5#medium`.
- **Skills.** A `.opencode/skills` symlink to the shared skills folder, in the same way as the existing Claude Code and Codex symlinks. It gives the project skills a higher precedence than global opencode skills and does not depend on opencode's Claude compatibility settings.
- **context-mode.** Loaded only as an opencode plugin by package name. opencode installs it. The plugin registers the `ctx_*` tools itself, so no MCP entry is added.
- **Dependencies.**

  | Dependency | Version | Use |
  | --- | --- | --- |
  | opencode | 2.3.x | Runs the configuration |
  | Node | 24.x (24.16.0 verified) | Runs the plugin tests with built-in type stripping |
  | rtk | 1.2.1 | `rtk hook opencode` |
  | context-mode | 2.2.1 at time of writing, unpinned | opencode plugin |
  | Python | 3.x, as today | Safety hook |

## Testing Decisions

- A good test drives the public interface and asserts observable results: whether a tool call is rejected with the hook's reason, or what command it runs.
- The plugin tests drive the plugin's default export through `setup` with a fake plugin context that captures the registered hook. The fixture reads the plugin options from the real opencode configuration file, so the tests cover the configured safety command, `run.sh` and the real Python hook together. The fixture replaces only the rtk command with a stub that echoes its arguments. The fixture stays local to the plugin folder.
- The hook tests extend the existing subprocess tests of the Python hook, which are the prior art. They add parameters to the existing tests instead of new test methods.
- Black-box tests:
  1. The plugin blocks with the hook's reason: `shell` with `git reset --hard HEAD`, `bash` with `rm -rf build`, `write` to `.env`, `edit` of the absolute path of the project's `.git/config`, `write` to `/etc/hosts`, `write` to a relative path that leaves the project, a `patch` that deletes `.git/config`, `shell` with `git status` when the safety command exits with an error, times out or prints anything on success, and `shell` without a command.
  2. The plugin allows: `shell` with `git status` as agent `build`, rewritten to the rtk stub's answer; `edit` of the absolute path of a project file, unchanged; `read` of `.env`, unchanged; `shell` with `git status` when the rtk stub fails or answers `{}`, unchanged.
  3. `setup` fails when an option is missing or has the wrong type.
  4. The hook denies `Edit` of `.env`, `Write` to `/etc/hosts` and a patch that moves a file to `.git/hooks/pre-commit`, and allows `Write` to `docs/GLOSSARY.md`.

## Out of Scope

- Safety checks for opencode MCP tool calls.
- Moving the safety hook out of `.codex`, adding the safety hook to Claude Code, or protecting the guard's own files.
- opencode slash command files for the skills.
- rtk binary discovery outside `PATH`, `RTK_DISABLED`, and Windows support.
- A generator for the per-tool copies of the agent prompts.
- A TypeScript type check.

## Further Notes

opencode is not installed on the development machine. These points come from opencode's source and need a check in a real session:

- whether the configured plugin options replace the auto-discovered plugin instead of loading it twice without options
- the input shape of a GPT `patch` call
- whether the skill scan follows the symlink
- whether skills appear as `@skill` mentions in the prompt
- whether opencode resolves a plugin folder without `package.json` to its `index.ts`
- whether opencode writes cache files into `.opencode` that `.gitignore` must exclude

The hook's `rm` rules only inspect the first token of a command, so `git status && rm -rf x` passes. This existing gap applies to opencode as well.

The hook also ignores the shell `workdir`, and it allows relative `..` paths inside patches. Both gaps exist for Codex today and apply to opencode too.
