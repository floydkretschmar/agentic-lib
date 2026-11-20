# agentic-lib

A shared agent setup for Claude Code, Codex and opencode. All three tools read the same project rules, skills and subagents, so a project gets one workflow regardless of which agent runs it.

## Contents

| Path | What it holds |
| --- | --- |
| `AGENTS.md` | Operating principles and the coding, testing and naming rules. `CLAUDE.md` is a symlink to it. |
| `skills/` | The skills. `.claude/skills`, `.codex/skills` and `.opencode/skills` are symlinks to this folder. |
| `.claude/agents/`, `.codex/agents/`, `.opencode/agents/` | The same five subagents, once in each tool's format. |
| `hooks/pre_tool_use_policy.py` | Safety hook for Claude Code, Codex and opencode. `run.sh safety-hook` runs it, so it works without any tool folder. It blocks `git reset --hard`, `git clean`, `rm -rf`, `sudo`, `curl \| sh` and edits to `.git`, `.ssh`, `.env`, key files and paths outside the project. It judges an edit by the files it touches, from the directory the tool works in: it denies a path that tools resolve differently through a symlink, a touched file outside the project or in its `.git` storage, and a sensitive name in any case. It judges a shell command one simple command at a time. `.claude/settings.json` runs it for every Claude Code tool call and blocks the call when the hook fails. Because the hook denies paths outside the project, the Claude Code `Write` and `Edit` tools cannot write outside it, for example to the session scratchpad or to `~/.claude/plans`. |
| `.opencode/opencode.json` | The opencode configuration. It loads the `pre-tool-use` plugin with its commands and timeouts. |
| `.opencode/plugins/pre-tool-use/` | opencode plugin that sends each shell command, edit, write and patch to the safety hook and then rewrites allowed shell commands with `rtk hook opencode`. It blocks the call when the safety hook fails, and runs the original command when rtk fails. It does not check MCP tool calls. `./run.sh test` does not run its tests, so run them with `node --test .opencode/plugins/pre-tool-use/pre-tool-use.test.ts`. |
| `docs/` | Templates for the glossary and ADRs, and the GitHub issue tracker conventions. |
| `run.sh` | The one entry point for `test`, `lint`, `format`, `build`, `safety-hook` and `setup-environment`. |

## Workflow

The usual order is `/plan`, then `/implement`, then `/review`. In opencode, type `@plan` instead of `/plan`, and the same for the other skills.

- `/plan` asks about the intent, explores the code and the web with researcher subagents, has architect subagents propose designs, and writes a spec to `docs/specs/` and a phased implementation plan to `docs/implementation-plans/`. A review subagent checks both before the plan is final.
- `/implement` executes the plan one phase at a time with `/tdd`.
- `/review` reviews the diff against a given ref, the spec and the project rules.

The other skills:

- `/tdd` runs the red-green-refactor loop.
- `/interview` questions the user one decision at a time until both sides agree.
- `/research` collects facts from primary sources into a cited Markdown file.
- `/prototype` builds throwaway code to test a state model or a UI idea.
- `/wayfinder` splits work too large for one session into a map issue with child tickets on GitHub. Only the user can invoke it.
- `/unslop` removes AI writing patterns from text.
- `/frontend-design` guides UI work.

The subagents are `architect-agent`, `codebase-researcher-agent`, `web-researcher-agent`, `review-agent` and `qa-agent`. All of them are read-only.

## Setup

Requirements: [rtk](https://www.rtk-ai.app/docs/getting-started/installation/) 1.2.1 or later, Python 3 and the `gh` CLI. Claude Code needs version 2.1.295 or later. opencode needs version 2.3.x, and its plugin tests need Node 24.

1. Copy the files into the root of your project. Leave out `.claude`, `.codex` or `.opencode` for each tool that you do not use.
2. Run `./run.sh setup-environment`. It checks that `rtk` is installed.
3. Replace the bodies of `run_test`, `run_lint`, `run_format` and `run_build` in `run.sh` with your project's commands. The agents treat a task as done only when `./run.sh lint`, `./run.sh test` and `./run.sh build` pass.
4. Fill in `docs/GLOSSARY.md`, and record decisions as ADRs in `docs/adr/` based on `0000-adr-template.md`.
5. Set the pull request triage option in `docs/ISSUE-TRACKER.md`.
