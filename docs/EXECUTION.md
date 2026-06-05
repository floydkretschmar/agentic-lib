## Development Principles

- **Retry failed tool calls**: Failed tool calls are NOT unexpected and do NOT trigger stop-the-line by themselves; reexecute the tool call and only stop-the-line if the failure is not transient.
- **Test failures in changed classes are expected (RED PHASE)**: A regression in a test touched during the current implementation is expected debugging work, DO NOT STOP THE LINE FOR THIS.
- **Follow planning docs**: If a discrepancy appears between scheme or spec and implementation, do not retrofit them to match code. Fix implementation to match the approved planning docs instead.
- **Clean baseline**: Never continue execution or review work on a dirty baseline; restore `npm test`, `npm run typecheck`, `npm run lint`, and `npm run build` to green first.
- **Use websearch to fix tooling incompatibilities**: When tooling incompatibilities occur, use web verification to confirm the latest compatible versions before changing approach or switching tools.
- **In-phase review drift**: Treat review drift against an approved phase as a bug to fix immediately; do not create a separate todo item before dispatching the bug-fix subagent.

## Verification Before Done

- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- When changing code related to user-facing surfaces, always perform a full visual check with the Browser across the affected screens and controls
- Ask yourself: "Would a staff engineer approve this?"
- Run full validation suite (`npm test`, `npm run typecheck`, `npm run lint`, and `npm run build`) to prove correctness

## Coding conventions

**General principles:**
- Use ES modules with proper import sorting and extensions
- Prefer `function` keyword over arrow functions
- Use explicit return type annotations for top-level functions
- Follow proper React component patterns with explicit Props types
- Use proper error handling patterns (avoid try/catch when possible)
- Maintain consistent naming conventions
- Prefer async/await over promise chaining for better readability

**Enforce Clarity**:
- Limit unnecessary complexity and nesting
- Eliminate redundant code and abstractions
- Consolidate related logic
- IMPORTANT: Avoid nested ternary operators - prefer switch statements or if/else chains for multiple conditions
- Choose clarity over brevity - explicit code is often better than overly compact code

### Deep modules

When given the choice, always prefer implementing deep modules. From "A Philosophy of Software Design":

**Deep module** = small interface + lots of implementation

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

**Shallow module** = large interface + little implementation (avoid)

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing interfaces, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?
- Is the module deep without becoming a god module? As rough guidance, prefer 200-400 line modules with 1-3 public runtime exports when the responsibility is substantial.

### React Hooks

- Decompose large hooks into smaller focused hooks that each own one cohesive behavior or derived state concern.
- Keep hook exports production-used and behavior-oriented; do not create hook boundaries solely for tests.

### Design Interfaces for Testability

Good interfaces make testing natural:

1. **Accept dependencies, don't create them**

   ```typescript
   // Testable
   function processOrder(order, paymentGateway) {}

   // Hard to test
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **Return results, don't produce side effects**

   ```typescript
   // Testable
   function calculateDiscount(cart): Discount {}

   // Hard to test
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **Small surface area**
   - Fewer methods = fewer tests needed
   - Fewer params = simpler test setup

### Other Conventions
- Redact sensitive values before sharing outputs (`***REDACTED***`) and summarize instead of pasting raw credentials.
- NEVER use defaults for parameterized configuration via environment variables; ALWAYS use the `.env` scheme for local testing and deployment.
- Never use fallback defaults for required environment gates (for example `BUGETO_ENVIRONMENT`); require explicit values and fail fast when missing.
- Review regressions that are still within an approved phase stay in that same phase; fix them immediately with fresh subagents and do not create new task items unless the user explicitly asks for that bookkeeping change.
- During an approved red-green slice, do not hand control back to the user just because full verification exposed regressions caused by the active slice; keep debugging within the same slice until the suite is green or a genuine external blocker is proven.
- Do not run review after individual slices within a phase. Execute the entire approved phase with fresh subagents first, then run one review cycle for the whole phase.
- Never keep parallel abstractions that model the same responsibility; one canonical port path must exist and dead abstractions must be removed.
- After refactoring, never leave unused artifacts behind; remove the maximum amount of dead code and configuration that can be deleted without changing behavior.
- Keep living docs current only when the approved phase explicitly calls for documentation updates; otherwise treat documentation changes as out of scope.
