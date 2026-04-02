---
name: session-sync
description: Sync your current coding session to Obsidian as structured notes.
---

# Session Sync

2-phase multi-agent workflow that analyzes the current session and writes structured notes to an Obsidian vault.

## Prerequisites

- Config exists at `resolved obsidian-sync config path` (run `/configure` if missing)
- qmd installed for indexing (`npm install -g @tobilu/qmd`)
- Obsidian app running (for `obsidian` CLI; direct file write works without it)
- `obsidian:obsidian-markdown` skill is available
- `obsidian:json-canvas` skill is available

## Execution Flow

```text
Step 0: Load Config
         ↓
Step 1: Gather Session Context
         ↓
Step 2: Phase 1 — 4 Agents in Parallel
  ┌──────────────────┬──────────────────┐
  │  session-drafter │  til-drafter     │  (gpt-5.4-mini)
  ├──────────────────┼──────────────────┤
  │  task-drafter    │  idea-drafter    │  (gpt-5.4-mini / gpt-5.4)
  └──────────────────┴──────────────────┘
         ↓ (collect all results)
Step 3: Phase 2 — note-reviewer Sequential
  ┌──────────────────────────────────────┐
  │           note-reviewer              │  (gpt-5.4-mini)
  │  (validate, deduplicate, finalize)   │
  └──────────────────────────────────────┘
         ↓
Step 4: Preview & User Selection
         ↓
Step 5: Write Notes to Vault
         ↓
Step 6: Link to Daily Note
         ↓
Step 7: Index with qmd
```

## Step 0: Load Config

Read the config from `resolved obsidian-sync config path`.

Extract: `vault_name`, `vault_path`, `qmd_collection`, `search_mode`, `folders`, `default_tags`, `content_language`.

If config is missing:

```text
Config not found. Run /configure to set up your vault first.
```

## Step 1: Gather Session Context

Collect information about the current session by combining conversation history with git data.

### 1a. Identify Session Commits

Scan the conversation history for commits made during this session. Extract their hashes to determine the exact range of committed changes.

If commits were made during the session, run:

```bash
git log --oneline {earliest_commit_hash}^..{latest_commit_hash}
git diff --stat {earliest_commit_hash}^..{latest_commit_hash}
```

If no commits were made during the session, skip these commands.

### 1b. Identify Uncommitted Changes

```bash
git status --short
git diff --stat
git diff --staged --stat
```

### 1c. Construct Session Context

Build a lightweight session context as a roadmap for Phase 1 agents. This is an orientation aid, not the primary source of truth — Phase 1 and Phase 2 subagents inherit the parent conversation context via `fork_context: true`, so they can inspect the full session natively.

```text
Session Context:
- Project: {current working directory name}
- Date: {YYYY-MM-DD}
- Parent Context: inherited from the main session
- Work performed: {brief list of main topics/tasks}
- Committed changes: {from 1a — commit messages and files changed, or "None"}
- Uncommitted changes: {from 1b — staged/unstaged diffs and untracked files, or "None"}
- Key decisions: {brief list}
- Problems solved: {brief list}
- Rejected approaches: {brief list}
- Tools/technologies used: {notable APIs, libraries, frameworks}
- Content language: {from config content_language}
```

Keep this concise — it is a roadmap, not a comprehensive record.

Also detect Obsidian CLI availability (used by Phase 2 reviewer and Step 5 write):

```bash
pgrep -xi obsidian >/dev/null 2>&1 && obsidian vaults 2>/dev/null
```

Store the result as `obsidian_cli: true/false` for later steps.

## Step 2: Phase 1 — Parallel Analysis

Launch 4 subagents with `fork_context: true`. Each subagent receives the session context summary plus the full parent conversation context.

Open these prompt files and use their contents as the worker prompts:

- `./support/agents/session-drafter.md` with model `gpt-5.4-mini` and reasoning effort `xhigh`
- `./support/agents/til-drafter.md` with model `gpt-5.4-mini` and reasoning effort `xhigh`
- `./support/agents/task-drafter.md` with model `gpt-5.4-mini` and reasoning effort `xhigh`
- `./support/agents/idea-drafter.md` with model `gpt-5.4` and reasoning effort `xhigh`

When launching, prepend a short session context summary to each prompt so the agent can orient quickly before consulting inherited context.


### Agent Summary

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| session-drafter | gpt-5.4-mini | Session report | 1 session note |
| til-drafter | gpt-5.4-mini | Learnings | 0–N TIL notes |
| task-drafter | gpt-5.4-mini | Follow-up tasks | 0–N task notes |
| idea-drafter | gpt-5.4 | Creative ideas | 0–N idea notes + optional .canvas |

Agents that find nothing to write return "No {type} notes for this session."

## Step 3: Phase 2 — Validation

After all Phase 1 agents complete, pass til, task, and idea output to the reviewer. Session-drafter output bypasses review — it is created with filename `{YYYY-MM-DD}-{slug}.md` in the sessions folder, where `{slug}` is derived from the drafter's `title` (lowercase, hyphens, max 50 chars). If a file with that name already exists, append a numeric suffix (`-1`, `-2`, …) to avoid overwriting.

Launch a review subagent with `fork_context: true` using `./support/agents/note-reviewer.md`, model `gpt-5.4-mini`, and reasoning effort `xhigh`.

Pass the Phase 1 outputs inline together with:

- `vault_path`
- `vault_name`
- `qmd_collection`
- `search_mode`
- `obsidian_cli`
- `folders`


The note-reviewer:
1. Checks for duplicates against existing vault content
2. Assigns final filenames and folders
3. Returns drafts with dispositions (create / append / skip)

