---
name: create-plan
description: Use turn the current conversation into a spec.
---

Turn the current conversation and your knowledge of the codebase into a spec. Do NOT interview the user.

1. Do these tasks yourself so you have all relevant information in your context:
   1a. Explore the repo to make sure that the assertions in the conversation are correct, and to understand the current state of the codebase.
   1b. If the user refers to external information that you do not know, such as products, web pages, or design patterns, use web search.

2. Have three architect-agents in parallel produce RADICALLY different design approaches. Each subagent must sketch the seams where you will test the feature. A seam is a place where a test attaches to the code. Prefer existing seams to new ones, and put every seam as high as possible. Use as few seams as possible, ideally one.

3. Critically compare the three approaches and synthesize one approach. You may mix and match different part of approaches, or you can choose to follow one approach only if it is cleary the best one. Ask the user if these modules and this approach match their expectations.

4. When you fully understand the problem and the solution, write the spec file `docs/specs/YYYY-MM-DD-<feature-name>.md` with the template [spec-template.md](spec-template.md).

5. Have a business-agent review the spec and find gaps and inconsistencies. The reviewer must report with NEEDS_CHANGES or PASSED. Repeat review until the reviewer finds no more issues.

6. Review [ADR.md](ADR.md) to identify any candidates for ADRs based on the current conversation and spec file. 