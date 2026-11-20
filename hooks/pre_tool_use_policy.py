#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import unicodedata
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Any, NamedTuple


SHELL_OPERATOR_CHARACTERS = ";&|()\n"
SHELL_INTERPRETERS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "ash", "mksh", "csh", "tcsh"}
SCRIPT_INTERPRETERS = SHELL_INTERPRETERS | {"python", "python3", "perl", "ruby", "node"}
TEXT_RUNNING_PROGRAMS = SHELL_INTERPRETERS | {"eval"}
READ_ONLY_PROGRAMS = {"echo", "printf", "grep", "egrep", "fgrep", "rg", "ag", "cat", "head", "tail", "wc", "ls", "which", "type", "man"}
REDIRECTION_PATTERN = re.compile(r"\d*(&>>?|>>?&?|<&|<>|>\||<)")
DOWNLOADING_PROGRAMS = {"curl", "wget"}
DELETING_PROGRAMS = {"rm", "unlink", "rmdir"}
SYSTEM_PROGRAMS = {"shutdown", "reboot", "poweroff", "halt"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c"}
HEREDOC_DELIMITER_PATTERN = re.compile(r"[^\s;&|()<>]+")
PATCH_MARKER = "*** Begin Patch"
MAXIMUM_SHELL_NESTING = 20
CODEX_WHITESPACE = "".join(
    chr(code_point)
    for code_point in (0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B), 0x2028, 0x2029, 0x202F, 0x205F, 0x3000)
)

EDIT_PATH_FIELD_BY_TOOL = {"Edit": "file_path", "MultiEdit": "file_path", "Write": "file_path", "NotebookEdit": "notebook_path"}
SENSITIVE_PATH_PARTS = {".git", ".ssh"}
SENSITIVE_FILE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
SENSITIVE_FILE_EXTENSIONS = (".pem", ".key", ".p12", ".pfx")