## Step 4: Preview & Approval

Present all notes in a single numbered list and let the user choose which to save. Session notes are always saved — exclude them from the list.

If there are no notes to review (all session or no Phase 1 output), skip this step.

### Display Format

Print a numbered list with type tag and title for each note:

```text
Notes ready to save:

1. [Learning] SQLite FTS5 requires explicit column weights
2. [Learning] Local session context can replace JSONL lookups
3. [Task] Add error handling for missing config
4. [Idea] Event-driven sync pipeline

Enter note numbers to save (e.g. "1,3,4"), "all" to save all, or "none" to skip all.
```

Then wait for the user's response. Do not use forced structured questions for this step — let the user reply naturally.

### Handling Responses

- `all` → save all listed notes
- `none` → skip all listed notes
- Comma-separated numbers (e.g. `1,3,4`) → save only those notes
- If the user asks to see a note's content, display it and re-prompt
- If the user requests edits, apply them and re-prompt

## Step 5: Format & Write Notes

Convert selected drafts into Obsidian-formatted notes and write to the vault.

### 5a. Format Drafts → Obsidian Notes

Convert each draft to Obsidian-native format following `references/note-templates.md`.

Use the `obsidian:obsidian-markdown` skill for Obsidian-specific syntax:

- Add YAML frontmatter (date, tags, type, etc.)
- Include `obsidian-sync` and `codex` in generated note tags
- Convert plain text cues to Obsidian syntax (callouts, wikilinks, highlights)
- Convert notable concepts in body text to inline `[[wikilinks]]`
- Add `session` wikilink to all non-session notes using the session filename (e.g. `session: "[[2026-03-31-slug]]"`)
- Populate `## Related` section with wikilinks from the reviewer's **Related** field
- Add wikilink embeds for diagram files (`![[{canvas-filename}]]`) in idea notes

For idea drafts that include a `---DIAGRAM---` block, use the `obsidian:json-canvas` skill:

- Convert the diagram description into a valid `.canvas` file
- Assign it to the `canvas` folder from config

### 5b. Write to Vault

Use the `obsidian_cli` flag from Step 1 to choose the write method.

**Primary — `obsidian` CLI**:

```bash
obsidian vault="${vault_name}" create name="${note_name}" content="${content}" silent
obsidian vault="${vault_name}" property:set name="tags" value="${tags}" file="${note_name}"
```

**Fallback — Direct File Write**:

```bash
mkdir -p "${vault_path}/${folder}"
```

Write the file directly at `${vault_path}/${folder}/${filename}`. Include frontmatter in the file content since `property:set` is unavailable.

### Session Filename Collision Check

Before writing the session note, check if the target file already exists.

**Primary** (`obsidian_cli: true`):

```bash
obsidian vault="${vault_name}" files folder="${sessions_folder}"
```

**Fallback** (`obsidian_cli: false`):

Search `${vault_path}/${sessions_folder}/${YYYY-MM-DD}-${slug}*.md`.

If `{YYYY-MM-DD}-{slug}.md` exists, append a numeric suffix (`-1`, `-2`, …) until no collision.

### Write Order

1. Session note first (other notes link to it)
2. TIL notes
3. Task notes
4. Idea notes + canvas files

## Step 6: Link to Daily Note

Append wikilinks of the written notes to today's Obsidian daily note so they are discoverable from the daily hub.

Collect the filename (without `.md` extension) and H1 heading of each note written in Step 5. Build a wikilink block using `[[filename|Type: heading]]` alias syntax, with the session note as the parent and other notes nested under it:

```markdown
## Agent Session
- [[{session-filename}|Session: {session heading}]]
	- [[{learning-filename}|Learning: {learning heading}]]
	- [[{task-filename}|Task: {task heading}]]
	- [[{idea-filename}|Idea: {idea heading}]]
```

If the session produced no sub-notes (TIL, task, idea), the session link still appears as a standalone item. When sync runs multiple times in a day, each session becomes a separate top-level item under the same heading.

Before appending, read the current daily note to check for already-linked filenames and exclude duplicates.

**Primary — `obsidian` CLI** (`obsidian_cli: true`):

```bash
obsidian daily:read
obsidian daily:append content="${wikilink_block}"
```

**Fallback** (`obsidian_cli: false`):

```bash
obsidian daily:path
```

Use the returned path to read the daily note for duplicate checking, then append the wikilink block. If `daily:path` also fails, skip this step with a warning — the notes themselves are already saved.

## Step 7: Index with qmd

After all notes are written and the daily note is updated:

```bash
qmd update --collection "${qmd_collection}"
```

If `search_mode` is `hybrid`, also run embedding in the background:

```bash
nohup qmd embed --collection "${qmd_collection}" > /dev/null 2>&1 &
```

If `search_mode` is `keyword`, skip embedding.

If qmd fails, display a warning but do not block — the notes are already saved.

## Error Handling

If a Phase 1 agent fails or returns an error:
- Continue with results from the remaining agents
- Note the failure in the preview step
- Do not block the pipeline for a single agent failure

## Quick Reference

### When to Use

- End of a productive work session
- After completing a feature or fixing a significant bug
- Before switching projects
- When you want to capture knowledge for future reference

### When to Skip

- Very short session with trivial changes
- Only reading/exploring code
- Quick question-and-answer

### Arguments

- `/session-sync` — full interactive workflow
- No quick mode — always runs the full pipeline for quality

## Related Resources

- `references/note-templates.md` — complete templates for all note types
- Agent definitions in `support/agents/` — detailed instructions for each Phase 1 and Phase 2 agent
