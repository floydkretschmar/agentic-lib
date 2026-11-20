#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import sys
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Any


DANGEROUS_COMMAND_PATTERNS = (
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "hard git resets are blocked"),
    (re.compile(r"\bgit\s+clean\s+-[^\s]*[fdx]"), "destructive git clean is blocked"),
    (
        re.compile(r"\bgit\s+(checkout|restore)\s+[^;\n]*\s--\s"),
        "destructive git checkout/restore is blocked",
    ),
    (
        re.compile(r"\b(curl|wget)\b[^|;\n]*\|\s*(sh|bash|zsh|python3?)\b"),
        "remote download piped to an interpreter is blocked",
    ),
    (re.compile(r"\bdd\b[^;\n]*\bof=/dev/"), "raw device writes are blocked"),
    (re.compile(r"\b(mkfs|shutdown|reboot|poweroff|halt)\b"), "system-level destructive command is blocked"),
    (
        re.compile(r"(^|[;&|\n]\s*)sudo\b"),
        "sudo commands require explicit human approval outside this hook",
    ),
)

EDIT_PATH_FIELD_BY_TOOL = {"Edit": "file_path", "MultiEdit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}
SENSITIVE_PATH_PARTS = {".git", ".ssh"}
SENSITIVE_FILE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
SENSITIVE_FILE_EXTENSIONS = (".pem", ".key", ".p12", ".pfx")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            separators=(",", ":"),
        )
    )


def load_payload() -> dict[str, Any] | None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def string_field_from(tool_input: Any, field_name: str) -> str:
    if isinstance(tool_input, dict) and isinstance(tool_input.get(field_name), str):
        return tool_input[field_name]
    return ""


def has_sensitive_name(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return name in SENSITIVE_FILE_NAMES or name.endswith(SENSITIVE_FILE_EXTENSIONS)


def is_sensitive_path(path: str) -> bool:
    clean = path.strip().strip("\"'")
    if not clean:
        return False
    parts = {part.lower() for part in PurePosixPath(clean).parts}
    return clean.startswith("/") or bool(parts & SENSITIVE_PATH_PARTS) or has_sensitive_name(clean)


def patch_paths(command: str) -> list[str]:
    paths = []
    for line in command.split("\n"):
        match = re.match(r"\*\*\* (Add File|Delete File|Update File|Move to): (.+)$", line.strip())
        if match:
            paths.append(match.group(2))
    return paths


def flattened_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from flattened_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from flattened_strings(nested)


def bash_denial_reason(command: str) -> str | None:
    lowered = command.lower()
    for pattern, reason in DANGEROUS_COMMAND_PATTERNS:
        if pattern.search(lowered):
            return reason

    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    if tokens and tokens[0] == "rm" and any(
        token.startswith("-") and "r" in token and "f" in token for token in tokens[1:]
    ):
        return "recursive forced deletion is blocked"

    if tokens and tokens[0] in {"rm", "unlink", "rmdir"} and any(
        is_sensitive_path(token) for token in tokens[1:] if not token.startswith("-")
    ):
        return "deleting sensitive or absolute paths is blocked"

    return None


def edit_denial_reason(paths: list[str], working_directory: str, project_directory: str) -> str | None:
    if not os.path.isabs(working_directory) or not paths or not all(paths):
        return "editing needs an absolute working directory and a path in the hook input"
    real_project_directory = os.path.realpath(project_directory)
    for path in paths:
        target_path = os.path.realpath(os.path.join(working_directory, path))
        project_path = os.path.relpath(target_path, real_project_directory)
        if project_path == ".." or project_path.startswith("../"):
            return f"editing outside the project is blocked: {target_path}"
        if is_sensitive_path(project_path) or has_sensitive_name(path):
            return f"editing sensitive path is blocked: {project_path}"
    return None


def mcp_denial_reason(tool_name: str, tool_input: Any) -> str | None:
    destructive_tool = re.search(
        r"(^|__)(delete|remove|rm|rmdir|unlink|write|move|rename)($|_|__)",
        tool_name,
    )
    if destructive_tool and any(is_sensitive_path(value) for value in flattened_strings(tool_input)):
        return "MCP tool targets a sensitive or absolute path"
    return None


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("project_directory")
    project_directory = argument_parser.parse_args().project_directory

    payload = load_payload()
    if payload is None:
        deny("Malformed PreToolUse hook input")
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input")
    working_directory = string_field_from(payload, "cwd")

    reason = None
    if tool_name == "Bash":
        reason = bash_denial_reason(string_field_from(tool_input, "command"))
    elif tool_name == "apply_patch":
        reason = edit_denial_reason(patch_paths(string_field_from(tool_input, "command")), working_directory, project_directory)
    elif tool_name in EDIT_PATH_FIELD_BY_TOOL:
        edited_path = string_field_from(tool_input, EDIT_PATH_FIELD_BY_TOOL[tool_name])
        reason = edit_denial_reason([edited_path], working_directory, project_directory)
    elif tool_name.startswith("mcp__"):
        reason = mcp_denial_reason(tool_name, tool_input)

    if reason:
        deny(reason)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
