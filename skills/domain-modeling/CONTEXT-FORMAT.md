# PROJECT.md format

## Structure

```md
# {Context Name}
<!-- 2-3 sentence concise summary of the entire project scope from a user perspective -->

## Modules
| Module               | Summary                                                        |
|----------------------|----------------------------------------------------------------|
| <!-- Module name --> | <!-- Small one sentence description of the module content --> |

## Language

**Order**:
{A one or two sentence description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## Rules

- When several words exist for one concept, pick the best one and list the others under `_Avoid_`.
- Write one or two sentences per definition. Define what the term is, not what it does.
- Include only terms that are specific to this project. Leave out general programming concepts, such as timeouts, error types, and utility patterns, even if the project uses them a lot.
- Group terms under subheadings when they form natural clusters. Otherwise, use a flat list.
