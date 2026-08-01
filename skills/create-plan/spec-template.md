# Spec template

<spec-template>

## Problem Statement

The problem that the user has, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

An extensive, numbered list of user stories that covers all aspects of the feature. Each user story must use this format:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

## Implementation Decisions

A list of the implementation decisions that you made. It can include:

- The [deep modules](../../../docs/EXECUTION.md#deep-modules) that the feature builds or modifies, with a clear description of their public interfaces
- Technical clarifications for the developer
- Architectural decisions
- Schema or database changes
- API contracts: if the feature integrates external APIs, state the functions, endpoints, and contracts to use, from authoritative sources such as the API docs
- Dependencies: if the feature adds or modifies dependencies, state the EXACT version to use in one or more version matrices

Do NOT include file paths or code snippets, because they go out of date quickly.
DO include diagrams, abstract data flows, module dependencies, and public interface abstractions.

## Testing Decisions

A list of the testing decisions that you made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules the tests cover
- Prior art for the tests (similar tests that already exist in the codebase)
- An explicit list of black-box tests that prove the expected behavior end-to-end

## Out of Scope

What this spec excludes.

## Further Notes

Any further notes about the feature.

</spec-template>