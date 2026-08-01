# Scheme template

<scheme-template>
# Scheme: <Feature Name>

> Source spec: <brief identifier or link>

## Architectural decisions

Durable decisions that apply across all phases:

- **Routes**: ...
- **Schema**: ...
- **Key models**: ...
- (add or remove items as needed)

---

## Phase 1: <Title>

**User stories**: <list from spec>

### What to build
<!-- The end-to-end behavior this ticket makes work, from the user's perspective, not a layer-by-layer implementation. Reference architectural decisions from the spec where applicable -->

#### Step 1.1: Write failing test
List ALL test scenarios and edge cases of the phase in this format:

- [Test class 1]
    - [Flow 1]
        - [Happy path]: 
            - [input] -> [expected output]
            - [input2] -> [expected output2]
        - [Edge case 1]: [input1, input2] -> [expected output]
        - [Edge case 2]: [input1, input2] -> [expected output]
        - [Unhappy path]: [input1, input2, input3] -> [expected error]
    - [Flow 2]
        - ...
    - [Flow 3]
- [Test class 2]
    - ...
...

**Run:** The narrowest relevant test command (a class or method, if possible).
**Expect:** FAIL (red)

#### Step 1.2: Implement minimal code
A short description of the end-to-end behavior of this vertical slice, not a layer-by-layer implementation.

#### Step 1.3: Verify test passes
**Run:** The same test command as in Step 1.1.
**Expect:** PASS (green)

#### Step 1.4: Aggressive refactor
A complete list of ALL refactor candidates for this vertical slice, in both production code and test classes. The main goal of the refactor must be to REDUCE lines of code. Follow DRY and YAGNI.

#### Step 1.5: Manual verification
All manual steps that make sure that the behavior is correct in a real environment, for all critical user-facing scenarios. A non-technical user must be able to execute them.

### Acceptance criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Phase 2: <Title>

**User stories**: <list from spec>

### What to build
...

#### Step 2.1: Write failing test
...

#### Step 2.2: Implement minimal code
...

#### Step 2.3: Verify test passes
...

#### Step 2.4: Aggressive refactor
...

#### Step 2.5: Manual verification (deferred after review phase)
...

### Acceptance criteria
- [ ] ...

## Phase 3: <Title>

**User stories**: <list from spec>

### What to build
...

#### Step 3.1: Write failing test
...

#### Step 3.2: Implement minimal code
...

#### Step 3.3: Verify test passes
...

#### Step 3.4: Aggressive refactor
...

#### Step 3.5: Manual verification
...

### Acceptance criteria
- [ ] ...

<!-- Repeat for each phase -->
</scheme-template>