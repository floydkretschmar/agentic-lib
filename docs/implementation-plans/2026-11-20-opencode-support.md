# Implementation plan: opencode support

> Source spec: docs/specs/2026-11-20-opencode-support.md

## Architectural decisions

Durable decisions that apply across all phases:

- **Layout**: `.opencode/opencode.json`, `.opencode/plugins/pre-tool-use/{index.ts,pre-tool-use.test.ts,pre-tool-use.fixture.ts}`, `.opencode/agents/<name>.md`, `.opencode/skills -> ../skills`.
- **Plugin contract**: default export `{ id: "pre-tool-use", setup(context) }`. It reads the required options `safetyHookCommand` (argument array), `safetyHookTimeoutMilliseconds`, `rtkRewriteCommand` (argument array) and `rtkRewriteTimeoutMilliseconds` from `context.options`, and the project directory from `context.location.directory`. It registers its callback with `context.tool.hook("execute.before", callback)` and reads `event.tool`, `event.agent` and the mutable `event.input`. Configured in `.opencode/opencode.json` as the only plugin, `{ "package": "./plugins/pre-tool-use", "options": {...} }`.
- **Safety command**: `["sh", "-c", "\"$(git rev-parse --show-toplevel)/run.sh\" safety-hook"]`, the same command string as in `.codex/config.toml`. Timeouts 5000 ms for the safety hook and 3000 ms for rtk.
- **Hook payload**: `{"hook_event_name": "PreToolUse", "tool_name": ..., "tool_input": ...}`. `shell`/`bash` map to `Bash {command}`, `patch` to `apply_patch {command: patchText}`, and `edit`/`write` (opencode V2 input field `path`, not V1 `filePath`) to `Edit`/`Write {file_path}`, with the path resolved against the project directory. Other tools are not sent.
- **Failure policy**: the safety step fails closed. A spawn error, timeout, non-zero exit or non-empty stdout blocks the call. The rtk step fails open.
- **Process handling**: asynchronous `execFile` without a shell, with `cwd` set to `context.location.directory` and the configured timeout. The safety payload goes to stdin, with an error listener on the child's stdin.
- **Agent models**: architect `anthropic/claude-fable-5-2#high`; qa and review `anthropic/claude-opus-5-5#high`; both researchers `anthropic/claude-opus-5-5#medium`. Each agent denies the `edit` action on `*`.

---

## Phase 1: Guarded opencode setup

**User stories**: 1–14, 16

### What to build
A developer who opens the repository in opencode gets the project skills, the five read-only subagents and the context-mode plugin. Every shell command, edit, write and patch goes through the same Python safety hook as Codex, before rtk rewrites shell commands. `./run.sh test` verifies the plugin and the hook, and the README explains the setup.

#### Step 1.1: Write failing test
- `test_pre_tool_use_policy.py` (existing tests, new parameters through `subTest`)
    - Denied edit targets (the renamed `test_denies_sensitive_apply_patch_targets`)
        - Happy path:
            - existing `apply_patch` case -> deny
            - `Edit {file_path: ".env"}` -> deny
            - `Write {file_path: "/etc/hosts"}` -> deny
        - Edge case, move target: `apply_patch` with `*** Update File: notes.md` and `*** Move to: .git/hooks/pre-commit` -> deny
    - Allowed edit targets (the renamed `test_allows_ordinary_apply_patch_targets`)
        - Happy path:
            - existing `apply_patch` case -> allow
            - `Write {file_path: "docs/GLOSSARY.md"}` -> allow
