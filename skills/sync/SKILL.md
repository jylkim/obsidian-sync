---
name: obsidian-sync
description: Sync your current Claude Code session to Obsidian as structured notes. Use when the user says "sync to obsidian", "save session", "write notes to vault", "obsidian sync", or wants to capture session knowledge before ending. Runs a multi-agent pipeline that generates session reports, TIL notes, follow-up tasks, and creative ideas, then writes them to the Obsidian vault. Always use this skill when the user wants to persist session work to their knowledge base.
version: 0.1.0
user-invocable: true
allowed-tools: Bash(git *), Bash(obsidian *), Bash(qmd *), Bash(pgrep *), Bash(mkdir *), Bash(nohup *), Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion
---

# Obsidian Sync

2-phase multi-agent workflow that analyzes the current session and writes structured notes to an Obsidian vault.

## Prerequisites

- Config exists at `~/.claude/plugins/obsidian-sync/config.yaml` (run `/obsidian-config` if missing)
- qmd installed for indexing (`npm install -g @tobilu/qmd`)
- Obsidian app running (for `obsidian` CLI; direct file write works without it)

## Execution Flow

```
Step 0: Load Config
         ↓
Step 1: Gather Session Context
         ↓
Step 2: Phase 1 — 4 Agents in Parallel
  ┌──────────────────┬──────────────────┐
  │  session-writer   │  til-writer      │  (sonnet)
  ├──────────────────┼──────────────────┤
  │  task-writer      │  idea-writer     │  (sonnet / opus)
  └──────────────────┴──────────────────┘
         ↓ (collect all results)
Step 3: Phase 2 — note-reviewer Sequential
  ┌──────────────────────────────────────┐
  │           note-reviewer              │  (sonnet)
  │  (validate, deduplicate, finalize)   │
  └──────────────────────────────────────┘
         ↓
Step 4: Preview & User Selection
         ↓
Step 5: Write Notes to Vault
         ↓
Step 6: Index with qmd
```

---

## Step 0: Load Config

```
Read: ~/.claude/plugins/obsidian-sync/config.yaml
```

Extract: `vault_name`, `vault_path`, `qmd_collection`, `folders`, `default_tags`.

If config is missing:
```
Config not found. Run /obsidian-config to set up your vault first.
```

---

## Step 1: Gather Session Context

Collect information about the current session:

```bash
git status --short
git diff --stat HEAD~5 2>/dev/null || git diff --stat
git log --oneline -10
```

Construct a session summary from the conversation history and git data:

```
Session Context:
- Project: {current working directory name}
- Date: {YYYY-MM-DD}
- Work performed: {summarize main tasks from conversation}
- Files changed: {from git diff stat}
- Key decisions: {extracted from conversation}
- Problems solved: {extracted from conversation}
- Tools/technologies used: {notable APIs, libraries, frameworks}
```

Keep the summary concise — focus on what matters, not exhaustive detail. Cap at roughly 500 words to avoid overwhelming Phase 1 agents.

---

## Step 2: Phase 1 — Parallel Analysis

Launch 4 agents simultaneously in a single message. All receive the same session context.

```
Agent(
    subagent_type="obsidian-sync:session-writer",
    description="Session report note",
    prompt="[Session Context]\n\nGenerate a session report note for Obsidian."
)

Agent(
    subagent_type="obsidian-sync:til-writer",
    description="TIL learning notes",
    prompt="[Session Context]\n\nExtract learnings and compose TIL notes."
)

Agent(
    subagent_type="obsidian-sync:task-writer",
    description="Follow-up task notes",
    prompt="[Session Context]\n\nIdentify follow-up tasks and format for Obsidian."
)

Agent(
    subagent_type="obsidian-sync:idea-writer",
    description="Creative idea notes",
    prompt="[Session Context]\n\nGenerate creative ideas inspired by this session."
)
```

### Agent Summary

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| session-writer | sonnet | Session report | 1 session note |
| til-writer | sonnet | Learnings | 0–N TIL notes |
| task-writer | sonnet | Follow-up tasks | Daily note tasks + 0–N task notes |
| idea-writer | opus | Creative ideas | 0–N idea notes + optional .canvas |

Agents that find nothing to write return "No {type} notes for this session."