class Heredoc(NamedTuple):
    owner_words: list[str]
    body: str
    is_quoted: bool
    is_terminated: bool


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
    def __init__(self, text: str, start_position: int, stops_at_closing_parenthesis: bool) -> None:
        self.text = text
        self.position = start_position
        self.stops_at_closing_parenthesis = stops_at_closing_parenthesis
        self.parenthesis_depth = 0
        self.closing_parenthesis_position = -1
        self.word: str | None = None
        self.simple_commands: list[list[str]] = [[]]
        self.substitutions: list[str] = []
        self.heredocs: list[Heredoc] = []
        self.pending_heredocs: list[tuple[str, bool, bool, list[str]]] = []

    def read(self) -> bool:
        while self.position < len(self.text):
            character = self.text[self.position]
            if character == "\\":
                self.read_escape()
            elif character == "'":
                if not self.read_single_quoted():
                    return False
            elif self.text.startswith("$'", self.position):
                if not self.read_ansi_c_quoted():
                    return False
            elif self.text.startswith('$"', self.position):
                self.position += 1
            elif character == '"':
                if not self.read_double_quoted():
                    return False
            elif self.text.startswith("$(", self.position) or character == "`":
                if not self.read_substitution():
                    return False
            elif character == "#" and self.word is None:
                self.skip_comment()
            elif self.text.startswith("<<", self.position):
                self.read_heredoc_operator()
            elif self.is_part_of_redirection(character):
                self.append(character)
                self.position += 1
            elif character == ")" and self.stops_at_closing_parenthesis and self.parenthesis_depth == 0:
                self.end_word()
                self.closing_parenthesis_position = self.position
                return True
            elif character in SHELL_OPERATOR_CHARACTERS:
                self.read_operator(character)
            elif character in " \t":
                self.end_word()
                self.position += 1
            else:
                self.append(character)
                self.position += 1
        self.end_word()
        self.read_heredoc_bodies()
        return not self.stops_at_closing_parenthesis

    def read_expanding_text(self) -> bool:
        while self.position < len(self.text):
            if self.text[self.position] == "\\":
                self.position += 2
            elif self.text.startswith("$(", self.position) or self.text[self.position] == "`":
                if not self.read_substitution():
                    return False
            else:
                self.position += 1
        return True

    def append(self, characters: str) -> None:
        self.word = (self.word or "") + characters

    def end_word(self) -> None:
        if self.word is not None:
            self.simple_commands[-1].append(self.word)
            self.word = None

    def read_operator(self, operator: str) -> None:
        self.end_word()
        if operator == "(":
            self.parenthesis_depth += 1
        if operator == ")":
            self.parenthesis_depth -= 1
        if self.simple_commands[-1]:
            self.simple_commands.append([])
        self.position += 1
        if operator == "\n":
            self.read_heredoc_bodies()

    def is_part_of_redirection(self, character: str) -> bool:
        previous_character = self.text[self.position - 1] if self.position > 0 else ""
        next_character = self.text[self.position + 1 : self.position + 2]
        if character == "&":
            return previous_character in ("<", ">") or next_character == ">"
        if character == "|":
            return previous_character == ">"
        return False

    def read_escape(self) -> None:
        escaped_character = self.text[self.position + 1 : self.position + 2]
        if escaped_character != "\n":
            self.append(escaped_character)
        self.position += 2

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

    def read_ansi_c_quoted(self) -> bool:
        index = self.position + 2
        while index < len(self.text) and self.text[index] != "'":
            index += 2 if self.text[index] == "\\" else 1
        if index >= len(self.text):
            return False
        quoted_text = self.text[self.position + 2 : index]
        self.append(quoted_text.encode("latin-1", "backslashreplace").decode("unicode_escape", "replace"))
        self.position = index + 1
        return True

    def read_double_quoted(self) -> bool:
        self.append("")
        self.position += 1
        while self.position < len(self.text):
            character = self.text[self.position]
            escaped_character = self.text[self.position + 1 : self.position + 2]
            if character == '"':
                self.position += 1
                return True
            if character == "\\" and escaped_character == "\n":
                self.position += 2
            elif character == "\\" and escaped_character in ('"', "\\", "$", "`"):
                self.append(escaped_character)
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
            content_start = self.position + 1
            content_end = self.closing_backtick_after(content_start)
        else:
            content_start = self.position + 2
            substitution_reader = ShellCommandReader(self.text, content_start, True)
            content_end = substitution_reader.closing_parenthesis_position if substitution_reader.read() else -1
        if content_end == -1:
            return False
        self.substitutions.append(self.text[content_start:content_end])
        self.append(self.text[self.position : content_end + 1])
        self.position = content_end + 1
        return True

    def closing_backtick_after(self, start_position: int) -> int:
        index = start_position
        while index < len(self.text):
            if self.text[index] == "\\":
                index += 2
            elif self.text[index] == "`":
                return index
            else:
                index += 1
        return -1

    def read_heredoc_operator(self) -> None:
        self.end_word()
        self.position += 2
        strips_tabs = self.text.startswith("-", self.position)
        if strips_tabs:
            self.position += 1
        while self.text[self.position : self.position + 1] in (" ", "\t"):
            self.position += 1
        raw_delimiter = HEREDOC_DELIMITER_PATTERN.match(self.text, self.position)
        if raw_delimiter:
            is_quoted = any(character in "'\"\\" for character in raw_delimiter.group(0))
            delimiter = re.sub(r"\\(.)|['\"]", r"\1", raw_delimiter.group(0))
            self.pending_heredocs.append((delimiter, strips_tabs, is_quoted, self.simple_commands[-1]))
            self.position = raw_delimiter.end()

    def read_heredoc_bodies(self) -> None:
        for delimiter, strips_tabs, is_quoted, owner_words in self.pending_heredocs:
            body_lines = []
            is_terminated = False
            while self.position < len(self.text):
                newline = self.text.find("\n", self.position)
                line_end = len(self.text) if newline == -1 else newline
                line = self.text[self.position : line_end]
                self.position = line_end + 1
                if (line.lstrip("\t") if strips_tabs else line) == delimiter:
                    is_terminated = True
                    break
                body_lines.append(line)
            self.heredocs.append(Heredoc(owner_words, "\n".join(body_lines), is_quoted, is_terminated))
        self.pending_heredocs = []


def program_name_of(word: str) -> str:
    return os.path.basename(word.lstrip("=<")).lower()


def without_redirections(arguments: list[str]) -> list[str]:
    kept_arguments = []
    skips_redirection_target = False
    for argument in arguments:
        redirection = REDIRECTION_PATTERN.match(argument)
        if skips_redirection_target:
            skips_redirection_target = False
        elif redirection and redirection.end() == len(argument):
            skips_redirection_target = True
        elif not redirection:
            kept_arguments.append(argument)
    return kept_arguments


def matches_long_option(arguments: list[str], full_option: str) -> bool:
    return any(len(argument) > 2 and full_option.startswith(argument.split("=")[0]) for argument in arguments if argument.startswith("--"))


def deletion_denial_reason(program: str, arguments: list[str]) -> str | None:
    operands = []
    options = []
    options_ended = False
    for argument in arguments:
        if options_ended or argument == "-" or not argument.startswith("-"):
            operands.append(argument)
        elif argument == "--":
            options_ended = True
        else:
            options.append(argument)
    short_flags = "".join(option[1:] for option in options if not option.startswith("--"))
    is_recursive = "r" in short_flags.lower() or matches_long_option(options, "--recursive")
    is_forced = "f" in short_flags or matches_long_option(options, "--force")
    if program == "rm" and is_recursive and is_forced:
        return "recursive forced deletion is blocked"
    if any(is_sensitive_path(operand) or operand.startswith("~") or is_outside_project(os.path.normpath(operand)) for operand in operands):
        return "deleting sensitive, absolute or parent paths is blocked"
    return None


