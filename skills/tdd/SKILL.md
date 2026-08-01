---
name: tdd
description: Test-driven development with a red-green-refactor loop. Use when the user wants to build features or fix bugs with TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
---

# Test-driven development

TDD is the red-to-green-refactor loop:

1. Write a test for the current slice.
2. Run it and make sure that it fails (RED).
3. Implement the slice, and run the same test to make sure that it passes (GREEN).
4. After all tests pass, find and refactor all refactor candidates (REFACTOR).
5. Run the baseline verification to make sure that the refactor is correct.

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
