---
name: tdd
description: Use whenever code is changed. Use when "TDD", "Test-Driven Development" or "Test first" are mentioned.
---

# Test-driven development

TDD is the red-to-green-refactor cycle:

1. List the required behaviors, including unhappy paths.
2. Write one test for one behavior through the public interface. Assert on what the caller gets back. (RED)
3. Run it. It must fail because the behavior is missing, not because of a typo.
4. Write the least code that makes it pass. (GREEN)
5. Run the suite until green.
6. Find and refactor all refactor candidates, then run the tests again and make sure the full baseline is green. You change structure only. (REFACTOR)
7. Repeat until all required behaviors are implemented.

The sections below define what makes the loop produce useful tests. Each section applies to every cycle.

Read `/docs` if it exists, so that test names and interface vocabulary match the domain language of the project. Follow the ADRs in the area that you touch.

## What a good test is

A good test proves behavior through public interfaces, not implementation details, so the code can change entirely without a change to the test. It reads like a specification. For example, "user can checkout with valid cart" names exactly one capability.

See [TESTING.md](../../../docs/TESTING.md) for examples and for mocking guidelines.

## Seams: where tests go

A seam is a public interface where a test observes behavior without reaching inside. Test against seams, not against internals.

Ask: "What is the public interface, and which seams do we test?"

## Anti-patterns

- Implementation-coupled. The test mocks internal collaborators, tests private methods, or asserts through a side channel, such as a database query instead of the interface. The symptom is a test that breaks after a refactor that did not change behavior.
- Tautological. The assertion computes the expected value the same way the code does, so it passes by construction, as in `expect(add(a, b)).toBe(a + b)`. Expected values must come from an independent source of truth.
- Horizontal slicing. You write all tests first, then all implementation. Such tests describe imagined behavior and the shape of the code instead of user-facing behavior. They miss real changes, and they fix a test structure before you understand the implementation. Work in vertical slices instead: one test, then one implementation, then one refactor, then repeat.

## Rules of the loop

- Red before green. Write the failing test first, then only enough code to pass it, with nothing for future tests or speculative features.
- One slice at a time. Each cycle covers one seam, one test, and one minimal implementation.
