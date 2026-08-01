---
name: wayfinder
description: Plan a huge chunk of work, more than one agent session can hold, as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
disable-model-invocation: true
---

This skill starts from a loose idea that is too big for one agent session, when the way to the destination is not visible yet. It charts the way as a shared map on the issue tracker of the repo. Then it resolves the decision tickets of the map one at a time until the way is clear. A decision ticket is a question that a decision answers, not a slice of a build to execute.

The destination can be a spec to hand off and iterate on, or a decision to lock before planning starts. It can also be a change made in place, such as a data-structure migration. Charting starts with naming the destination, because it shapes every ticket. The map works in any domain, such as engineering work or course content.

## Plan, do not do the work

Wayfinder plans by default, and each ticket resolves a decision. The map is done when nothing is left to decide before someone does the work. If you want to do the work yourself, you are usually at the edge of the map, so hand off. Produce decisions, not deliverables, unless the Notes of the effort carry execution into the map.

## Refer by name

Every map and ticket is an issue, so its title is its name. Refer to it by that name in everything the human reads, such as your narration and the Decisions so far of the map. Never use a bare id, number, or slug, because a list like `#42, #43, #44` is unreadable. Make the name the text of a link to the id and URL.

## The map

The map is a single issue on the issue tracker of the repo, with the label `wayfinder:map`. It is the canonical artifact, and its tickets are its child issues.

The map is an index. It gives each decision a one-line gist and a link, and the detail lives only in the ticket.

The tracker decides where the map, its child tickets, blocking, and frontier queries live. Normally, you already have the issue tracker. If not, run `/setup-matt-pocock-skills`. The "Wayfinding operations" section of the tracker doc describes how this repo expresses them. If you have no tracker, use the local-markdown tracker as the default.

### The map body

The map body is the whole map at low resolution, and each session loads it once. It does not list open tickets, because a query finds them as open child issues.

```markdown
## Destination

<what reaching the end of this map looks like — the spec, decision, or change this effort is finding its way to. One or two lines; every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for the detail the ticket holds -->

- [<closed ticket title>](link) — <one-line gist of the answer>

## Not yet specified

<!-- see "Fog of war": in-scope fog you can't ticket yet; graduates as the frontier advances -->

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed, never graduates -->
```

### Tickets

The issue id of the tracker identifies a ticket. Its body is the question, sized to one agent session of 100K tokens:

```markdown
## Question

<the decision or investigation this ticket resolves>
```

