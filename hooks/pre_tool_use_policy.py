#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import unicodedata
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
SHELL_OPERATOR_CHARACTERS = ";&|()\n"
SHELL_INTERPRETERS = {"sh", "bash", "zsh", "dash", "ksh"}
DELETING_PROGRAMS = {"rm", "unlink", "rmdir"}
HEREDOC_DELIMITER_PATTERN = re.compile(r"""(['"]?)([^\s;&|()<>'"]+)\1""")
PATCH_MARKER = "*** Begin Patch"
MAXIMUM_SHELL_NESTING = 20
CODEX_WHITESPACE = "\t\n\x0b\x0c\r \x85\xa0                　"

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
    except (ValueError, RecursionError):
        return None
    return payload if isinstance(payload, dict) else None


def string_field_from(tool_input: Any, field_name: str) -> str:
    if isinstance(tool_input, dict) and isinstance(tool_input.get(field_name), str):
        return tool_input[field_name]
    return ""


def has_control_characters(text: str) -> bool:
    return any(unicodedata.category(character) in ("Cc", "Cs") for character in text)


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


def repository_storage_for(project_directory: str) -> str:
    git_entry = os.path.join(project_directory, ".git")
    if os.path.isfile(git_entry):
        with open(git_entry, encoding="utf-8", errors="replace") as git_file:
            first_line = git_file.readline()
        if first_line.startswith("gitdir:"):
            return os.path.realpath(os.path.join(project_directory, first_line.removeprefix("gitdir:").strip()))
    return os.path.realpath(git_entry)


def is_inside_directory(path: str, directory: str) -> bool:
    return os.path.commonpath([path.lower(), directory.lower()]) == directory.lower()


def edited_path_denial_reason(path: str, working_directory: str, project_directory: str) -> str | None:
    if not path:
        return "editing without a path in the hook input is blocked"
    if has_control_characters(path):
        return "editing a path with control characters is blocked"
    if path.startswith("~"):
        return f"editing a path that tools expand differently is blocked: {path}"

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

    repository_storage = repository_storage_for(project_directory)
    if any(is_inside_directory(touched_path, repository_storage) for touched_path in touched_paths):
        return f"editing the repository storage is blocked: {judged_paths[0]}"
    return None


def edit_denial_reason(paths: list[str], working_directory: str, project_directory: str) -> str | None:
    if not os.path.isabs(working_directory) or has_control_characters(working_directory):
        return "editing without an absolute working directory in the hook input is blocked"
    if not paths:
        return "editing without a path in the hook input is blocked"
    for path in paths:
        reason = edited_path_denial_reason(path, working_directory, project_directory)
        if reason:
            return reason
    return None


def patch_paths(command: str) -> list[str]:
    paths = []
    for line in command.split("\n"):
        match = re.match(r"\*\*\* (Add File|Delete File|Update File|Move to): (.+)$", line.strip(CODEX_WHITESPACE))
        if match:
            paths.append(match.group(2))
    return paths


class ShellCommandReader:
    def __init__(self, command: str) -> None:
        self.text = command.replace("\\\n", "")
        self.position = 0
        self.word: str | None = None
        self.simple_commands: list[list[str]] = [[]]
        self.skeleton: list[str] = []
        self.substitutions: list[str] = []
        self.heredoc_bodies: list[tuple[list[str], str]] = []
        self.pending_heredocs: list[tuple[str, bool, list[str]]] = []

    def read(self) -> bool:
        while self.position < len(self.text):
            character = self.text[self.position]
            if character == "\\":
                self.append(self.text[self.position + 1 : self.position + 2])
                self.position += 2
            elif character == "'":
                if not self.read_single_quoted():
                    return False
            elif character == '"':
                if not self.read_double_quoted():
                    return False
            elif self.text.startswith("$(", self.position) or character == "`":
                if not self.read_substitution():
                    return False
            elif character == "#" and self.word is None:
                self.skip_comment()
            elif self.text.startswith("<<", self.position) and not self.text.startswith("<<<", self.position):
                self.read_heredoc_operator()
            elif character in SHELL_OPERATOR_CHARACTERS:
                self.end_simple_command(character)
                self.position += 1
                if character == "\n":
                    self.read_heredoc_bodies()
            elif character in " \t":
                self.end_word()
                self.position += 1
            else:
                self.append(character)
                self.position += 1
        self.end_word()
        return True

    def append(self, characters: str) -> None:
        self.word = (self.word or "") + characters

    def end_word(self) -> None:
        if self.word is not None:
            self.simple_commands[-1].append(self.word)
            self.skeleton.append("_" if any(character.isspace() for character in self.word) else self.word)
            self.word = None

    def end_simple_command(self, operator: str) -> None:
        self.end_word()
        self.skeleton.append(operator)
        if self.simple_commands[-1]:
            self.simple_commands.append([])

    def skip_comment(self) -> None:
        newline = self.text.find("\n", self.position)
        self.position = len(self.text) if newline == -1 else newline

    def read_single_quoted(self) -> bool:
        closing_quote = self.text.find("'", self.position + 1)
        if closing_quote == -1:
            return False
        self.append(self.text[self.position + 1 : closing_quote])
        self.position = closing_quote + 1
        return True

    def read_double_quoted(self) -> bool:
        self.append("")
        self.position += 1
        while self.position < len(self.text):
            character = self.text[self.position]
            if character == '"':
                self.position += 1
                return True
            if character == "\\" and self.text[self.position + 1 : self.position + 2] in ('"', "\\", "$", "`"):
                self.append(self.text[self.position + 1])
                self.position += 2
            elif self.text.startswith("$(", self.position) or character == "`":
                if not self.read_substitution():
                    return False
            else:
                self.append(character)
                self.position += 1
        return False

    def read_substitution(self) -> bool:
        if self.text[self.position] == "`":
            closing_backtick = self.text.find("`", self.position + 1)
            if closing_backtick == -1:
                return False
            content_start, content_end = self.position + 1, closing_backtick
        else:
            content_start = self.position + 2
            content_end = self.closing_parenthesis_after(self.position + 1)
            if content_end == -1:
                return False
        self.substitutions.append(self.text[content_start:content_end])
        self.append(self.text[self.position : content_end + 1])
        self.position = content_end + 1
        return True

    def closing_parenthesis_after(self, opening_parenthesis: int) -> int:
        depth = 0
        quote = None
        for index in range(opening_parenthesis, len(self.text)):
            character = self.text[index]
            if quote:
                quote = None if character == quote else quote
            elif character in "'\"":
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    return index
        return -1

    def read_heredoc_operator(self) -> None:
        self.end_word()
        self.position += 2
        strips_tabs = self.text.startswith("-", self.position)
        if strips_tabs:
            self.position += 1
        while self.text[self.position : self.position + 1] in (" ", "\t"):
            self.position += 1
        delimiter = HEREDOC_DELIMITER_PATTERN.match(self.text, self.position)
        if delimiter:
            self.pending_heredocs.append((delimiter.group(2), strips_tabs, self.simple_commands[-1]))
            self.position = delimiter.end()

    def read_heredoc_bodies(self) -> None:
        for delimiter, strips_tabs, owner_words in self.pending_heredocs:
            body_lines = []
            while self.position < len(self.text):
                newline = self.text.find("\n", self.position)
                line_end = len(self.text) if newline == -1 else newline
                line = self.text[self.position : line_end]
                self.position = line_end + 1
                if (line.lstrip("\t") if strips_tabs else line) == delimiter:
                    break
                body_lines.append(line)
            self.heredoc_bodies.append((owner_words, "\n".join(body_lines)))
        self.pending_heredocs = []


