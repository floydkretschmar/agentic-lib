# Implementation plan: opencode support

> Source spec: docs/specs/2026-11-20-opencode-support.md

## Architectural decisions

Durable decisions that apply across all phases:

- **Layout**: `.opencode/opencode.json`, `.opencode/plugins/pre-tool-use/{index.ts,pre-tool-use.test.ts,pre-tool-use.fixture.ts}`, `.opencode/agents/<name>.md`, `.opencode/skills -> ../skills`.
- **Plugin contract**: default export `{ id: "pre-tool-use", setup(context) }`. It reads the required options `safetyHookCommand` (argument array), `safetyHookTimeoutMilliseconds`, `rtkRewriteCommand` (argument array) and `rtkRewriteTimeoutMilliseconds` from `context.options`, and the project directory from `context.location.directory`. It registers its callback with `context.tool.hook("execute.before", callback)` and reads `event.tool`, `event.agent` and the mutable `event.input`. Configured in `.opencode/opencode.json` as the only plugin, `{ "package": "./plugins/pre-tool-use", "options": {...} }`.
- **Safety command**: `["sh", "-c", "\"$(git rev-parse --show-toplevel)/run.sh\" safety-hook"]`, the same command string as in `.codex/config.toml`. Timeouts 5000 ms for the safety hook and 3000 ms for rtk.
- **Hook payload**: `{"hook_event_name": "PreToolUse", "tool_name": ..., "tool_input": ...}`. `shell`/`bash` map to `Bash {command}`, `patch` to `apply_patch {command: patchText}`, and `edit`/`write` (opencode V2 input field `path`, not V1 `filePath`) to `Edit`/`Write {file_path}`, with the path as opencode sent it. Every payload carries the location directory as `cwd`. Other tools are not sent.
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

---

## Phase 4: Path decisions from the final review

**User stories**: 22–25

### What to build
The hook checks `NotebookEdit`, follows symlinks, and resolves relative paths against the `cwd` that each tool sends. The opencode plugin sends its location directory as `cwd` and drops its own path resolution. `run.sh safety-hook` takes the project directory from its own location, and Claude Code calls it through `$CLAUDE_PROJECT_DIR`.

#### Step 4.1: Write failing test
- `test_pre_tool_use_policy.py` (existing tests, new parameters; the project directory becomes a real temporary folder with a symlink to an outside folder and a symlink to the project)
    - Denied edit targets
        - `NotebookEdit {notebook_path: "<outside>/notes.ipynb"}` -> deny
        - `Write {file_path: "<project>/outside-link/notes.md"}` -> deny
        - Unhappy path: `Write` with a payload that has no `cwd` -> deny
    - Allowed edit targets
        - The absolute `Write` case goes through the symlink to the project -> allow
        - `apply_patch` updating `../README.md` with `cwd` `<project>/docs` -> allow
- `pre-tool-use.test.ts`: no new cases. The existing `docs` case covers the plugin's `cwd`.

**Run:** `./run.sh test` and `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`
**Expect:** FAIL (red)

#### Step 4.2: Implement minimal code
Map `Edit`, `Write` and `NotebookEdit` to their path field in the hook. Resolve paths against the payload `cwd` with `os.path.realpath` for the path and the project directory, and deny an edit payload without `cwd`. Send `cwd` from the plugin and remove its `resolve`. Take the project directory in `run.sh safety-hook` from the folder of `run.sh`, and call `"$CLAUDE_PROJECT_DIR/run.sh" safety-hook` from `.claude/settings.json`. Apply the hook and `run.sh` changes in one step, because the live Claude Code hook fails closed.

#### Step 4.3: Verify test passes
**Run:** `./run.sh test` and `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`
**Expect:** PASS (green)

#### Step 4.4: Aggressive refactor
- Plugin: no path logic and no `inputIsPath` flag.
- Hook: one path function with one purpose.

### Acceptance criteria
- [x] `./run.sh lint`, `./run.sh test`, `./run.sh build` and the plugin tests pass.
- [x] Each new test fails once when its production line is broken.
- [x] In the running Claude Code session, `sudo -n true` is denied and an `Edit` of a project file succeeds.
- [x] The Claude Code hook command works from a folder outside the repository.

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
- [x] Step 4.1
- [x] Step 4.2
- [x] Step 4.3
- [x] Step 4.4

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
- Implementation review after Phase 3
  - [x] The plugin's `resolve` against the plugin directory has no failing test -> allowed case with the plugin directory `docs` and `edit ../README.md`
  - [x] No test proves that the safety hook judges the command before rtk rewrites it -> the blocked hard-reset case uses an rtk command that answers `git status`
  - [x] Story 21 has no test for an absolute in-project patch path -> the allowed patch case also updates an absolute in-project path
  - [x] The README does not say that Claude Code `Write` and `Edit` outside the project are denied -> README note
  - [x] The plugin writes `event.input.command` instead of the mapped input field -> use the mapping's field
  - [x] The fixture commands used as rtk lack the `--` separator, so Node rejects `--agent` and the `{}` case only tested an rtk failure -> `--` added
- Implementation review after Phase 4
  - [x] A `.env` that is a symlink to a file with an ordinary name can be overwritten, because the hook judges only the resolved target -> also check the path name as the tool wrote it; the test project gets a `.env` symlink, so the existing `Edit .env` case covers it
  - [x] `deep/../../x` through an in-project symlink that points deeper is allowed, although opencode resolves `..` before symlinks and writes outside the project -> judge both the kernel resolution and the `..`-first resolution; new denied cases for both directions
  - [x] `run.sh` finds the project with git in `run_test` and with its own folder in `safety_hook`, and `cd` breaks under `CDPATH` -> one project directory from the folder of `run.sh`, with `CDPATH` cleared
- Implementation review after the path fix
  - [x] The hook strips quotes and whitespace before it resolves an edit path, so it judges another path than the tool writes -> judge the raw path; new denied cases for a leading quote, a trailing quote and a patch header with trailing spaces, plus a file symlink that points outside
  - [x] The written-name check counts folders above the project, so a project under a folder named `.ssh` or `.git` cannot be edited through absolute paths -> judge the entry itself (parent folder with symlinks followed, plus its own name) relative to the project instead of the written text; the test project moves under a folder named `.ssh`
  - [x] The plan's durable payload decision still says the plugin resolves paths -> raw path and `cwd`
- Implementation review after the redesign
  - [x] Codex trims patch header lines, so a padded header through a symlink and an indented header are judged as other paths than Codex writes -> parse headers like Codex: split on line feeds only and trim each line; new denied cases for a padded header through the outside symlink, an indented header and a carriage return inside a header path
  - [x] A `.git` or `.ssh` folder that is itself a symlink to a folder inside the project loses its name once the parent folder is resolved -> also judge the path with `..` collapsed and no symlinks followed, relative to the project; the test project's `.git` becomes such a symlink, plus a `.git/config` case through the project symlink. This check makes the separate entry check redundant, so it is removed