def git_denial_reason(arguments: list[str]) -> str | None:
    remaining_arguments = list(arguments)
    while remaining_arguments and remaining_arguments[0].startswith("-"):
        if remaining_arguments.pop(0) in GIT_OPTIONS_WITH_VALUE and remaining_arguments:
            remaining_arguments.pop(0)
    if not remaining_arguments:
        return None
    subcommand, subcommand_arguments = remaining_arguments[0], remaining_arguments[1:]
    short_flags = "".join(argument[1:] for argument in subcommand_arguments if argument.startswith("-") and not argument.startswith("--"))
    if subcommand == "reset" and matches_long_option(subcommand_arguments, "--hard"):
        return "hard git resets are blocked"
    if subcommand == "clean" and (set(short_flags) & set("fdx") or matches_long_option(subcommand_arguments, "--force")):
        return "destructive git clean is blocked"
    if subcommand in ("checkout", "restore") and "--" in subcommand_arguments:
        return "destructive git checkout/restore is blocked"
    return None


def program_denial_reason(program: str, words_after_program: list[str]) -> str | None:
    arguments = without_redirections(words_after_program)
    if program == "sudo":
        return "sudo commands require explicit human approval outside this hook"
    if program in DELETING_PROGRAMS:
        return deletion_denial_reason(program, arguments)
    if program == "git":
        return git_denial_reason(arguments)
    if program == "dd" and any(argument.startswith("of=/dev/") for argument in arguments):
        return "raw device writes are blocked"
    if program.startswith("mkfs") or program in SYSTEM_PROGRAMS:
        return "system-level destructive command is blocked"
    return None


def split_string_commands_for(words: list[str]) -> list[str]:
    return [
        later_word
        for earlier_word, option, later_word in zip(words, words[1:], words[2:])
        if program_name_of(earlier_word) == "env" and option in ("-S", "--split-string")
    ]


def heredoc_commands_for(heredoc: Heredoc) -> list[str] | None:
    if not heredoc.is_terminated:
        return [heredoc.body]
    if heredoc.is_quoted:
        return []
    expansion_reader = ShellCommandReader(heredoc.body, 0, False)
    return expansion_reader.substitutions if expansion_reader.read_expanding_text() else None


def collected_shell_parts(command: str, nesting: int, treats_text_as_commands: bool) -> tuple[list[list[str]], list[str]] | None:
    if nesting > MAXIMUM_SHELL_NESTING:
        return None
    reader = ShellCommandReader(command, 0, False)
    if not reader.read():
        return None

    simple_commands = [words for words in reader.simple_commands if words]
    patch_texts = [word for words in simple_commands for word in words if PATCH_MARKER in word]
    nested_commands = list(reader.substitutions)
    for words in simple_commands:
        nested_commands.extend(split_string_commands_for(words))
        if treats_text_as_commands:
            nested_commands.extend(word for word in words if any(character.isspace() for character in word))
    for heredoc in reader.heredocs:
        if PATCH_MARKER in heredoc.body:
            patch_texts.append(heredoc.body)
        heredoc_commands = [heredoc.body] if treats_text_as_commands else heredoc_commands_for(heredoc)
        if heredoc_commands is None:
            return None
        nested_commands.extend(heredoc_commands)

    for nested_command in nested_commands:
        nested_parts = collected_shell_parts(nested_command, nesting + 1, treats_text_as_commands)
        if nested_parts is None:
            return None
        simple_commands.extend(nested_parts[0])
        patch_texts.extend(nested_parts[1])
    return simple_commands, patch_texts


def programs_in(simple_commands: list[list[str]]) -> set[str]:
    return {program_name_of(word) for words in simple_commands for word in words}


def shell_denial_reason(command: str, working_directory: str, project_directory: str) -> str | None:
    shell_parts = collected_shell_parts(command, 0, False)
    runs_text = shell_parts is not None and bool(programs_in(shell_parts[0]) & TEXT_RUNNING_PROGRAMS)
    if runs_text:
        shell_parts = collected_shell_parts(command, 0, True)
    if shell_parts is None:
        return "a shell command with unbalanced quotes, substitutions or deep nesting is blocked"
    simple_commands, patch_texts = shell_parts

    for words in simple_commands:
        if not runs_text and program_name_of(words[0]) in READ_ONLY_PROGRAMS:
            continue
        for index, word in enumerate(words):
            reason = program_denial_reason(program_name_of(word), words[index + 1 :])
            if reason:
                return reason

    programs = programs_in(simple_commands)
    if programs & DOWNLOADING_PROGRAMS and programs & SCRIPT_INTERPRETERS:
        return "remote download piped to an interpreter is blocked"

    for patch_text in patch_texts:
        paths = patch_paths(patch_text)
        reason = edit_denial_reason(paths, working_directory, project_directory) if paths else None
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
        reason = shell_denial_reason(string_field_from(tool_input, "command"), working_directory, project_directory)
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
