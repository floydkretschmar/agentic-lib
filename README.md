# agentic-lib

A shared agent setup for Claude Code, Codex and opencode. All three tools read the same project rules, skills and subagents, so a project gets one workflow regardless of which agent runs it.

You copy the files into a project and point `run.sh` at the project's test, lint and build commands. The agent then plans a change as a spec and a phased plan, implements it test-first, and reviews it with separate subagents.

## What you get

- Project rules in `AGENTS.md`. They cover operating principles, forbidden actions, and the coding, testing and naming conventions. Claude Code reads them through the `CLAUDE.md` symlink.
- Ten skills in `skills/`, linked into each tool's folder.
- Five subagents, written once in each tool's format.
- A sandbox or permission configuration for each tool, and one safety hook that all three tools run before a tool call.
- `run.sh`, the one entry point for `test`, `lint`, `format`, `build`, `safety-hook` and `setup-environment`.

## Requirements

Install only the tools that you use.

| Tool | Version | Notes |
| --- | --- | --- |
| [rtk](https://www.rtk-ai.app/docs/getting-started/installation/) | 1.2.1 or later | Rewrites shell commands so that their output costs fewer tokens. |
| Python | 3.10 or later | Runs the safety hook. |
| `gh` CLI | any | The skills use it for issues and pull requests. |
| Claude Code | 2.1.314 or later | On Linux, the sandbox needs `bubblewrap` and `socat`. Without them, Claude Code refuses to start in the project. |
| Codex | any | On Linux, the sandbox needs `bubblewrap`. |
| opencode | 2.3.x | The plugin tests need Node 24. |

## Setup

1. Copy the files into the root of your project and keep the symlinks, for example with `cp -a`. Leave out `.claude`, `.codex` or `.opencode` for each tool that you do not use.
2. Run `./run.sh setup-environment`. It checks that `rtk` is installed.
3. Replace the bodies of `run_test`, `run_lint`, `run_format` and `run_build` in `run.sh` with your project's commands. The agents treat a task as done only when `./run.sh lint`, `./run.sh test` and `./run.sh build` pass.
4. Fill in `docs/GLOSSARY.md`, and record decisions as ADRs in `docs/adr/` based on `0000-adr-template.md`.
5. Set the pull request triage option in `docs/ISSUE-TRACKER.md`.
6. If you use Claude Code, keep the sandbox placeholder entries from this repository's `.gitignore` in your own. The Claude Code limits below explain why.

## Workflow

The usual order is `/plan`, then `/implement`, then `/review`. In opencode, type `@plan` instead of `/plan`, and the same for the other skills.

| Skill | What it does |
| --- | --- |
| `/plan` | Asks about the intent and explores the code and the web with researcher subagents. Architect subagents propose designs. The skill writes a spec to `docs/specs/` and a phased implementation plan to `docs/implementation-plans/`, and a review subagent checks both before the plan is final. |
| `/implement` | Executes the plan one phase at a time with `/tdd` and commits after each phase. It ends with `/review` and repeats until the review passes. |
| `/review` | Reviews the diff against a ref that you give, the spec and the project rules. A review subagent reads the code while a QA subagent tests the running application. |
| `/tdd` | Runs the red-green-refactor loop in vertical slices. |
| `/interview` | Questions you one decision at a time until both sides agree. |
| `/research` | Collects facts from primary sources into a cited Markdown file. |
| `/prototype` | Builds throwaway code that tests a state model in a terminal app, or compares UI variants on one route. |
| `/wayfinder` | Splits work too large for one session into a map issue with child tickets on GitHub. Only you can invoke it. |
| `/unslop` | Removes AI writing patterns from text. `AGENTS.md` tells the agent to apply it to everything it writes. |
| `/frontend-design` | Guides UI work. It has its own license in `skills/frontend-design/LICENSE.txt`. |

## Subagents

| Subagent | Job | Claude Code and opencode | Codex |
| --- | --- | --- | --- |
| `architect-agent` | Designs implementation approaches and phase breakdowns. | Fable, high effort | `gpt-6.2-astra`, high effort |
| `codebase-researcher-agent` | Traces execution paths and cites files and symbols. | Opus, medium effort | `gpt-6.2-sol`, medium effort |
| `web-researcher-agent` | Gathers evidence from web pages and API documentation. | Opus, medium effort | `gpt-6.2-sol`, medium effort |
| `review-agent` | Reviews code or a plan against its spec and returns graded findings with a verdict. | Opus, high effort | `gpt-6.2-sol`, high effort |
| `qa-agent` | Operates the running application like a user and returns a pass or fail verdict with evidence. | Opus, high effort | `gpt-6.2-sol`, high effort |

The subagents report and do not edit files. Claude Code and opencode take the edit tools away from them. The Codex definitions have no such setting, so in Codex only the agents' instructions keep them from editing.

## Safety

Each tool's sandbox and permission rules are the security boundary. The safety hook is a best-effort check on top of them, and a command that it does not recognize passes.

### Sandboxes and permission rules

| Tool | Configuration | Shell commands | File edits |
| --- | --- | --- | --- |
| Claude Code | `.claude/settings.json` | Run in the Bash sandbox. Claude Code refuses to start when the sandbox is unavailable, and no command runs outside it. | The file tools cannot write outside the project or to `.git`, `.ssh`, `.env` and key files. |
| Codex | `.codex/config.toml` | Run in a permission profile that extends the workspace sandbox. | The profile denies `.ssh`, `.env` and key files, for reading too. |
| opencode | `.opencode/opencode.json` | opencode has no sandbox, so shell commands run with your rights. | The rules deny edits outside the project and to `.git`, `.ssh`, `.env` and key files. |

Key files are `id_rsa`, `id_ed25519` and files that end in `.pem`, `.key`, `.p12` or `.pfx`. The `.env` rules also cover `.env.local` and `.env.production`.

### Safety hook

`hooks/pre_tool_use_policy.py` runs through `./run.sh safety-hook` before a tool call. It blocks the following shell commands:

- `git reset --hard`, `git clean` with `-f`, `-d` or `-x`, and `git checkout` or `git restore` with a ` -- ` path separator
- `rm` with the recursive and force flags, and `rm`, `unlink` or `rmdir` on an absolute or sensitive path
- `sudo`
- `curl` or `wget` piped to a shell or to Python
- `dd` to a device, `mkfs`, `shutdown`, `reboot`, `poweroff` and `halt`

It also blocks edits, writes and patches that resolve outside the project or to a sensitive path, and MCP tools with a destructive name, such as `delete` or `write`, when an argument is an absolute or sensitive path.

Claude Code and the opencode plugin block the tool call when the hook itself fails. In opencode, the plugin in `.opencode/plugins/pre-tool-use/` sends the command that the model wrote to the hook first and then rewrites it with `rtk hook opencode`. When rtk fails, the plugin runs the original command.

### Limits to know

Claude Code:

- Shell commands cannot change `skills/` or `.claude/agents`. Edit them with the file tools.
- The sandbox sends shell network traffic through its filtering proxy and keeps home-folder caches such as `~/.npm` read-only for shell commands.
- The sandbox mounts placeholder entries such as `.bashrc` and `.mcp.json` into the project. Keep the matching entries in `.gitignore`, or `git add -A` fails. Those entries also hide a real shared `.mcp.json` or `.vscode` folder.

Codex:

- Codex loads `.codex/config.toml` only for trusted projects.
- A user config that sets `sandbox_mode` replaces the project's permission profile.
- On Linux, the profile covers only the files that exist when Codex starts.

opencode:

- The `external_directory` rule also denies reads and shell commands outside the project.
- The plugin does not send MCP tool calls to the safety hook.

## Repository layout

| Path | What it holds |
| --- | --- |
| `AGENTS.md` | The project rules. `CLAUDE.md` is a symlink to it. |
| `skills/` | The skills. `.claude/skills`, `.codex/skills` and `.opencode/skills` are symlinks to this folder. |
| `.claude/agents/`, `.codex/agents/`, `.opencode/agents/` | The five subagents in each tool's format. |
| `.claude/settings.json`, `.codex/config.toml`, `.opencode/opencode.json` | Each tool's sandbox or permission rules and its hook registration. |
| `.opencode/plugins/pre-tool-use/` | The opencode plugin that calls the safety hook and rtk. Its commands and timeouts live in `.opencode/opencode.json`. |
| `hooks/` | The safety hook and its tests. |
| `docs/` | Templates for the glossary and ADRs, and the GitHub issue tracker conventions. `/plan` adds `docs/specs/` and `docs/implementation-plans/`. |
| `run.sh` | The entry point for tests, lint, format, build, the safety hook and the environment check. |

## Working on agentic-lib itself

`./run.sh test` runs the safety hook tests. It does not run the plugin tests, so run them with Node 24:

```sh
node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts
```

`./run.sh lint`, `./run.sh format` and `./run.sh build` do nothing in this repository. They are the placeholders that step 3 of the setup replaces.

A change to a subagent has to go into all three agent folders, because each tool has its own copy.
