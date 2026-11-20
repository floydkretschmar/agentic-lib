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

---

## Phase 5: Robust edit and shell rules (superseded by Phase 6)

**User stories**: 26, 27

### What to build
The hook judges an edit by the locations it touches under the five rules of the spec's path contract, instead of adding one candidate spelling per finding: one meaning or deny, target and entry inside the project and outside the `.git` storage, sensitive names in any case, malformed input denied without errors, and Codex header parsing. Shell commands are judged per simple command.

#### Step 5.1: Write failing test
- `test_pre_tool_use_policy.py`
    - New parameterized test: every spelling of an edit target gets the decision of its plain spelling. Targets: `docs/GLOSSARY.md`, a new file in a new folder, `docs/settings.txt` (allowed); `.env`, `.ENV`, `.git/config`, the `.git` storage folder's `config`, `docs/.ssh/authorized_keys`, `docs/.env.local`, `docs/outside-notes.md` (denied). Spellings: relative, `./`, `docs/..`, from `cwd` `docs`, absolute, through each project symlink, through the link to `docs`, from a `cwd` outside the project. Shapes: `Write` and a patch delete.
    - Denied edit targets: replace the spelling cases that the new test covers; add a path where `..` follows a symlink and stays inside the project, a tab, a NUL byte and a lone surrogate in a path.
    - Shell commands: denied `sudo` after a line break, `rm -rf` after `&&`, `rm --recursive --force`, `rm -r -f`, `rm` behind `env FOO=1`, `/bin/rm -rf`; allowed a pipe of harmless commands.

**Run:** `./run.sh test`
**Expect:** FAIL (red)

#### Step 5.2: Implement minimal code
Replace the candidate list with one function per rule. Write the new hook next to the live one and switch it in one command that verifies it and restores the old hook on failure, because the live Claude Code hook fails closed.

#### Step 5.3: Verify test passes
**Run:** `./run.sh test` and `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`
**Expect:** PASS (green)

#### Step 5.4: Aggressive refactor
- Hook: no candidate enumeration left; one function per rule.
- Tests: no case that the spelling test already covers.

### Acceptance criteria
- [x] `./run.sh lint`, `./run.sh test`, `./run.sh build` and the plugin tests pass.
- [x] Each rule fails at least one case when its production line is broken.
- [x] In the running Claude Code session, `sudo -n true` is denied and an `Edit` of a project file succeeds.

---

## Phase 6: Native sandboxes and a small hook

**User stories**: 25, 26, 27

### What to build
Phase 5 tried to make the text-matching hook a security boundary and grew it into a shell parser of about 600 lines. The user rejected that approach. Each tool's own sandbox and permission rules become the boundary, and the hook shrinks back to a small best-effort tripwire.

#### Step 6.1: Write failing test
- `test_pre_tool_use_policy.py`: a compact suite for the tripwire. The command patterns of `main` with `sudo` after a line break; edits through an outside symlink, sensitive names in any case, `MultiEdit`, `NotebookEdit`, patches with `Move to` or without header paths, edits without a path or without `cwd`, invalid UTF-8; edits through a symlink to the project are allowed.

#### Step 6.2: Implement minimal code
Replace the Phase 5 hook with `main`'s hook plus one edit-path check: the path joined to the absolute `cwd` and resolved through symlinks must lie inside the project, and neither its project path nor its written file name may be sensitive. Add the Codex permission profile, the opencode permission rules, and the Claude Code sandbox and deny rules.

#### Step 6.3: Verify test passes
**Run:** `./run.sh test` and `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`
**Expect:** PASS (green)

#### Step 6.4: Aggressive refactor
- The hook stays close to `main`; every check is proven by breaking its line once.

### Acceptance criteria
- [x] `./run.sh lint`, `./run.sh test`, `./run.sh build` and the plugin tests pass.
- [x] `.claude/settings.json`, `.codex/config.toml` and `.opencode/opencode.json` parse.
- [x] In a running Claude Code session with the sandbox on, a shell write outside the project fails, an `Edit` of `.env` is denied by a deny rule, and an `Edit` of a project file succeeds.

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
14. Install `bubblewrap` and `socat`, start Claude Code, and ask it to run `touch ~/sandbox-probe`. The command fails with a read-only file system error.
15. Start Codex in the repository and ask it to create `.env`. The sandbox refuses the write.
16. In opencode, ask for a file outside the project. The `external_directory` rule denies it.

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
- [x] Step 5.1
- [x] Step 5.2
- [x] Step 5.3
- [x] Step 5.4
- [x] Step 6.1
- [x] Step 6.2
- [x] Step 6.3
- [x] Step 6.4

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
- Implementation review after the header fix
  - [x] Removing the entry check left a `.env` symlink unprotected when the path reaches the project through another spelling, such as a second project symlink -> the entry path is a candidate again; new denied case through a second project symlink
  - [x] An edit payload without its path field was allowed -> deny it like a payload without `cwd`; new denied case
