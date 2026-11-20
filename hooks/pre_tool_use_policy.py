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
)
COMMAND_SEPARATOR_PATTERN = re.compile(r"&&|\|\||\$\(|[;&|\n()`]")
VARIABLE_ASSIGNMENT_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")
COMMAND_WRAPPERS = {"command", "env", "exec", "nice", "nohup", "time", "xargs"}
DELETING_COMMANDS = {"rm", "unlink", "rmdir"}

EDIT_PATH_FIELD_BY_TOOL = {"Edit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}
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

    parts = [part.lower() for part in PurePosixPath(clean).parts]
    name = PurePosixPath(clean).name.lower()
    return (
        clean.startswith("/")
        or any(part in SENSITIVE_PATH_PARTS for part in parts)
        or name in SENSITIVE_FILE_NAMES
        or name.endswith(SENSITIVE_FILE_EXTENSIONS)
    )


def is_outside_project(project_relative_path: str) -> bool:
    return project_relative_path == ".." or project_relative_path.startswith("../")


def project_path_for(resolved_path: str, project_directory: str) -> str:
    project_relative_path = os.path.relpath(resolved_path, os.path.realpath(project_directory))
    if is_outside_project(project_relative_path):
        return resolved_path
    return project_relative_path


def written_project_path_for(lexical_path: str, project_directory: str) -> str:
    real_project_directory = os.path.realpath(project_directory)
    path_parts = PurePosixPath(lexical_path).parts
    for part_count in range(1, len(path_parts) + 1):
        prefix_project_path = os.path.relpath(os.path.realpath(PurePosixPath(*path_parts[:part_count])), real_project_directory)
        if not is_outside_project(prefix_project_path):
            return str(PurePosixPath(prefix_project_path, *path_parts[part_count:]))
    return lexical_path


def touched_paths_for(path: str) -> tuple[str, str]:
    target_path = os.path.realpath(path)
    entry_path = os.path.normpath(os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path)))
    return target_path, entry_path


def is_inside_directory(path: str, directory: str) -> bool:
    return os.path.commonpath([path, directory]) == directory


def edited_path_denial_reason(path: str, working_directory: str, project_directory: str) -> str | None:
    if not path:
        return "editing without a path in the hook input is blocked"
    if not path.isprintable():
        return "editing a path with control characters is blocked"

    joined_path = os.path.join(working_directory, path)
    lexical_path = os.path.normpath(joined_path)
    touched_paths = touched_paths_for(joined_path)
    if touched_paths != touched_paths_for(lexical_path):
        return f"editing a path that tools resolve differently through a symlink is blocked: {path}"

    judged_paths = [project_path_for(touched_path, project_directory) for touched_path in touched_paths]
    judged_paths.append(written_project_path_for(lexical_path, project_directory))
    for judged_path in judged_paths:
        if is_sensitive_path(judged_path):
            return f"editing sensitive path is blocked: {judged_path}"

    repository_storage = os.path.realpath(os.path.join(project_directory, ".git"))
    if any(is_inside_directory(touched_path, repository_storage) for touched_path in touched_paths):
        return f"editing the repository storage is blocked: {judged_paths[0]}"
    return None


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


def command_words_for(simple_command: str) -> list[str]:
    try:
        words = shlex.split(simple_command)
    except ValueError:
        words = simple_command.split()
    while words and (words[0] in COMMAND_WRAPPERS or VARIABLE_ASSIGNMENT_PATTERN.fullmatch(words[0])):
        words = words[1:]
    return words


def is_recursive_forced_removal(arguments: list[str]) -> bool:
    long_options = {argument for argument in arguments if argument.startswith("--")}
    short_flags = "".join(argument[1:] for argument in arguments if argument.startswith("-") and not argument.startswith("--"))
    is_recursive = "--recursive" in long_options or "r" in short_flags.lower()
    is_forced = "--force" in long_options or "f" in short_flags
    return is_recursive and is_forced


def simple_command_denial_reason(words: list[str]) -> str | None:
    program = os.path.basename(words[0])
    arguments = words[1:]
    if program == "sudo":
        return "sudo commands require explicit human approval outside this hook"
    if program == "rm" and is_recursive_forced_removal(arguments):
        return "recursive forced deletion is blocked"
    if program in DELETING_COMMANDS and any(
        is_sensitive_path(argument) for argument in arguments if not argument.startswith("-")
    ):
        return "deleting sensitive or absolute paths is blocked"
    return None


def bash_denial_reason(command: str) -> str | None:
    lowered = command.lower()
    for pattern, reason in DANGEROUS_COMMAND_PATTERNS:
        if pattern.search(lowered):
            return reason

    for simple_command in COMMAND_SEPARATOR_PATTERN.split(command):
        words = command_words_for(simple_command)
        if words:
            reason = simple_command_denial_reason(words)
            if reason:
                return reason
    return None


def edit_denial_reason(paths: Iterable[str], working_directory: str, project_directory: str) -> str | None:
    if not os.path.isabs(working_directory) or not working_directory.isprintable():
        return "editing without an absolute working directory in the hook input is blocked"
    for path in paths:
        reason = edited_path_denial_reason(path, working_directory, project_directory)
        if reason:
            return reason
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
