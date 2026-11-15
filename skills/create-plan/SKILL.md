---
name: create-plan
description: Turn the current conversation into a spec and save it as a Markdown file in docs/specs/. No interview, only a synthesis of what you already discussed.
---

Turn the current conversation and your knowledge of the codebase into a spec. Do NOT interview the user.

1. Do these tasks in parallel, each in a new subagent with fresh context:
   1a. Explore the repository using codebase-explorere-agents to make sure that the assertions in the conversation are correct, and to understand the current state of the codebase.
   1b. If the user refers to external information that you do not know, such as products, web pages, or design patterns, use web-research-agents to verify.

2. Have exactly as many architect-agents as the user asks for produce RADICALLY different design approaches in parallel. If the user does not specify, only use one agent. Each subagent must sketch the modules it wants to create or modify and the public interfaces where the feature will be tested. They should prefer existing public interfaces to new ones, and put every public interfaces as high as possible. Use as few public interfaces as possible, ideally one.

3. Critically compare all created approaches and synthesize one approach from the best aspects of each. If there is only one approach, use it without synthesis. Ask the user if these modules and this approach match their expectations.

4. When you fully understand the problem and the solution, write the spec file `docs/specs/YYYY-MM-DD-<feature-name>.md` with the template [spec-template.md](spec-template.md).