def matches_long_option(long_options: list[str], full_option: str) -> bool:
    return any(len(option) > 2 and full_option.startswith(option) for option in long_options)


def deletion_denial_reason(program: str, arguments: list[str]) -> str | None:
    operands = []
    long_options = []
    short_flags = ""
    options_ended = False
    for argument in arguments:
        if options_ended or argument == "-" or not argument.startswith("-"):
            operands.append(argument)
        elif argument == "--":
            options_ended = True
        elif argument.startswith("--"):
            long_options.append(argument)
        else:
            short_flags += argument[1:]
    is_recursive = "r" in short_flags.lower() or matches_long_option(long_options, "--recursive")
    is_forced = "f" in short_flags or matches_long_option(long_options, "--force")
    if program == "rm" and is_recursive and is_forced:
        return "recursive forced deletion is blocked"
    if any(is_sensitive_path(operand) for operand in operands):
        return "deleting sensitive or absolute paths is blocked"
    return None


def program_denial_reason(program: str, arguments: list[str]) -> str | None:
    if program == "sudo":
        return "sudo commands require explicit human approval outside this hook"
    if program in DELETING_PROGRAMS:
        return deletion_denial_reason(program, arguments)
    return None


def nested_commands_for(program: str, arguments: list[str]) -> list[str]:
    if program == "eval":
        return [" ".join(arguments)]
    if program in SHELL_INTERPRETERS:
        for index, argument in enumerate(arguments[:-1]):
            if argument.startswith("-") and not argument.startswith("--") and "c" in argument:
                return [arguments[index + 1]]
    return []


def shell_denial_reason(command: str, working_directory: str, project_directory: str, nesting: int) -> str | None:
    if nesting > MAXIMUM_SHELL_NESTING:
        return "deeply nested shell commands are blocked"
    reader = ShellCommandReader(command)
    if not reader.read():
        return "a shell command with unbalanced quotes or substitutions is blocked"

    skeleton = " ".join(reader.skeleton).lower()
    for pattern, reason in DANGEROUS_COMMAND_PATTERNS:
        if pattern.search(skeleton):
            return reason

    nested_commands = list(reader.substitutions)
    patch_texts = []
    for words in reader.simple_commands:
        for index, word in enumerate(words):
            program = os.path.basename(word).lower()
            reason = program_denial_reason(program, words[index + 1 :])
            if reason:
                return reason
            nested_commands.extend(nested_commands_for(program, words[index + 1 :]))
        patch_texts.extend(word for word in words if PATCH_MARKER in word)
    for owner_words, body in reader.heredoc_bodies:
        if PATCH_MARKER in body:
            patch_texts.append(body)
        if any(os.path.basename(word).lower() in SHELL_INTERPRETERS for word in owner_words):
            nested_commands.append(body)

    for patch_text in patch_texts:
        reason = edit_denial_reason(patch_paths(patch_text), working_directory, project_directory)
        if reason:
            return reason
    for nested_command in nested_commands:
        reason = shell_denial_reason(nested_command, working_directory, project_directory, nesting + 1)
        if reason:
            return reason
    return None


def flattened_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from flattened_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from flattened_strings(nested)


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
        reason = shell_denial_reason(string_field_from(tool_input, "command"), working_directory, project_directory, 0)
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
