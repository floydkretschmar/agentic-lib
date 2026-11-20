# agentic-lib

A shared agent setup for Claude Code and Codex. Both tools read the same project rules, skills and subagents, so a project gets one workflow regardless of which agent runs it.

## Contents

| Path | What it holds |
| --- | --- |
| `AGENTS.md` | Operating principles and the coding, testing and naming rules. `CLAUDE.md` is a symlink to it. |
| `skills/` | The skills. `.claude/skills` and `.codex/skills` are symlinks to this folder. |
| `.claude/agents/`, `.codex/agents/` | The same five subagents, once in each tool's format. |
| `.codex/hooks/pre_tool_use_policy.py` | Safety hook for Codex. It blocks `git reset --hard`, `git clean`, `rm -rf`, `sudo`, `curl \| sh` and edits to `.git`, `.ssh`, `.env` and key files. |
| `docs/` | Templates for the glossary and ADRs, and the GitHub issue tracker conventions. |
| `run.sh` | The one entry point for `test`, `lint`, `format`, `build`, `safety-hook` and `setup-environment`. |

## Workflow

The usual order is `/plan`, then `/implement`, then `/review`.

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

Requirements: [rtk](https://www.rtk-ai.app/docs/getting-started/installation/), Python 3, the `gh` CLI, and npm for `context-mode`.

1. Copy the files into the root of your project.
2. Run `./run.sh setup-environment`. It checks for `rtk` and installs `context-mode` with npm.
3. Replace the bodies of `run_test`, `run_lint`, `run_format` and `run_build` in `run.sh` with your project's commands. The agents treat a task as done only when `./run.sh lint`, `./run.sh test` and `./run.sh build` pass.
4. Fill in `docs/GLOSSARY.md`, and record decisions as ADRs in `docs/adr/` based on `0000-adr-template.md`.
5. Set the pull request triage option in `docs/ISSUE-TRACKER.md`.
