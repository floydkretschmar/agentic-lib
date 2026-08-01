# Logic prototype

A logic prototype is a tiny interactive terminal app that lets the user drive a state model by hand. Use it when the question is about business logic, state transitions, or data shape. These often look reasonable on paper and only feel wrong when you run real cases through them.

## When this is the right shape

- "I'm not sure if this state machine handles the edge case where X then Y."
- "Does this data model actually let me represent the case where..."
- "I want to feel out what the API should look like before writing it."
- Anything where the user wants to press buttons and watch state change.

If the question is "what should this look like", use [UI.md](UI.md) instead.

## Process

### 1. State the question

Before you write code, describe the state model and the question in one paragraph. Put it in the README of the prototype or in a comment at the top of the file. The user can then examine it now or later.

### 2. Pick the language

Use the language and the tooling conventions of the host project, and add no new package manager or runtime for the prototype. If the project has no obvious runtime, for example a docs repo, ask the user.

### 3. Isolate the logic in a portable module

Put the logic behind a small, pure interface that you can move into the real codebase later. Only the terminal UI (TUI) around it is throwaway.

The right shape depends on the question:

- A pure reducer, `(state, action) => state`. Use it when actions are discrete events and state is a single value.
- A state machine with explicit states and transitions. Use it when "which actions are even legal right now" is part of the question.
- A small set of pure functions over a plain data type. Use it when there is no implicit current state, only transformations.
- A class or module with a clear set of methods. Use it when the logic owns ongoing internal state.

Pick the shape that fits the question, not the one that is easiest to connect to a TUI. Keep the module pure, with no I/O, no terminal code, and no `console.log` for control flow. The TUI calls the module, and the module never calls the TUI.

After the prototype answers the question, move the validated reducer, machine, or function set into the real module, and delete the TUI shell.

### 4. Build the smallest TUI that exposes the state

Each frame has two parts, in this order:

1. The current state, one field per line or as formatted JSON. Show field names and section headers in bold, and less important context (timestamps, IDs, derived values) in dim text. Plain ANSI escape codes are enough (`\x1b[1m` bold, `\x1b[2m` dim, `\x1b[0m` reset), unless the project already has a styling library.
2. The keyboard shortcuts at the bottom, for example `[a] add user  [d] delete user  [t] tick clock  [q] quit`. Bold the key and dim the description, or the reverse.

Behavior:

1. Keep the state in one in-memory object or struct, and render the first frame on start.
2. Read one keystroke or one line at a time, and pass it to a handler that changes the state.
3. After every action, clear the screen (`console.clear()` / `print("\033[2J\033[H")` / equivalent) and render the full frame again. The user then sees one stable view instead of a growing scrollback.
4. Loop until the user quits.

The whole frame must fit on one screen.

### 5. Make it runnable in one command

Add a script to the existing task runner of the project (`package.json` scripts, `Makefile`, `justfile`, `pyproject.toml`). The user then runs `pnpm run <prototype-name>` or an equivalent instead of a path. If the project has no task runner, put the command at the top of the README of the prototype.

### 6. Hand it over

Give the user the run command, and add new actions when they ask for them. Listen for remarks such as "wait, that shouldn't be possible" or "huh, I assumed X would be different". Those remarks show the bugs in the idea, and the prototype exists to find them.

### 7. Capture the answer

The answer is the only part of the prototype worth keeping. If the user is available, ask what the prototype taught them. If not, leave a `NOTES.md` next to the prototype, so that someone writes down the answer before anyone deletes the prototype. If you watched the session, fill it in yourself.

## Anti-patterns

- Do not add tests. A prototype that needs tests is no longer a prototype.
- Do not connect it to the real database. Use an in-memory store unless the question is about persistence.
- Do not generalize for "what if we wanted to support X later". The prototype answers one question.
- Do not mix the logic into the TUI. A reducer or state machine that references `console.log`, prompts, or terminal escape codes is no longer portable.
- Do not ship the TUI shell to production. Keep only the logic module behind it.
