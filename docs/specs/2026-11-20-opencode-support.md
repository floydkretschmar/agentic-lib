## Problem Statement

The agent setup in this repository works for Claude Code and Codex. A developer who uses opencode gets the project rules from `AGENTS.md`, but no project subagents, no protection from the safety hook and no rtk command rewriting. The developer has to build that setup by hand, and it drifts from the setup of the other two tools. Claude Code runs without the safety hook that Codex uses.

## Solution

The repository ships an opencode V2 configuration next to the Claude Code and Codex configurations. In opencode, a developer gets the same skills, the same five read-only subagents on Anthropic models, the same safety rules for shell commands and file edits, and rtk rewriting of shell commands. The safety rules stay in the one Python hook that Codex already uses, which moves out of `.codex` so that Claude Code and opencode can run it without the Codex folder. The repository drops context-mode.

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
13. As a Codex user, I want patches that move a file onto a sensitive path blocked, so that a `Move to` line cannot bypass the guard.
14. As a maintainer, I want the plugin's commands and timeouts in the opencode configuration file, so that no command or timeout is a literal in code.
15. As a maintainer, I want `run.sh` and the safety hook to use only files that every project has, so that a project that keeps only some of `.claude`, `.codex` and `.opencode` still works.
16. As a new user, I want the README to describe the opencode setup, its requirements and the command that runs the plugin tests, so that I can set it up without reading the configuration files.
17. As a maintainer, I want context-mode removed from all three setups, so that rtk is the only command rewriter to install and maintain.
18. As a Claude Code user, I want every tool call checked by the same safety hook as in Codex and opencode, so that the agent cannot run destructive commands or edit sensitive paths.
19. As a Claude Code user, I want edits to project files allowed although Claude Code passes absolute paths, so that the guard does not block normal work.
20. As a Claude Code user, I want a tool call blocked when the safety hook fails, times out or returns unreadable output, so that a broken guard never lets a call through.
21. As a Codex user, I want patches that leave the project through a relative `..` path blocked, and patches with an absolute path inside the project allowed, so that the guard judges where a patch writes and not how its path is spelled.
22. As a Claude Code user, I want `NotebookEdit` calls checked like `Edit` and `Write`, so that a notebook edit cannot reach a sensitive path.
23. As a user of any of the three tools, I want the guard to judge where a path leads after symlinks, so that a symlink cannot take an edit out of the project or into `.git`, and a project opened through a symlinked path can still be edited.
24. As a Claude Code user, I want the guard to keep working after the session changes into a folder outside the project, so that a `cd` neither blocks every tool call nor runs another repository's `run.sh`.
25. As a Codex or opencode user, I want relative paths judged from the directory that the tool works in, so that a session started in a subfolder can edit the files of its project.

## Implementation Decisions

