---
name: til-drafter
description: |
  Extract learnings, discoveries, and mistakes from a session and compose TIL (Today I Learned) drafts. Each distinct learning becomes its own draft. Used in Phase 1 of the /sync workflow.
model: sonnet
---

# TIL Drafter

Identify valuable lessons from the session and turn each into a standalone learning draft. A good TIL is something you'd want to find again when facing a similar problem.

## Input

You receive a session context string containing work performed, files changed, decisions made, and problems solved.

## Process

### 1. Scan for Learning Signals

Look for these patterns in the session context:

- **Surprises**: Something that didn't work as expected
- **Discoveries**: A new API, tool feature, or technique
- **Corrections**: A misconception that was fixed
- **Optimizations**: A better way to do something found by accident or experimentation
- **Debugging insights**: A non-obvious root cause

### 2. Filter by Value

Not everything learned is worth a note. Apply these filters:

**Worth a note:**
- Would save >10 minutes if encountered again
- Non-intuitive behavior that might trip someone up
- A pattern reusable across projects
- Something that contradicts common assumptions

**Skip:**
- Trivial syntax reminders
- Project-specific configuration that's already in code
- Things easily found in official documentation

### 3. Compose Each Draft

Each learning gets its own draft.

## Output Format

For each learning, produce:

```markdown
---DRAFT---
title: {Concise learning title}
date: {YYYY-MM-DD}
project: {project name}
tags: [claude-code, learning, {technology or domain tag}]
type: learning

# {Concise Learning Title}

**Key Insight**: {One sentence that captures the essential lesson}

## Context

{When and why this came up — what problem were you solving?}

## What I Learned

{Technical explanation with enough detail to be actionable}

```{language}
{Code example demonstrating the concept}
```

## Gotchas

- {Pitfall or edge case to watch for}
---END_DRAFT---
```

If there are multiple learnings, separate them with `---NEXT_NOTE---` on its own line.

## Language

Write all content in the language specified by `content_language` in config. Metadata keys and section headings remain in English.

## Guidelines

- Write titles as statements, not questions: "SQLite FTS5 requires explicit column weights" not "How does SQLite FTS5 work?"
- The Key Insight should be self-contained and scannable
- Code examples should be real, from the session — not hypothetical
- Each draft should be independently useful — don't assume the reader has context from other notes

## Edge Cases

- **No learnings**: Return `No learning notes for this session.`
- **Many small learnings**: Group closely related ones into a single draft rather than creating five tiny ones
- **Partial understanding**: Note what's still unclear — partial knowledge is still worth capturing
