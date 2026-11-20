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
        re.compile(r"(^|[;&|]\s*)sudo\b"),
        "sudo commands require explicit human approval outside this hook",
    ),
)

EDIT_PATH_FIELD_BY_TOOL = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}
SENSITIVE_PATH_PARTS = {".git", ".ssh"}
SENSITIVE_FILE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}


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
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def string_field_from(tool_input: Any, field_name: str) -> str:
    if isinstance(tool_input, dict) and isinstance(tool_input.get(field_name), str):
        return tool_input[field_name]
    return ""


def is_sensitive_path(path: str) -> bool:
    clean = path.strip().strip("\"'")
    if not clean:
        return False

    parts = PurePosixPath(clean).parts
    name = PurePosixPath(clean).name
    return (
        clean.startswith("/")
        or any(part in SENSITIVE_PATH_PARTS for part in parts)
        or name in SENSITIVE_FILE_NAMES
        or name.endswith((".pem", ".key", ".p12", ".pfx"))
    )


def is_outside_project(project_relative_path: str) -> bool:
    return project_relative_path == ".." or project_relative_path.startswith("../")


def project_path_for(resolved_path: str, project_directory: str) -> str:
    project_relative_path = os.path.relpath(resolved_path, os.path.realpath(project_directory))
    if is_outside_project(project_relative_path):
        return resolved_path
    return project_relative_path


def lexical_project_paths_for(lexical_path: str, project_directory: str) -> list[str]:
    real_project_directory = os.path.realpath(project_directory)
    path_parts = PurePosixPath(lexical_path).parts
    for part_count in range(1, len(path_parts) + 1):
        prefix_project_path = os.path.relpath(os.path.realpath(PurePosixPath(*path_parts[:part_count])), real_project_directory)
        if not is_outside_project(prefix_project_path):
            return [str(PurePosixPath(prefix_project_path, *path_parts[part_count:]))]
    return []


def entry_path_for(path: str) -> str:
    return os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path))


def checked_paths_for(path: str, project_directory: str) -> list[str]:
    lexical_path = os.path.normpath(path)
    resolved_project_paths = [
        project_path_for(resolved_path, project_directory)
        for spelled_path in (path, lexical_path)
        for resolved_path in (os.path.realpath(spelled_path), entry_path_for(spelled_path))
    ]
    return lexical_project_paths_for(lexical_path, project_directory) + resolved_project_paths


def patch_paths(command: str) -> Iterable[str]:
    for line in command.split("\n"):
        match = re.match(r"\*\*\* (Add File|Delete File|Update File|Move to): (.+)$", line.strip())
        if match:
            yield match.group(2)


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


def edit_denial_reason(paths: Iterable[str], working_directory: str, project_directory: str) -> str | None:
    if not os.path.isabs(working_directory):
        return "editing without an absolute working directory in the hook input is blocked"
    for path in paths:
        if not path:
            return "editing without a path in the hook input is blocked"
        for checked_path in checked_paths_for(os.path.join(working_directory, path), project_directory):
            if is_sensitive_path(checked_path):
                return f"editing sensitive path is blocked: {checked_path}"
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
