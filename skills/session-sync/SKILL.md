---
name: session-sync
description: Sync your current Claude Code session to Obsidian as structured notes. Use when the user says "sync to obsidian", "save session", "write notes to vault", "obsidian sync", or wants to capture session knowledge before ending. Runs a multi-agent pipeline that generates session reports, TIL notes, follow-up tasks, and creative ideas, then writes them to the Obsidian vault. Always use this skill when the user wants to persist session work to their knowledge base.
version: 0.1.0
user-invocable: true
allowed-tools: Bash(git *), Bash(obsidian *), Bash(qmd *), Bash(pgrep *), Bash(mkdir *), Bash(nohup *), Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion, Skill(obsidian-markdown), Skill(json-canvas)
---

# Obsidian Session Sync

2-phase multi-agent workflow that analyzes the current session and writes structured notes to an Obsidian vault.

## Prerequisites

- Config exists at `~/.claude/plugins/obsidian-sync/config.yaml` (run `/configure` if missing)
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
  │  session-drafter   │  til-drafter      │  (sonnet)
  ├──────────────────┼──────────────────┤
  │  task-drafter      │  idea-drafter     │  (sonnet / opus)
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
Step 6: Link to Daily Note
         ↓
Step 7: Index with qmd
```

---

## Step 0: Load Config

```
Read: ~/.claude/plugins/obsidian-sync/config.yaml
```

Extract: `vault_name`, `vault_path`, `qmd_collection`, `folders`, `default_tags`.

If config is missing:
```
Config not found. Run /configure to set up your vault first.
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

Also detect Obsidian CLI availability (used by Phase 2 reviewer and Step 5 write):

```bash
pgrep -xi obsidian >/dev/null 2>&1 && obsidian vaults 2>/dev/null
```

Store the result as `obsidian_cli: true/false` for later steps.

---

## Step 2: Phase 1 — Parallel Analysis

Launch 4 agents simultaneously in a single message. All receive the same session context.

```
Agent(
    subagent_type="obsidian-sync:session-drafter",
    description="Session report note",
    prompt="[Session Context]\n\nGenerate a session report note for Obsidian."
)

Agent(
    subagent_type="obsidian-sync:til-drafter",
    description="TIL learning notes",
    prompt="[Session Context]\n\nExtract learnings and compose TIL notes."
)

Agent(
    subagent_type="obsidian-sync:task-drafter",
    description="Follow-up task notes",
    prompt="[Session Context]\n\nIdentify follow-up tasks and format for Obsidian."
)

Agent(
    subagent_type="obsidian-sync:idea-drafter",
    description="Creative idea notes",
    prompt="[Session Context]\n\nGenerate creative ideas inspired by this session."
)
```

### Agent Summary

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| session-drafter | sonnet | Session report | 1 session note |
| til-drafter | sonnet | Learnings | 0–N TIL notes |
| task-drafter | sonnet | Follow-up tasks | 0–N task notes |
| idea-drafter | opus | Creative ideas | 0–N idea notes + optional .canvas |

Agents that find nothing to write return "No {type} notes for this session."

---

## Step 3: Phase 2 — Validation

After all Phase 1 agents complete, pass til, task, and idea output to the reviewer. Session-drafter output bypasses review — it is always created with filename `{YYYY-MM-DD}-session.md` in the sessions folder.

```
Agent(
    subagent_type="obsidian-sync:note-reviewer",
    description="Check duplicates and assign filenames",
    prompt="""
Check drafts for duplicates and assign filenames.

## til-drafter output:
{til-drafter results}

## task-drafter output:
{task-drafter results}

## idea-drafter output:
{idea-drafter results}

## Config:
vault_path: {vault_path}
vault_name: {vault_name}
qmd_collection: {qmd_collection}
search_mode: {search_mode}
obsidian_cli: {true/false from Step 5b detection}
folders: {folders}
"""
)
```

The note-reviewer:
1. Checks for duplicates against existing vault content
2. Assigns final filenames and folders
3. Returns drafts with dispositions (create / append / skip)

---

## Step 4: Preview & Selection

Use AskUserQuestion to let the user choose which notes to sync. Requirements:

- **Session notes are always approved** — do not ask the user about them. Proceed directly to write.
- **One question per type**: Learnings, Tasks, Ideas each get their own separate multi-select question. Never combine multiple types into a single question.
- **Skip empty types**: only ask about types that have content
- **Individual selection**: each note is its own option, labeled by title
- **Content preview**: include the target path and a 2–3 line content excerpt in each option's description so the user can judge without reading the full note
- If the user provides custom input, display the full note content and allow edits before proceeding

---

## Step 5: Format & Write Notes

Convert selected drafts into Obsidian-formatted notes and write to the vault.

### 5a. Format Drafts → Obsidian Notes

Use the **obsidian-markdown** skill to convert each draft:

- Add YAML frontmatter (title, date, tags, type, etc.)
- Convert plain text cues to Obsidian syntax (callouts, wikilinks, highlights)
- Add `source` wikilinks between related notes using filenames from the reviewer
- Add wikilink embeds for diagram files (`![[{canvas-filename}]]`) in idea notes

For idea drafts that include a `---DIAGRAM---` block, use the **json-canvas** skill to:

- Convert the diagram description into a valid JSON Canvas file
- Assign to the `canvas` folder from config

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

Use the Write tool to create files directly at `${vault_path}/${folder}/${filename}`. Include frontmatter in the file content since property:set is unavailable.

### Write Order

1. Session note first (other notes link to it)
2. TIL notes
3. Task notes
4. Idea notes + canvas files

---

## Step 6: Link to Daily Note

Append wikilinks of the written notes to today's Obsidian daily note so they are discoverable from the daily hub.

Collect the filename (without `.md` extension) and frontmatter `title` of each note written in Step 5. Build a wikilink block using `[[filename|title]]` alias syntax, with the session note as the parent and other notes nested under it:

```markdown
## Claude Session
- [[{session-filename}|{session title}]]
	- [[{learning-filename}|{learning title}]]
	- [[{task-filename}|{task title}]]
	- [[{idea-filename}|{idea title}]]
```

If the session produced no sub-notes (TIL, task, idea), the session link still appears as a standalone item. When sync runs multiple times in a day, each session becomes a separate top-level item under the same heading.

Before appending, read the current daily note to check for already-linked filenames and exclude duplicates.

**Primary — `obsidian` CLI** (`obsidian_cli: true`):

```bash
obsidian daily:read
```

Check for duplicates, then append:

```bash
obsidian daily:append content="${wikilink_block}"
```

**Fallback** (`obsidian_cli: false`):

```bash
obsidian daily:path
```

Use the returned path to Read the daily note for duplicate checking, then Edit to append the wikilink block. If `daily:path` also fails, skip this step with a warning — the notes themselves are already saved.

---

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

- `/session-sync` — full interactive workflow
- No quick mode — always runs the full pipeline for quality

---

## Related Resources

- `references/note-templates.md` — complete templates for all note types
- Agent definitions in `agents/` — detailed instructions for each Phase 1 and Phase 2 agent
