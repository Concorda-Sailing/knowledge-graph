---
node_id: <domain::subkind::name>
node_kind: domain
subkind: <role|resource|relationship|attribute>
definition_status: stub
last_reviewed: <YYYY-MM-DD>
last_reviewed_against_hash: <node structural_hash>
---

<!--
TEMPLATE — Domain dossier.

Quality bar: written for the LLM collaborator first. Use enumerated lists,
concrete predicates, and short sentences. A non-engineer being able to
read this is a useful proxy for prose clarity, not the calibration
target.

Validator enforcement (per `kg logigraph validate`) is narrow and
subkind-specific:

  Role subkind — REQUIRED sections:
    - ## Plain definition
    - ## They can

  Other subkinds (resource / relationship / attribute) — NO required
  sections today; validate.py only enforces the role-subkind list above.

Recommended sections (not validator-enforced, but expected for quality
domain dossiers — every shipped role dossier should grow these once it
leaves `definition_status: stub`):
  - ## They cannot
  - ## Becomes one when
  - ## Stops being one when
  - ## Examples / counter-examples
  - ## Surfaces       (where the role is checked / displayed in code)

The body sections shown below this comment block are an older
template that doesn't match the role-subkind validator. They remain
as a starting point for resource / relationship / attribute subkinds
(which currently have no enforced shape). Role-subkind dossiers
should override the section list with `## Plain definition` and
`## They can` at minimum.

The Decision table is mandatory: enumerate the realistic boundary
conditions and the domain concept's verdict on each (e.g. "does this
predicate qualify someone as an X?"). Narrative examples + counter-examples
support prose clarity but don't substitute for an enumerated table.
-->

# <Domain concept title>

## The thing

<Single paragraph: what is this concept? For a role: who is this person and
what predicate qualifies them? For a resource: what row/entity does this name?
What is its identity key? For a relationship: what two nodes does it connect,
and under what conditions? For an attribute: what field, what type, and what
does it control?>

## Why it exists

<Rationale. What real-world fact, design constraint, or business decision
motivated separating this into its own node? Why is it a first-class concept
rather than an implementation detail or a property of another node? This is the
section that lets the LLM judge whether a proposed refactor preserves intent.>

## Examples

- <Concrete positive case 1: who/what qualifies, and why.>
- <Concrete positive case 2 covering a different path.>
- <Concrete positive case 3 covering a different angle.>

## Counter-examples (what this is NOT)

- <Adjacent concept 1 that could be confused with this: how it differs.>
- <Misconception 2: this concept does **not** ___.>

## Decision table

<Required. Enumerate the realistic boundary conditions and the verdict
on each (e.g. "does this predicate hold?", "is this resource visible?",
"is this relationship active?"). Use Markdown tables.>

| <Condition 1> | <Condition 2> | <...> | Outcome |
|---------------|---------------|-------|---------|
| <value>       | <value>       | <...> | <verdict> |
| <value>       | <value>       | <...> | <verdict> |

<Optional notes after the table: known inconsistencies, legacy paths,
future-state intent.>

## Edge cases

- <Subtlety not captured in the table.>
- <Interaction with another domain concept or rule.>
- <Lifecycle edge: what happens when a parent resource is deleted?
  What happens during a role transition?>

## Surfaces

<Where does this concept live in code? Which models, helpers, or
chokepoints are the canonical source of truth? The structured form
is `claims_code` on the node JSON, with current line ranges. This
section explains the *shape*: which surfaces enforce, which display,
which emit, which only check.>

- Backend: <description>
- Frontend: <description>
- Mobile / other: <description, if any>

## Open questions

- <Unresolved design or implementation question, if any.>