- Manual regression test after the entry fix
  - [x] A `.git` or `.ssh` folder that is a symlink stays unprotected when the path reaches the project through a third spelling, because the name check compares only against the given and the resolved project directory -> find the first prefix of the written path that resolves to the project and check the names after it; new denied cases through a second project symlink, through a link to `docs`, and for `..` that lands on a file symlink pointing outside
- Implementation review and manual regression test after the name check fix
  - [x] A symlinked `.git` or `.ssh` folder inside a project subfolder stays editable through a link to that subfolder, because the name check starts only at a prefix that resolves to the project root -> start at the first prefix that resolves anywhere inside the project, and prepend that prefix's project path; new denied case through the link to `docs`. This covers the entry check, so it is removed
- Implementation review and manual regression test after the prefix extension
  - [x] Removing the entry check let patch deletes and moves of a symlink entry through, such as a symlink to the project or a dotfile link outside it, because both resolved paths land on the in-project target -> restore the entry check; new denied case that deletes the project symlink
  - [x] A relative `cwd` is resolved against the hook process's folder -> deny an edit payload whose `cwd` is not absolute, which also covers a missing `cwd`; new denied case with a relative `cwd`
- Implementation review after the entry restore
  - [x] The entry check uses only the `..`-first spelling, so a patch delete through a project symlink and `..` can unlink a symlink outside the project in the kernel order -> build the entry from the raw and the `..`-first spelling; new denied case that deletes `outside-link/../project-link`
- Implementation review and differential test of Phase 5, fixed in one round
  - [x] Shell: wrappers with options, keywords, braces, leading redirections, `find -exec` and `xargs` hid `sudo` and `rm`; quoted separators cut commands; quoted prose, heredoc bodies and comments were falsely denied; abbreviated long options, line continuations and `--` were mishandled -> a shell reader that honors quotes, escapes, continuations, comments, substitutions and heredocs, and a rule that judges every word that names `sudo`, `rm`, `unlink` or `rmdir` with its following arguments parsed like GNU options; `sh -c`, `bash -c` and `eval` arguments and heredocs passed to a shell are judged as commands; patches in heredocs or words are judged with the patch rules; unbalanced quotes are denied
  - [x] Paths: a patch without a header path passed; a `.git` gitdir file was not resolved; header trimming removed characters that Codex keeps; non-ASCII spaces were denied as control characters; invalid UTF-8 and deep JSON crashed the hook; `~` paths were judged inside the project; storage comparison ignored case -> deny patches without paths, resolve `gitdir:`, trim with Rust's whitespace set, deny only Unicode categories Cc and Cs, deny undecodable input as malformed, deny `~` paths, compare the storage without regard to case
- Implementation review and differential test of the shell reader, fixed in one round
  - [x] Reader fidelity: continuations in comments and quoted heredocs, `<<\EOF` and `<<E"OF"` delimiters, substitutions in unquoted heredoc bodies, here-strings, `$'…'` and `$"…"` quotes, redirection operators with `&` and `|`, arithmetic `<<`, and substitution boundaries across heredocs -> continuations and comments handled like bash, delimiters unquoted like bash, unquoted bodies scanned for substitutions, unterminated heredocs judged as commands, ANSI-C quotes decoded, redirections kept in their word, a nested reader finds the end of `$(…)`
  - [x] Shells fed indirectly (`echo … | bash`, `cat <<EOF | sh`, `bash -c "$(cat <<EOF…)"`, `env -S`), zsh `=sudo`, `git` with global options, `git checkout -- .`, downloads run by any interpreter, `rm ..` and `rm ~/x` -> quoted text and heredocs count as commands when a shell or `eval` runs, `env -S` arguments are commands, program names drop a leading `=` or `<`, the former regex patterns became word rules
  - [x] False denials of the commit idiom with an apostrophe, patch-marker searches, `grep sudo`, and `rm … 2> /dev/null` -> nested substitution reader, patch rules only for texts with header paths, read-only programs whose words are data, redirections dropped from arguments
  - [x] `MultiEdit` was unchecked -> mapped to `file_path`
