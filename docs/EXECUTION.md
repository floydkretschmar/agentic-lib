## Coding conventions
- Always ask yourself: "Would a staff engineer approve this?"
- Prefer explicit code over overly compact code
- Always remove all dead and redundant code, abstractions and configuration.
- Always consolidate related logic.
- Keep exactly one canonical port path for each responsibility, and remove parallel and dead abstractions.
- Never use default values anywhere. Require an explicit value, and fail fast when it is missing.
- Never write comments. The code must be self-explanatory through the naming of variables, functions and interfaces alone.
- Configuration lives in a dedicated configuration file. A hostname, a port, a URL or any other parameterized value is never a literal or a constant in code. One checked-in file owns each value, and every consumer reads it from there.
- Use proper error handling patterns, and avoid try/catch where you can
- Keep naming conventions consistent
- Limit unnecessary complexity and nesting
- Do not nest ternary operators. For multiple conditions, prefer switch statements or if/else chains
- Replace sensitive values with `***REDACTED***`, and never paste raw credentials.
- Put pipeline execution code into run.sh, and keep complex shell code out of pipeline actions.

## Boy scout rule
Fix an inconsistency, regression, bug or departure from a general project rule even outside the task, if it is small, localized and easy. Do the same for small and localized refactors. 

Localized is not a precise term, but as a rule of thumb a change is localized, if it applies within one module only. A change that needs a design decision or that touches more than one module, is generally not a boy scout fix.

## Development principles
- A failed tool call is not unexpected and can be self repairing. Run the tool call again, and stop only if the failure does not go away.
- If the implementation differs from the approved scheme or spec, fix the implementation, not the planning docs. 
- If the user changes a rule during the execution, record it in the spec and the scheme with the same change.
- If `./run.sh lint`, `./run.sh test`, or `./run.sh build` fails, restore it to green before you continue execution or review work.
- Treat review drift against an approved phase as a bug to fix immediately. Do not create a separate todo item before you dispatch the bug-fix subagent.
- Never mark a task complete until you prove that it works
- When it is relevant, diff the behavior between main and your changes
- If you change code related to user-facing surfaces, a full visual inspection of all affected screens and controls with the Browser is mandatory afterwards.

### Deep modules
If you have the choice, build deep modules: A deep module has a small interface and a lot of implementation.

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
- Is the module deep without becoming a god module? As rough guidance: prefer modules of 200-400 lines with 1-3 public runtime exports.

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
