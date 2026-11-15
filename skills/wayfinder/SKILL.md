---
name: wayfinder
description: Use when the user wants to plan work that is too large for one agent session.
disable-model-invocation: true
---

Wayfinder turns a loose idea that is too large for one agent session into a map on the issue tracker. It does two things:

1. It finds the destination, which is the goal that the user wants to reach.
2. It plans the way to the destination as a map. The map is a parent issue, and its child issues are tickets.

Each ticket asks one question about one part of the way to the destination. Wayfinder finds and answers these questions one at a time, until no question is left.

The destination can be any outcome, for example a spec to hand off or a decision to make before planning starts. Wayfinder defines the destination first, because the destination decides which tickets exist. The map works in any domain, for example engineering work or course content.

## Decide, do not do the work

Each ticket answers a question with a decision. The map is done when nothing is left to decide before someone starts the work. Wayfinder produces decisions, not deliverables. The only exception is a `task` ticket (see [Ticket types](#ticket-types)).

## Names

The title of an issue is its name. In all text that the human reads, refer to a map or a ticket by its title. This includes your messages and the Decisions so far section of the map. Write the title as the text of a link to the issue.

## The map

The map is one issue with the label `wayfinder:map`. It is the source of truth, and its child issues are the tickets. The [issue tracker](../../../docs/ISSUE-TRACKER.md) document says where the map and its tickets live.

The map is an index. For each decision, it holds a link and a one-line summary. The details stay in the ticket.

### The map body

The map body shows the whole map in short form. Each session loads it once. It does not list the open tickets, because a query for open child issues finds them.

```markdown
## Destination

<The spec, decision, or change that this map leads to. Every session reads this before it chooses a ticket.>

## Notes

<The domain, the skills that every session must use, and the known preferences of the user.>

## Decisions so far

- [<closed ticket title>](link): <one-line summary of the decision>

## Not yet specified

<!-- see "Not yet specified" -->

## Out of scope

<!-- see "Out of scope" -->
```

### Tickets

A ticket is a child issue of the map, and its issue id identifies it. A ticket answers one question that fits in one agent session (about 100K tokens). The body holds only the question:

```markdown
## Question

<The decision or investigation that this ticket resolves.>
```

Each ticket has one `wayfinder:<type>` label. The type is `research`, `prototype`, `grilling`, or `task` (see [Ticket types](#ticket-types)).

A session claims a ticket before it starts work, so that other sessions skip it. To claim a ticket, assign it to the developer who drives the map. An open ticket without an assignee is unclaimed.

Use the native blocking relation of the tracker for dependencies between tickets. The tracker UI then shows the human which tickets are available, without the map. Only if the tracker has no native blocking, list the blocking tickets in the body. A ticket is unblocked when all tickets that block it are closed. An available ticket is open, unblocked, and unclaimed.

When you resolve a ticket, write the answer in a resolution comment, not in the body (see [Work through the map](#work-through-the-map)). If you make an asset for a ticket, link it from the ticket. Do not paste it in.

A context pointer is a link to a ticket or asset with a one-line summary.

## Ticket types

Each ticket is HITL (human in the loop) or AFK (away from keyboard). The agent works on a HITL ticket together with a human, who gives their own answers. The agent works on an AFK ticket alone. A HITL ticket resolves only through that live conversation, so a grilling agent must never answer its own questions.

- `research` (AFK). Use it when a decision needs a fact from outside the working directory, for example documentation, a third-party API, or a local knowledge base. A `/research` subagent resolves it.
- `prototype` (HITL). Use it when the main question is how something must look or behave. Build a cheap, rough artifact that gives the discussion something concrete. Examples are an outline, a first draft, a stub, or UI or logic code from the `/prototype` skill. Link the prototype from the ticket.
- `grilling` (HITL). A conversation through the `/grilling` skill, one question at a time. This is the default type.
- `task` (HITL or AFK). Work that must happen before someone can make a decision, with nothing in it to decide, prototype, or research. Examples are a sign-up for a service to judge its API, access setup, or a data move to see the shape of the data. It is the only type that does work instead of making a decision. It is on the map because it unblocks a decision, not because it reaches the destination. If the agent can do the work alone, it does it (AFK). If not, it gives the human an exact checklist (HITL). The ticket resolves when the work is done. The answer records the work and the facts that later tickets need, for example the location of credentials, new URLs, or row counts.

## Not yet specified

The map is incomplete on purpose. Do not plan what you cannot see yet. The Not yet specified section of the map holds the decisions and investigations that you know will come. You cannot state them yet, because they depend on open questions. Each resolved ticket makes some of them precise enough to become tickets. This repeats until the way to the destination is clear and no tickets are left.

Write each item as a suspected question or as an area to come back to later. Each item is in scope and leads toward the destination, but it is not precise enough for a ticket yet. Write as loosely or as fully as you can. Other people read this section to see where the work is going.

To choose between a ticket and this section, ask if you can state the question precisely now. It does not matter if you can answer it now. If the question is precise, write a ticket, even if the ticket is blocked. If not, write it under Not yet specified. Do not split an item into ticket-sized parts in advance, because one item can become several tickets or none.

Not yet specified does not hold decisions that are already made (Decisions so far), questions that already have an open ticket, or work that is out of scope (the next section).

## Out of scope

The destination sets the scope. Work past the destination is out of scope, and it does not go in Not yet specified. The Out of scope section of the map lists the work that you excluded from this map on purpose. The scope of the work puts it there, not how precise it is.

Out-of-scope work never becomes a ticket, because the map ends at the destination. It comes back only as a new effort, after someone sets a new destination.

An existing ticket can turn out to be past the destination. The charting put it in scope by mistake, or a resolution showed that it is out of scope. Close it, so that it is no longer available. Then add one line to Out of scope with a summary, the reason, and a link to the closed ticket. Do not add it to Decisions so far. That section records the decisions on the way to the destination, and a scope boundary is not one of them.

## Invocation

In both modes, resolve at most one ticket per session. Research tickets are the exception.

### Chart the map

The user starts the skill with a loose idea.

1. Define the destination first, because it sets the scope. Run a `/grilling` session to find the spec, decision, or change that the map leads to.
2. Grill again, breadth-first this time, to find the open decisions and the first steps that are possible now. If nothing goes to Not yet specified, the whole job fits in one session and needs no map. In that case, stop and ask the user how to continue.
3. Create the map with the label `wayfinder:map`. Fill in Destination and Notes. Leave Decisions so far empty. Write the unclear parts in Not yet specified.
4. Create the tickets that you can specify now, as child issues of the map. Then add the blocking relations in a second pass, because an issue needs an id before other issues can refer to it. Everything else stays in Not yet specified.
5. Start one `/research` subagent for each new `research` ticket, all in parallel. Each subagent saves its findings on a throwaway `research/<name>` branch and adds a context pointer to them on the ticket.
6. Stop. Charting takes one session, and you do not resolve a ticket yourself.

### Work through the map

The user starts the skill with a map (URL or number) and, optionally, a ticket.

1. Load the map. Do not load every ticket body.
2. Take the ticket that the user named. If the user named none, take the first available ticket. Before you start work, assign it to the developer who is working the map to claim it.
3. Resolve the ticket with the skills that the Notes section names. If you are not sure which skill to use, use `/grilling`. If you need the details of a related or closed ticket, load its full body.
4. Post the answer as a resolution comment and close the ticket. Add a context pointer to it in Decisions so far on the map.
5. Create the new tickets that you found, then add their blocking relations. Turn the items in Not yet specified that the answer made precise into tickets, and remove them from that section.
6. If the answer shows that a ticket is past the destination, move it to Out of scope as that section describes. This includes the current ticket. Do not resolve it. If the decision makes other tickets wrong, update or delete them.

The user can work on available tickets in parallel. Expect other sessions to change the tracker at the same time.
