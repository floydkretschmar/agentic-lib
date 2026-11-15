## Golden rule
Every public interface has a test. This covers every exported function and every React component.

## Testing pyramid
Follow the testing pyramid of unit, integration and end-to-end tests:

- Unit tests are cheap and plentiful. Cover EVERYTHING a function could produce: Happy case, unhappy case, edge cases. Be as exhaustive as possible
- Integration test verify behavior that only emerges when interacting with other systems: API responses, Database queries and other external system calls. Cover critical integration points thoroughly but be aware of the increased cost compared to unit tests.
- End-to-end test prove the correctness of user journey through the real stack. They confirm that the most critical paths of the application work. They offer the highest quality proof but are very expensive and should be used sparingly. ALWAYS prefer to test new behavior as part of existing end-to-end tests, instead of creating a new one.

## Testing rules
- Work test driven and write the test before you build.
- Never skip tests to "move faster".
- Never weaken or simplify a test to make it pass. Keep the real failing value in the test, and fix the root cause of the failure.
- Every test must include meaningful assertions and follow the Arrange-Act-Assert pattern.
- Cover all observable paths that users, callers, or commands rely on.
- Cover a new case with a change to an existing test, for example a new parameter, instead of a new test.
- Remove duplicate tests, including partial duplicates of the same logic spread across multiple tests. 
- A change to a user-facing surface needs a full visual inspection of the affected screens and controls in the Browser. 
- Extract shared setup or fixture logic into a single fixture file next to the test files, and reuse it. Fixtures have to stay local in a module, so do not centralize them or cross-reference them across modules.
- Maintain readability and never use bad formatting practices to reduce lines of code.
- A test that passes at its first run proves nothing yet. Break the line of production code for one run, see the test fail, and restore the line.
- Write test that prevent race conditions and flakiness. Wait for all the values a step needs in one condition before asserting the next step.
- Never add dedicated tests for a cleanup-only change that changes no user-visible behavior, such as dead-code removal, catalog pruning, or unused-import deletion.
- Never use tests to enforce policy, architecture constraints, dependency state, version state, coverage metrics, file existence, file absence, or deletion.

### Good tests assert through real interfaces

```pseudocode
// GOOD: Tests observable behavior
test "user can checkout with valid cart":
  cart = create_cart()
  cart.add(product)

  result = checkout(cart, payment_method)

  assert result.status == "confirmed"
```

Good tests share the following characteristics. They:

- test behavior that users and callers care about
- use the public API only
- survive internal refactors that do not change external behavior
- have a name that describes WHAT a public interface should return, not HOW it works internally

### Bad tests depend on internal structure

```pseudocode
// BAD: Tests implementation details
test "checkout calls payment service process":
  mock_payment_service = mock(payment_service)

  checkout(cart, payment_method)

  assert mock_payment_service.process_was_called_with(cart.total)
```

Bad tests share the following red flags. They

- mock internal collaborators
- test private methods
- assert on call counts or order
- break after a refactor that does not change public behavior
- their name describes HOW a function works, not WHAT it should return
- assert through external means instead of the interface

```pseudocode
// BAD: Bypasses interface to verify
test "create user saves to storage":
  create_user(name: "Alice")

  row = storage.query_user_by_name("Alice")

  assert row exists

// GOOD: Verifies through interface
test "create user makes user retrievable":
  user = create_user(name: "Alice")

  retrieved = get_user(user.id)

  assert retrieved.name == "Alice"
```

### When to mock

Mock at system boundaries:
- External APIs (for example payment or email)
- Databases (sometimes, but prefer a test DB)
- Time and randomness
- File system (sometimes)

Do not mock:
- Your own classes or modules
- Internal collaborators
- Anything you control

### Designing for mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in instead of creating them internally:

```pseudocode
// Easy to mock
function process_payment(order, payment_client):
  return payment_client.charge(order.total)

// Hard to mock
function process_payment(order):
  client = create_payment_client_from_environment()
  return client.charge(order.total)
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create one specific function for each external operation, not one generic function with conditional logic:

```pseudocode
// GOOD: Each function is independently mockable
client:
  get_user(id)
  get_orders(user_id)
  create_order(order_data)

// BAD: Mocking requires conditional logic inside the mock
generic_client:
  request(operation_name, options)
```

The SDK approach gives these results:

- Each mock returns one specific shape
- No conditional logic in test setup
- It is easier to see which endpoints a test exercises
- Type safety per endpoint
