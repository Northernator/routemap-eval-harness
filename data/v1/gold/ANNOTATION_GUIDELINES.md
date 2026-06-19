# RouteMap Human Annotation Guidelines

## Goal

Label each document passage by its structural role, not just its topic.

The key question:

> What job is this passage doing in the document?

---

## Fields to fill

### gold_role

Choose one:

```text
DEFINE
CLAIM
METHOD
RESULT
LIMITATION
NEXT_STEP
EXAMPLE
BACKGROUND
MODIFY
EXCEPT
SUPPORTS
CONTRADICTS
DEPENDS_ON
```

### gold_entities

List the main entities, separated by `|`.

Example:

```text
sigma|coordination density|critical threshold
```

### gold_operative_status

Choose one:

```text
OPERATIVE
BACKGROUND
EXAMPLE
REJECTED_DRAFT
HISTORICAL
NON_BINDING
UNKNOWN
```

Use `OPERATIVE` if the passage actually establishes, changes, limits, proves, measures, or instructs something.

Use `BACKGROUND` if it merely explains context.

Use `EXAMPLE` if it is illustrative but not structurally binding.

### gold_relation

Choose one:

```text
defines
modifies
excepts
supports
contradicts
depends_on
causes
measures
reports
limits
next_step
background_to
```

### gold_answer_relevant

Use:

```text
1 = this passage is needed to answer the query
0 = not needed
```

---

## Examples

### Example 1

Text:

```text
Sigma is defined as the proportion of mutually constraining degrees of freedom in the system.
```

Labels:

```text
gold_role = DEFINE
gold_entities = sigma|degrees of freedom|constraint
gold_operative_status = OPERATIVE
gold_relation = defines
```

### Example 2

Text:

```text
A previous draft considered a 1/sqrt(2) threshold, but the final test used a different criterion.
```

Labels:

```text
gold_role = LIMITATION
gold_entities = threshold|test criterion
gold_operative_status = HISTORICAL
gold_relation = limits
```

### Example 3

Text:

```text
For example, a legal contract may define rent on page 2 and except it on page 46.
```

Labels:

```text
gold_role = EXAMPLE
gold_entities = legal contract|rent
gold_operative_status = EXAMPLE
gold_relation = background_to
```