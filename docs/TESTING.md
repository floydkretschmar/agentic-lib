## Testing Principles
- **Test driven**: You test before you build. Never the other way around.
- **Tests are not optional**: Never skip tests to "move faster"
- **Test parity**: Every load-bearing class or module must have a corresponding test file before a task can be considered complete.
- **Testing module integration**: Every module MUST have relevant integration test that prove ALL relevant itegration paths
- **Testing simplicity**: Never add a new test when an existing test can be parameterized to cover both scenarios. Always modify existing tests to cover new cases instead of adding new ones when possible.
- **Visual verification**: User-facing surface changes require a full Browser visual check of the affected screens and controls in addition to automated tests.

## Testing Conventions
- **No empty tests**: Every test must include meaningful assertions and follow the Arrange-Act-Assert pattern.
- **Prefer holistic tests**: Merge multiple tests that are testing partial logic into a single test that tests the entire critical path.
- **Share fixtures within modules**: Extract any shared setup or fixture logic into a single fixture file adjacent to the test files and reuse it.Fixtures HAVE to stay local in a module. Do not centralize them or cross-reference them across modules.
- **Use parameterized tests**: Merge ALL dedicated tests that can be expressed as a single parameterized test testing the same critical path.
- **Remove duplicates**: Remove any partial or full duplicate tests.
- **Maintain readability**: Never use bad formatting practices to reduce lines of code. Always maintain readability and clarity of the tests.
- **Keep tests honest**: Never weaken or simplify a test to make it pass; keep the real failing value in the test and fix the logic at the root.
- **No contract assertions in tests**: Keep unit and strategy tests focused on public behavior of the module under test.

### Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

Characteristics:

- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

### Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface

```typescript
// BAD: Bypasses interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: Verifies through interface
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

### When to Mock

Mock at **system boundaries** only:

- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)

Don't mock:

- Your own classes/modules
- Internal collaborators
- Anything you control

### Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint

### Other Conventions
- Test package paths must mirror main package paths exactly; integration-test grouping must still align with corresponding implementation slice/package.
- Never add dedicated tests for pure cleanup-only changes such as dead-code removal, catalog pruning, or unused-import deletion when no user-visible behavior changes; verify existing behavior instead of introducing brittle cleanup tests.
