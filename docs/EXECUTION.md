## Development principles
- **Retry failed tool calls.** A failed tool call is NOT unexpected and does NOT trigger stop-the-line by itself. Run the tool call again, and stop the line only if the failure does not go away.
- **Test failures in changed classes are expected (RED PHASE).** A regression in a test that the current implementation touched is expected debugging work, so DO NOT STOP THE LINE FOR THIS.
- **Follow planning docs.** If the implementation differs from the approved scheme or spec, fix the implementation, not the planning docs. If the user changes a rule during the execution, record it in the spec and the scheme with the same change.
- **Clean baseline.** If `./run.sh lint`, `./run.sh test`, or `./run.sh build` fails, restore it to green before you continue execution or review work.
- **Use websearch to fix tooling incompatibilities.** Search the web for the latest compatible versions before you change approach or switch tools.
- **Boy scout rule.** Fix an inconsistency, regression, bug or departure from a general project rule even outside the task, if it is small, LOCALIZED and easy. Do the same for a small and LOCALIZED refactor. Each such fix lands as its own addendum of the current phase, that is, an item in `tasks/todo.md` with its TDD evidence. Name each fix to the user, and send it through the review and the QA of the phase. Change only what the defect or the refactor needs. If the fix changes behavior, it has its own test. A change that needs a design decision or a new abstraction, or that touches more than one module, is not a boy scout fix. Record such a change and discuss it first, as `AGENTS.md`/`CLAUDE.md` requires.
- **In-phase review drift.** Treat review drift against an approved phase as a bug to fix immediately. Do not create a separate todo item before you dispatch the bug-fix subagent.
- **No circular imports.** Fix every circular import as a direct amendment of the current phase, also when it is type-only or harmless today. One module owns the shared value, and its users import it from there.

## Verification before done
- Never mark a task complete until you prove that it works
- When it is relevant, diff the behavior between main and your changes
- If you change code related to user-facing surfaces, do a full visual inspection of all affected screens and controls with the Browser
- Ask yourself: "Would a staff engineer approve this?"
- Run the full validation suite: `./run.sh lint`, `./run.sh test`, and `./run.sh build`

## Coding conventions
**General principles**
- **Never write comments.** Find a better name instead, so that the names explain the code.
- **Configuration lives in a dedicated configuration file.** A hostname, a port, a URL or any other parameterized value is never a literal or a constant in code. One checked-in file owns each value, and every consumer reads it from there. A carve-out from 2026-08-21 lets a bundle that cannot import the configuration file hold the one value as a constant. The constant must have a constraint comment that names the `config/local.json` key, and a unit test that pins the two against drift.
- NEVER use a default for parameterized configuration or a required gate that comes from an environment variable. Require an explicit value, and fail fast when it is missing.
- Keep exactly one canonical port path for each responsibility, and remove parallel and dead abstractions.
- Use proper error handling patterns, and avoid try/catch where you can
- Keep naming conventions consistent

**Enforce clarity**
- Limit unnecessary complexity and nesting
- Eliminate redundant code and abstractions
- Consolidate related logic
- Do not nest ternary operators. For multiple conditions, prefer switch statements or if/else chains
- Prefer explicit code over overly compact code
- After a refactor, remove all dead code and configuration that you can delete without a change in behavior

**Other conventions**
- Summarize outputs before you share them, replace sensitive values with `***REDACTED***`, and never paste raw credentials.
- Execute the entire approved phase with fresh subagents, then run one review cycle for the whole phase, not one per slice.
- Put pipeline execution code into run.sh, and keep complex shell code out of pipeline actions.

### Deep modules

If you have the choice, build deep modules, as "A Philosophy of Software Design" describes them.

A deep module has a small interface and a lot of implementation.

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
│                     │
└─────────────────────┘
```

A shallow module has a large interface and little implementation. Avoid it.

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When you design interfaces, ask these questions:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?
- Is the module deep without becoming a god module? As rough guidance for a substantial responsibility, prefer modules of 200-400 lines with 1-3 public runtime exports.

### Design interfaces for testability

1. **Accept dependencies, do not create them**

   ```pseudocode
   // Testable
   function process_order(order, payment_gateway):
     use payment_gateway to process order
   
   // Hard to test
   function process_order(order):
     payment_gateway = create_payment_gateway()
     use payment_gateway to process order
   ```

2. **Return results, do not produce side effects**

   ```pseudocode
   // Testable
   function calculate_discount(cart):
     return discount

   // Hard to test
   function apply_discount(cart):
     cart.total = cart.total - discount
   ```

3. **Small interface**
   - Fewer methods mean fewer tests
   - Fewer parameters mean simpler test setup
