## Coding conventions
- Use ES modules with sorted imports and with file extensions in the import paths.
- Prefer the `function` keyword over arrow functions.
- Give each top-level function an explicit return type annotation.
- Give each React component an explicit Props type.
- Prefer async/await over promise chaining, because it is easier to read.

## React hooks

- Split a large hook into smaller hooks that each own one behavior or one concern of derived state.
- Export only hooks that production code uses and that are oriented to a behavior. Do not create hook boundaries only for tests.