---

## Step 3: Phase 2 — Validation

After all Phase 1 agents complete, pass their combined output to the reviewer:

```
Agent(
    subagent_type="obsidian-sync:note-reviewer",
    description="Validate and finalize notes",
    prompt="""
Validate Phase 1 outputs for the Obsidian vault.

## session-writer output:
{session-writer results}

## til-writer output:
{til-writer results}

## task-writer output:
{task-writer results}

## idea-writer output:
{idea-writer results}

## Config:
vault_name: {vault_name}
vault_path: {vault_path}
qmd_collection: {qmd_collection}
folders: {folders}
"""
)
```

The note-reviewer:
1. Validates frontmatter and formatting
2. Checks for duplicates against existing vault content
3. Assigns final filenames and folders
4. Returns a clean list of notes with dispositions (create / append / skip)

---

## Step 4: Preview & Selection

Present the validated notes to the user:

```
AskUserQuestion(
    questions=[{
        "question": "Select notes to sync to Obsidian:",
        "header": "Obsidian Sync Preview",
        "multiSelect": true,
        "options": [
            {"label": "{Session note title}", "description": "{folder}/{filename}"},
            {"label": "{TIL note title}", "description": "{folder}/{filename}"},
            {"label": "Daily Note tasks", "description": "{N} tasks to append"},
            {"label": "{Idea note title}", "description": "{folder}/{filename}"},
            {"label": "Edit before saving", "description": "Review and modify note content"},
            {"label": "Skip all", "description": "Don't sync anything"}
        ]
    }]
)
```

If the user selects "Edit before saving", display the note content and allow modifications before proceeding.

---

## Step 5: Write Notes

Write each selected note to the vault using the best available method.

### Detect Write Method

Check if Obsidian is running (CLI requires the app to be open):

```bash
pgrep -xi obsidian >/dev/null 2>&1 && obsidian vaults 2>/dev/null
```

- If both succeed: use `obsidian` CLI for write operations
- Otherwise: use direct file write as fallback

### Primary — `obsidian` CLI + obsidian-markdown skills

Use the `obsidian` CLI skill for vault operations and obsidian-markdown skill patterns for formatting:

```bash
# Create a note
obsidian vault="${vault_name}" create name="${note_name}" content="${content}" silent

# Append to daily note
obsidian vault="${vault_name}" daily:append content="${daily_tasks}"

# Set properties
obsidian vault="${vault_name}" property:set name="tags" value="${tags}" file="${note_name}"
```

For idea notes with canvas files, use the json-canvas skill:
```bash
# Write canvas file alongside the idea note
obsidian vault="${vault_name}" create name="${canvas_filename}" content="${canvas_json}" silent
```

### Fallback — Direct File Write

When `obsidian` CLI is unavailable or fails:

```bash
mkdir -p "${vault_path}/${folder}"
```

Use the Write tool to create files directly at `${vault_path}/${folder}/${filename}.md`. Include frontmatter in the file content since property:set is unavailable.

Note: Daily note append is skipped in fallback mode (cannot reliably locate the daily note file).

### Write Order

1. Session note first (other notes link to it)
2. TIL notes
3. Task notes
4. Idea notes + canvas files
5. Daily note append (last, references all created notes)

---

## Step 6: Index with qmd

After all notes are written:

```bash
# Synchronous — update file index (fast, enables keyword search immediately)
qmd update --collection "${qmd_collection}"

# Background — generate embeddings (slow, non-blocking)
nohup qmd embed --collection "${qmd_collection}" > /dev/null 2>&1 &
```

`qmd update` runs synchronously so notes are immediately findable via keyword search.
`qmd embed` runs in the background since embedding generation takes time.

If qmd fails, display a warning but do not block — the notes are already saved.

---

## Error Handling

If a Phase 1 agent fails or returns an error:
- Continue with results from the remaining agents
- Note the failure in the preview step
- Do not block the pipeline for a single agent failure

---

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

- `/obsidian-sync` — full interactive workflow
- No quick mode — always runs the full pipeline for quality

---

## Related Resources

- `references/note-templates.md` — complete templates for all note types
- Agent definitions in `agents/` — detailed instructions for each Phase 1 and Phase 2 agent