- `pre-tool-use.test.ts` (Node test runner, through `setup` with the fixture's fake context)
    - Blocked calls (one parameterized test, each rejects with the hook's reason)
        - `shell` `git reset --hard HEAD` -> rejects "hard git resets are blocked"
        - `bash` `rm -rf build` -> rejects "recursive forced deletion is blocked"
        - `write` `.env` -> rejects with the sensitive path reason
        - `edit` `<repo>/.git/config` (absolute) -> rejects with the sensitive path reason
        - `write` `/etc/hosts` -> rejects with the sensitive path reason
        - `patch` with `*** Delete File: .git/config` -> rejects with the sensitive path reason
        - Unhappy path, broken guard: `shell` `git status` with `safetyHookCommand` replaced by a command that exits with 1 -> rejects
        - Unhappy path, unreadable guard answer: `shell` `git status` with `safetyHookCommand` replaced by a command that prints `{}` and exits 0 -> rejects
        - Edge case, relative path outside the project: `write` `../<project folder name>-sibling/notes.md`, built from the fixture's directory -> rejects with "editing sensitive path is blocked: <absolute resolved path>"
        - Unhappy path, hanging guard: `shell` `git status` with `safetyHookCommand` replaced by a command that sleeps 2 s and `safetyHookTimeoutMilliseconds` set to 100 -> rejects
        - Unhappy path, unreadable input: `shell` with an input that has no `command` -> rejects
    - Allowed calls (one parameterized test)
        - `shell` `git status`, agent `build` -> resolves, `input.command` equals `--agent|build|git status`
        - `edit` `<repo>/docs/GLOSSARY.md` (absolute) -> resolves, input unchanged
        - `read` `.env` -> resolves, input unchanged
        - Unhappy path, broken rtk: `shell` `git status` with the rtk stub exiting 1 -> resolves, `input.command` equals `git status`
        - Edge case, no rewrite: `shell` `git status` with the rtk command replaced by one that prints `{}` -> resolves, `input.command` equals `git status`
    - Setup (one parameterized test)
        - Unhappy path: options without `rtkRewriteCommand` -> `setup` rejects
        - Unhappy path: `safetyHookTimeoutMilliseconds` set to `"5000"` -> `setup` rejects

**Run:** `python3 -m unittest discover --start-directory .codex/hooks --pattern 'test_*.py'` and `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`
**Expect:** FAIL (red)

#### Step 1.2: Implement minimal code
Extend the Python hook with the `Edit`/`Write` branch and the `Move to` target. Reuse the input reader and the patch denial path by giving them parameters instead of adding new functions. Write the pre-tool-use plugin and register it with its options in `.opencode/opencode.json`, followed by `context-mode`. Add the five agent files and the skills symlink. Add the plugin test to `run_test` in `run.sh`, and extend the rtk check in `setup_environment` with `rtk hook opencode --help`. Update the README: opencode in the intro and contents, Node 24 and opencode in the requirements, `@skill` instead of `/skill` in opencode, and that opencode MCP tool calls, including code that context-mode's `ctx_execute` runs, are not checked.

#### Step 1.3: Verify test passes
**Run:** The same test commands as in Step 1.1, then `./run.sh test`.
**Expect:** PASS (green)

#### Step 1.4: Aggressive refactor
- Plugin: one process helper for both commands. The mapping is a single lookup table, not a switch per tool, and no option is read twice.
- Plugin test: one parameterized blocked test and one parameterized allowed test. All context and option construction lives in the fixture.
- Python hook: `command_from`, `apply_patch_denial_reason` and `patch_paths` each end up with one clear purpose after the generalization, and `command_from` is removed if the generalized reader replaces it. Other functions stay as they are.
- Python tests: no duplicate cases between the patch and edit parameters.
- Agent files: frontmatter only differs from the Claude files where opencode needs it.

### Acceptance criteria
- [x] `./run.sh lint`, `./run.sh test` and `./run.sh build` pass.
- [x] Each new test fails once when its production line is broken, and passes again after the line is restored.
- [x] The plugin contains no literal command, path or timeout. All of them come from `.opencode/opencode.json`.
- [x] Codex calls with the tool names Codex sends today behave as before, except the approved `Move to` check.
- [x] The README lists the opencode files and requirements.

---

## Phase 2: Safety hook in Claude Code

**User stories**: 18–21

### What to build
Claude Code runs the same safety hook as Codex and opencode for every tool call, and a broken hook blocks the call. The hook takes over the path contract from the opencode plugin: it resolves `Edit`, `Write` and patch paths against the project directory that `run.sh safety-hook` passes, so absolute paths inside the project pass for all three tools and `..` paths that leave the project are denied.

#### Step 2.1: Write failing test
- `test_pre_tool_use_policy.py` (existing tests, new parameters; `run_hook` passes a fixed project directory argument)
    - Denied edit targets
        - `Edit {file_path: "<project>/.git/config"}` -> deny
        - Edge case, relative path that leaves the project: `apply_patch` with `*** Add File: ../outside.md` -> deny
    - Allowed edit targets
        - The existing `Write {file_path: "docs/GLOSSARY.md"}` case becomes `Write {file_path: "<project>/docs/GLOSSARY.md"}` -> allow
- `pre-tool-use.test.ts`: no new cases. The existing blocked and allowed cases must stay green after the plugin sends absolute paths.

**Run:** `./run.sh test`
**Expect:** FAIL (red)

#### Step 2.2: Implement minimal code
Give the hook a required project directory argument, and pass the git top level from `run.sh safety-hook`. Resolve edit and patch paths against it before the sensitive-path check. Make the plugin send the absolute resolved path and remove its own relative-path logic. Add the safety hook to `.claude/settings.json` with matcher `*`, the Codex command and timeout, and `onFailure: "block"`, next to the rtk hook. Update the README row of the safety hook.

#### Step 2.3: Verify test passes
**Run:** `./run.sh test`
**Expect:** PASS (green)

#### Step 2.4: Aggressive refactor
- Python hook: one function resolves a path against the project directory, and the bash and MCP rules stay unchanged.
- Plugin: no path logic beyond `resolve`.

### Acceptance criteria
- [x] `./run.sh lint`, `./run.sh test` and `./run.sh build` pass.
- [x] Each new test fails once when its production line is broken, and passes again after the line is restored.
- [x] In a running Claude Code session, `sudo -n true` and a `Write` outside the project are denied with the hook's reason, and an `Edit` of a project file succeeds.

---

## Phase 3: Tool-independent layout without context-mode

**User stories**: 15, 16, 17

### What to build
A project can keep any subset of `.claude`, `.codex` and `.opencode`. The safety hook and its tests move from `.codex/hooks` to a root `hooks` folder, `run.sh` runs only the hook tests and checks only that rtk is installed, and context-mode leaves the Codex configuration, the opencode configuration, `run.sh` and the README. The README names the command for the plugin tests.

#### Step 3.1: Write failing test
No new tests. The move and the removals change no behavior that a test observes, and the project rules forbid dedicated tests for a cleanup-only change. The existing hook and plugin tests must stay green from the new location.

#### Step 3.2: Implement minimal code
Move `.codex/hooks/pre_tool_use_policy.py` and its test to `hooks/` and point `run.sh` at them in the same step, because the live Claude Code hook fails closed. Remove the plugin test and the tool-specific rtk checks and the context-mode install from `run.sh`. Remove the context-mode MCP server and hooks from `.codex/config.toml` and the plugin entry from `.opencode/opencode.json`. Update the README.

#### Step 3.3: Verify test passes
**Run:** `./run.sh test` and `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`
**Expect:** PASS (green)

#### Step 3.4: Aggressive refactor
- `run.sh`: no references to `.claude`, `.codex` or `.opencode`.
- No remaining `context-mode` or `.codex/hooks` reference outside the docs history.

### Acceptance criteria
- [x] `./run.sh lint`, `./run.sh test`, `./run.sh build` and the plugin tests pass.
- [x] In a scratch copy without `.codex` and `.opencode`, `./run.sh test` passes and `./run.sh safety-hook` denies `sudo -n true`.
- [x] In the running Claude Code session, `sudo -n true` is denied and an `Edit` of a project file succeeds after the move.

# Manual verification
1. Install opencode 2.3.x and run `./run.sh setup-environment`. It reports that rtk is available.
2. Start opencode in the repository and run `opencode plugin list`. It lists `pre-tool-use` once, loaded without errors. Stop here and report if `pre-tool-use` is missing or listed twice.
3. Type `@` in the prompt. The skills `plan`, `implement`, `review` and the other repository skills appear. If a skill named `plan` exists in `~/.config/opencode/skills`, `@plan` loads the repository's version.
4. Ask opencode to run `git status`. The tool call shows the command `rtk git status`.
5. Ask opencode to run `git reset --hard HEAD`. The call fails with "hard git resets are blocked".
6. Ask opencode to create a file `.env` with any content. The call fails with "editing sensitive path is blocked: .env", and no `.env` exists afterwards.
7. Ask opencode to add a line to `docs/GLOSSARY.md`. The edit succeeds. Revert it afterwards.
8. Ask opencode to use the codebase-researcher-agent subagent for a question. It runs on Claude Opus 5.5 and answers. Ask it to edit a file, and it is refused. Repeat the question with the architect-agent subagent, which runs on Claude Fable 5.2.
9. Run `git status`. If opencode created cache files inside `.opencode`, they appear here and need a `.gitignore` entry.
10. Start Claude Code in the repository and ask it to run `sudo -n true`. The call fails with "sudo commands require explicit human approval outside this hook".
11. Ask Claude Code to add a line to `docs/GLOSSARY.md`. The edit succeeds. Revert it afterwards.
12. Ask Claude Code to write a file to `/tmp`. The call fails with "editing sensitive path is blocked".
13. Ask Claude Code to run `git status`. It runs as `rtk git status`.

# Task tracking
- [x] Step 1.1
- [x] Step 1.2
- [x] Step 1.3
- [x] Step 1.4
- [x] Step 2.1
- [x] Step 2.2
- [x] Step 2.3
- [x] Step 2.4
- [x] Step 3.1
- [x] Step 3.2
- [x] Step 3.3
- [x] Step 3.4

# Review findings:
- Step 1
  - A relative path outside the project has no test -> blocked case `../<project>-sibling/notes.md`
  - A guard answer that is not a deny decision has no test -> blocked case where the safety command prints `{}`
  - The opencode input field for `edit`/`write` is not named -> `path` stated in the payload decision
  - The refactor rule invites inlining unrelated hook functions -> limited to the generalized functions
  - The rtk `{}` answer has no test -> allowed case where the rtk command prints `{}`
  - The safety timeout and a missing input field have no test -> two blocked cases
  - Commands depend on the opencode process working directory -> `cwd` is the project directory for both commands
  - `setup` with a wrongly typed option has no test -> second parameter in the setup test
  - The context-mode `ctx_execute` gap is undocumented -> README note
- Implementation review
  - [x] The README claims that the hook blocks all paths outside the project, but relative `..` paths in patches pass -> README names absolute paths and the patch gap
  - [x] The README asks for opencode 2.3 or later, while the spec targets 2.3.x -> README says 2.3.x
