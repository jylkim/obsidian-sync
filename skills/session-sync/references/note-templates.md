# Note Templates Reference

Templates for each note type produced by the /sync workflow. Agents reference these for consistent formatting.

## Frontmatter Field Reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| date | date | Yes | YYYY-MM-DD format |
| tags | list | Yes | Always includes `claude-code` |
| type | string | Yes | `session-note`, `learning`, `task`, or `idea` |
| project | string | Yes | Working directory name |
| source | wikilink | TIL only | Links to session note |
| priority | string | Task only | P0, P1, P2, P3 |
| status | string | Task only | open, in-progress, done |
| category | string | Idea only | architecture, product, workflow, exploration |
| canvas | wikilink | Idea only | Links to .canvas file if exists |

## Obsidian Formatting Conventions

### Callout Types Used

| Callout | Purpose | Agent |
|---------|---------|-------|
| `> [!summary]` | Session overview | session-drafter |
| `> [!tip]` | Key insight | til-drafter |
| `> [!todo]` | Next action | task-drafter |
| `> [!spark]` | Inspiration source | idea-drafter |
| `> [!question]` | Open question | any |

### Wikilink Patterns

- `[[Session: YYYY-MM-DD description]]` — link to session note
- `[[Concept Name]]` — link to a concept (creates if doesn't exist)
- `[[#Heading]]` — link within the same note

### Tag Conventions

- `#claude-code` — on every generated note
- `#session`, `#learning`, `#task`, `#idea` — type tags
- `#{technology}` — e.g., `#python`, `#react`, `#sqlite`
- `#P0` through `#P3` — priority tags on tasks

## Session Note Template

```markdown
---
date: {YYYY-MM-DD}
project: {project name}
tags:
  - claude-code
  - session
  - {topic tags}
type: session-note
---

# {Brief Description}

> [!summary]
> {2-3 sentence overview}

## Accomplishments

- {Specific accomplishment}

## Problems & Solutions

### {Problem Title}

**Problem**: {description}
**Solution**: {how it was resolved}
**Takeaway**: {lesson for next time}

## Decisions

- **{Decision}**: {choice} — because {reason}

## Rejected Approaches

### {Approach Title}

**What**: {Approach that was considered but not taken}
**Why not**: {Reason for rejection}

## Open Questions

- {Unresolved question}

## Related

- [[{wikilink}]]
```

## Learning Note (TIL) Template

```markdown
---
date: {YYYY-MM-DD}
project: {project name}
tags:
  - claude-code
  - learning
  - {technology tag}
type: learning
source: "[[Session: {description}]]"
---

# {Concise Learning Title}

> [!tip] Key Insight
> {One sentence takeaway}

## Context

{When and why this came up}

## What I Learned

{Technical explanation}

```{language}
{Code example}
```

## Gotchas

- {Pitfall to watch for}

## Related

- [[{wikilink}]]
```

## Task Note Template

```markdown
---
date: {YYYY-MM-DD}
project: {project name}
tags:
  - claude-code
  - task
  - {topic tag}
type: task
priority: {P0|P1|P2|P3}
status: open
---

# {Descriptive Title}

> [!todo] Next Action
> {Specific first step}

## Context

{Background and motivation}

## Steps

- [ ] {Step 1}
- [ ] {Step 2}
- [ ] {Step 3}

## Related Files

- `{path/to/file}` — {relevance}

## Notes

{Additional context}
```

## Idea Note Template

```markdown
---
date: {YYYY-MM-DD}
project: {project name}
tags:
  - claude-code
  - idea
  - {category tag}
type: idea
category: {architecture|product|workflow|exploration}
canvas: "[[{canvas-filename}]]"
---

# {Compelling Title}

> [!spark] Inspiration
> {What triggered this idea}

## Core Idea

{Clear explanation}

## Why It Matters

{Problem solved or opportunity created}

## Possible Approach

{Concrete first steps}

## Open Questions

- {Key uncertainty}

## Related

- [[{wikilink}]]
```

