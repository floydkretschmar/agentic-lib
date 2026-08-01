# ADR format

ADRs live in `docs/adr/` with sequential numbers: `0001-slug.md`, `0002-slug.md`, and so on. Give a new ADR the highest existing number plus one. Create `docs/adr/` only when you need the first ADR.

## Change a decision

Do not change an ADR that is on the main branch. Write a new ADR that supersedes it:

1. In the new ADR, write `Supersedes [ADR NNNN](NNNN-slug.md).` under Relations.
2. In the old ADR, change only the status line to `Status: Superseded by [ADR NNNN](NNNN-slug.md)`.

You can still correct an ADR that exists only on an unmerged branch.

## Template

Write each ADR from [adr-template.md](adr-template.md). An ADR records the decision and its reason, and it can be very short.

### What qualifies

- Architectural shape. "We use a monorepo." "The write model is event-sourced, and a projection builds the read model in Postgres."
- Integration patterns between contexts. "Ordering and Billing communicate via domain events, not synchronous HTTP."
- Technology choices that carry lock-in, such as the database, message bus, auth provider, or deployment target. Record a library only if it takes a quarter to replace.
- Boundary and scope decisions. "The Customer context owns customer data, and other contexts reference it by ID only." Record the explicit no decisions as well as the yes decisions.
- Deliberate deviations from the obvious path. "We use manual SQL instead of an ORM because X." Record each decision where a reasonable reader assumes the opposite, so that the next engineer does not "fix" it.
- Constraints not visible in the code. "We cannot use AWS because of compliance requirements." "Response times must be under 200ms because of the partner API contract."
- Rejected alternatives when the rejection is not obvious. If you picked REST over GraphQL for subtle reasons, record it, or someone will suggest GraphQL again in six months.
