# Golden rule
- **Every public interface has a test.** This covers every exported function and every React component.

## Testing principles
- **Test only behavior.** A test proves behavior through public interfaces and observable outcomes. NEVER use tests to enforce policy, architecture constraints, dependency state, version state, coverage metrics, file existence, file absence, or deletion.
- **Test driven.** Write the test before you build.
- **Tests are not optional.** Never skip tests to "move faster".
- **Test the behavior that matters.** Cover the observable paths that users, callers, or commands rely on.
- **Testing simplicity.** Cover a new case with a change to an existing test, for example a new parameter, instead of a new test.
- **Visual verification.** A change to a user-facing surface needs automated tests and a full visual inspection of the affected screens and controls in the Browser. A review that passed is no substitute, because a fix can read correctly and still fail in the browser.

## Testing conventions

- **No empty tests.** Every test must include meaningful assertions and follow the Arrange-Act-Assert pattern.
- **Test the whole critical path.** Merge tests of partial logic into a single test of the entire critical path.
- **Share fixtures within modules.** Extract shared setup or fixture logic into a single fixture file next to the test files, and reuse it. Fixtures HAVE to stay local in a module, so do not centralize them or cross-reference them across modules.
- **Use parameterized tests.** Merge ALL dedicated tests that test the same critical path and that you can express as a single parameterized test.
- **Remove duplicates.** This includes partial duplicates of a test.
- **Maintain readability.** Never use bad formatting practices to reduce lines of code.
- **Keep tests honest.** Never weaken or simplify a test to make it pass. Keep the real failing value in the test, and fix the logic at the root.
- **Report a changed test.** Change a test only when the requirement changed, and say what it guarded before and what guards that now.
- **Prove the cover.** A test that passes at its first run proves nothing yet. Break the line of production code for one run, see the test fail, and restore the line.
- **Await one condition.** Wait for all the values a step needs in one condition. A wait for one and a read of the other is a race.
- **No cleanup tests.** Never add dedicated tests for a cleanup-only change that changes no user-visible behavior, such as dead-code removal, catalog pruning, or unused-import deletion. Make sure that existing behavior still works.

### Good tests

**Integration-style.** Test through real interfaces, not mocks of internal parts.

```pseudocode
// GOOD: Tests observable behavior
test "user can checkout with valid cart":
  cart = create_cart()
  cart.add(product)

  result = checkout(cart, payment_method)

  assert result.status == "confirmed"
```

Characteristics:

- Tests behavior that users and callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

### Bad tests

**Implementation-detail tests.** These tests depend on internal structure.

```pseudocode
// BAD: Tests implementation details
test "checkout calls payment service process":
  mock_payment_service = mock(payment_service)

  checkout(cart, payment_method)

  assert mock_payment_service.process_was_called_with(cart.total)
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts or order
- Test breaks after a refactor that does not change behavior
- Test name describes HOW, not WHAT
- Asserting through external means instead of the interface

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

Mock at system boundaries only:

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