- **Target version.** opencode V2 (2.3.x) with the V2 configuration keys (`plugins`, `agents` frontmatter with `permissions`), the V2 plugin shape (default export with `id` and `setup`) and the V2 tool names (`shell`, `edit`, `write`, `patch`).
- **Configuration file.** One opencode configuration file inside the `.opencode` folder, next to the plugins and agents, in the same way that Codex keeps its configuration inside `.codex`. It lists one plugin, the project pre-tool-use plugin with its options. It has no MCP, permissions, instructions or skills entries.
- **Pre-tool-use plugin.** One local plugin, stored as a folder so that its tests and fixture are not loaded as plugins. Its public interface is its default export, `{ id, setup(context) }`. `setup` reads four required options (safety hook command, safety hook timeout, rtk rewrite command, rtk rewrite timeout) and fails if one is missing or has the wrong type. It then registers one `execute.before` tool hook. The plugin runs both commands in the project directory from the plugin context and has no dependencies beyond Node built-ins.
- **Hook sequence for each tool call.**

  ```
  tool call ──> mapped tool? ──no──> pass through
                    │ yes
                    v
       read input field (missing => block)
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

- **Tool mapping to the hook payload.** Every payload has the event name `PreToolUse`, a tool name and a tool input. `shell` and `bash` map to `Bash` with the command. `patch` maps to `apply_patch` with the patch text as the command. `edit` maps to `Edit` and `write` maps to `Write`, each with the path as `file_path` as opencode sent it. Every payload carries the location directory from the plugin context as `cwd`. All other tools, including MCP tools, pass through unchecked.
- **Path contract.** The safety hook owns the path semantics for `Edit`, `Write`, `NotebookEdit` and patch paths. `run.sh safety-hook` passes the folder that holds `run.sh` as the project directory argument. The hook resolves each path against the `cwd` of the payload in two ways, because tools differ: following symlinks before `..` as the kernel does, and collapsing `..` before following symlinks as Node and Claude Code do. It also resolves the project directory's symlinks. It also judges the path with `..` collapsed and no symlinks followed, relative to the project, and the entry itself, which is its folder with symlinks followed plus its own name, so a sensitive name such as a `.env` symlink or a `.git` folder that is a symlink is denied, while folders above the project do not count. Patch header paths are read the way Codex reads them: the patch is split on line feeds only and each line is trimmed. It judges the raw path as the tool sent it, checks a resolved path inside the project as a relative path, and denies a resolved path outside it under the existing absolute-path rule. A payload without `cwd` or without a path is denied for these tools. Shell `rm` arguments and MCP tool arguments keep the existing rule. The opencode plugin sends paths unchanged.
- **Safety hook.** The hook stays the single source of the rules and stays reachable only through `run.sh safety-hook`. It moves with its tests from `.codex/hooks` to a root `hooks` folder next to `skills`, so that no tool folder depends on another. It gains a branch that checks the `file_path` of `Edit` and `Write` calls with the existing sensitive-path rule. It reuses the existing input reader and the existing patch denial path instead of adding parallel functions. The patch path reader also reads `Move to` targets. Both changes are approved by the user as security changes.
- **rtk contract.** The plugin calls the rtk rewrite command with `--agent`, the agent name and the original command as one argument. rtk answers with JSON that holds a `command`, or with an empty object. Verified with rtk 1.2.1.
- **Claude Code.** `.claude/settings.json` runs the safety hook for every tool (matcher `*`) with `"$CLAUDE_PROJECT_DIR/run.sh" safety-hook`, the same timeout as Codex and `onFailure: "block"`, next to the existing `rtk hook claude` hook. Claude Code runs matching hooks in parallel, and a deny takes precedence over the rtk rewrite, so a rewrite cannot hide a dangerous command from the guard.
- **Subagents.** Five V2 agent files with mode `subagent`, a permission rule that denies the `edit` action for every resource, and the same prompt body as the Claude Code agent. Models: architect `anthropic/claude-fable-5-2#high`; qa and review `anthropic/claude-opus-5-5#high`; codebase researcher and web researcher `anthropic/claude-opus-5-5#medium`.
- **Skills.** A `.opencode/skills` symlink to the shared skills folder, in the same way as the existing Claude Code and Codex symlinks. It gives the project skills a higher precedence than global opencode skills and does not depend on opencode's Claude compatibility settings.
- **run.sh.** It runs only what every project has. `test` runs the hook tests, and `setup-environment` checks that rtk is installed. It does not run the opencode plugin tests or check tool-specific rtk subcommands. The README names `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts` for the plugin tests.
- **context-mode.** Removed from the repository: the Codex MCP server and its six context-mode hooks, the opencode plugin entry, and the npm install in `run.sh`.
- **Dependencies.**

  | Dependency | Version | Use |
  | --- | --- | --- |
  | opencode | 2.3.x | Runs the configuration |
  | Node | 24.x (24.16.0 verified) | Runs the plugin tests with built-in type stripping |
  | rtk | 1.2.1 | `rtk hook claude`, `rtk hook codex`, `rtk hook opencode` |
  | Python | 3.x, as today | Safety hook |
  | Claude Code | 2.1.295 or later | `onFailure` for the safety hook |

## Testing Decisions

- A good test drives the public interface and asserts observable results: whether a tool call is rejected with the hook's reason, or what command it runs.
- The plugin tests drive the plugin's default export through `setup` with a fake plugin context that captures the registered hook. The fixture reads the plugin options from the real opencode configuration file, so the tests cover the configured safety command, `run.sh` and the real Python hook together. The fixture replaces only the rtk command with a stub that echoes its arguments. The fixture stays local to the plugin folder.
- The hook tests extend the existing subprocess tests of the Python hook, which are the prior art. They add parameters to the existing tests instead of new test methods.
- Black-box tests:
  1. The plugin blocks with the hook's reason: `shell` with `git reset --hard HEAD`, `bash` with `rm -rf build`, `write` to `.env`, `edit` of the absolute path of the project's `.git/config`, `write` to `/etc/hosts`, `write` to a relative path that leaves the project, a `patch` that deletes `.git/config`, `shell` with `git status` when the safety command exits with an error, times out or prints anything on success, and `shell` without a command.
  2. The plugin allows: `shell` with `git status` as agent `build`, rewritten to the rtk stub's answer; `edit` of the absolute path of a project file, unchanged; `read` of `.env`, unchanged; `shell` with `git status` when the rtk stub fails or answers `{}`, unchanged.
  3. `setup` fails when an option is missing or has the wrong type.
  4. The hook denies `Edit` of `.env`, `Edit` of the absolute path of the project's `.git/config`, `Write` to `/etc/hosts`, a patch that moves a file to `.git/hooks/pre-commit` and a patch that adds `../outside.md`, and allows `Write` to the absolute path of the project's `docs/GLOSSARY.md`.
  5. The hook denies `NotebookEdit` of a notebook outside the project, a `Write` through a symlink inside the project that points outside, and a payload without `cwd`. It allows a `Write` through a symlink to the project folder, and a patch that updates `../README.md` from the `docs` folder as `cwd`. The hook tests run against a real temporary project folder, because symlinks need real files.

## Out of Scope

- Safety checks for opencode MCP tool calls.
- Protecting the guard's own files.
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

The hook also ignores the shell `workdir`. This gap applies to all three tools.

In Claude Code, the `Write` and `Edit` tools can no longer write outside the project, for example to the session scratchpad or to `~/.claude/plans`. Shell commands still can.