Each ticket has a `wayfinder:<type>` label, where the type is `research`, `prototype`, `grilling`, or `task` (see [Ticket Types](#ticket-types)).

Before any work, a session claims the ticket, so that concurrent sessions skip it. To claim it, the session assigns it to the developer who drives the map. An open, unassigned ticket is unclaimed.

Blocking uses the native dependency relationship of the tracker. The tracker UI then shows the human which tickets are available without opening the map. Only a tracker without native blocking falls back to a convention in the body. A ticket is unblocked when every ticket that blocks it is closed. The frontier is the set of open, unblocked, unclaimed child tickets.

Record the answer at resolution, not in the body (see [Work through the map](#work-through-the-map)). Link the assets that you create for a ticket from the issue instead of pasting them in.

## Ticket types

Every ticket is HITL (human in the loop) or AFK (away from keyboard). The agent works a HITL ticket with a human who speaks for themselves, and an AFK ticket alone. A HITL ticket resolves only through that live exchange. A grilling agent that answers its own questions breaks this rule.

- Research (AFK): Use it when a decision waits on a fact from outside the current working directory, such as documentation, third-party APIs, or local knowledge bases. A `/research` subagent resolves it.
- Prototype (HITL): Use it when "how should it look" or "how should it behave" is the key question. Build a cheap, rough artifact that makes the discussion concrete, such as an outline, a rough take, a stub, or UI or logic code from the /prototype skill. The ticket links the prototype as an asset.
- Grilling (HITL): A conversation through the /grilling and /domain-modeling skills, one question at a time. This is the default type.
- Task (HITL or AFK): Manual work that must happen before you can make a decision, with nothing to decide, prototype, or research. Examples are signing up for a service to judge its API, provisioning access, and moving data to see its shape. It is the only type that does work instead of deciding. It is on the map because it unblocks a decision, not because it delivers the destination. The agent does the work alone if it can (AFK), and otherwise gives the human a precise checklist (HITL). The ticket resolves when the work is done. The answer records what was done and the facts that later tickets depend on, such as the location of credentials, new URLs, or row counts.

## Fog of war

The map is incomplete on purpose, so do not chart what you cannot see yet. The fog of war lies beyond the live tickets. It holds the decisions and investigations that you know are coming but cannot pin down yet, because they depend on open questions. Each resolved ticket clears the fog ahead of it, and whatever you can now specify graduates into new tickets. This repeats until the way to the destination is clear and no tickets remain.

Write the fog in the Not yet specified section of the map, as a suspected question or an area to revisit later. Everything in it is in scope and lies toward the destination, but it is not sharp enough for a ticket yet. Write as loosely or as fully as you can see. Collaborators also read this section to learn where the effort is going.

To choose between fog and a ticket, ask whether you can state the question precisely now, not whether you can answer it now.

- Write a ticket when the question is already sharp, even if it is blocked.
- Write it under Not yet specified when you cannot phrase it that sharply yet. Do not cut the fog into ticket-sized pieces in advance, because a patch of fog can graduate into several tickets or into none.

Not yet specified excludes what is already decided (Decisions so far), what is already a live ticket, and what is out of scope (the next section).

## Out of scope

The destination fixes the scope, so work beyond it is out of scope, not fog. It goes in the Out of scope section of the map, for work that you ruled out of this effort on purpose. Work goes there because of its scope, not its sharpness.

Out-of-scope work never graduates, because the frontier stops at the destination. It comes back only as a fresh effort, after someone redraws the destination.

An existing ticket can turn out to lie past the destination, because charting wrongly scoped it in or because a resolution exposed it. Close it, so that it is off the frontier. Then add one line to the Out of scope section with the gist, the reason, and a link to the closed ticket. Keep it out of Decisions so far. That section records the way actually walked, and a scope boundary is not a step on it.

## Invocation

In both modes below, resolve at most one ticket per session, except for research tickets.

### Chart the map

The user invokes the skill with a loose idea.

1. Name the destination first, because it fixes the scope. Run a `/grilling` and `/domain-modeling` session to pin down the spec, decision, or change that the map leads to.
2. Map the frontier. Grill again, breadth-first this time, to find the open decisions and the first steps that you can take now. If this shows no fog, the whole job fits in one session and needs no map. Stop and ask the user how they want to continue.
3. Create the map (label `wayfinder:map`). Fill in Destination and Notes, leave Decisions so far empty, and sketch the fog into Not yet specified.
4. Create the tickets that you can specify now as child issues of the map. Then add the blocking edges in a second pass, because issues need ids before they can reference each other. Everything else stays in Not yet specified.
5. Start a `/research` subagent for each new `research` ticket, all in parallel. Each subagent saves its findings on a throwaway `research/<name>` branch, with a context pointer from the ticket.
6. Stop. Charting takes one session and resolves no tickets by hand.

### Work through the map

The user invokes the skill with a map (URL or number) and optionally a ticket.

1. Load the map, not every ticket body.
2. Use the ticket that the user named, or else the first frontier ticket in order. Before any work, claim it by assigning it to yourself.
3. Resolve it with the skills that the `## Notes` block names, or with `/grilling` and `/domain-modeling` if in doubt. Fetch the full body of a related or closed ticket when you need its detail.
4. Post the answer as a resolution comment, close the issue, and append a context pointer to Decisions so far on the map.
5. Create newly found tickets, then add their blocking edges. Graduate the fog that the answer made specifiable into tickets, and remove it from Not yet specified. If the answer shows that any ticket, this one included, sits beyond the destination, rule it out of scope instead of resolving it. If the decision invalidates other tickets, update or delete them.

The user can work unblocked tickets in parallel, so expect other sessions to edit the tracker at the same time.
