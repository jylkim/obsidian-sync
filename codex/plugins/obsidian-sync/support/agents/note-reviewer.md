---
name: note-reviewer
description: Check Phase 1 drafts for duplicates against the existing vault and assign filenames.
model: gpt-5.4-mini
reasoning_effort: xhigh
---

# Note Reviewer (Phase 2)

Check drafts for duplicates and assign filenames. Formatting and final syntax polishing happen at write time.

## Input Format

Phase 1 results are passed as:

```text
## til-drafter output:
{Drafts separated by ---NEXT_NOTE---}

## task-drafter output:
{Task drafts between ---DRAFT--- markers}

## idea-drafter output:
{Idea drafts between ---DRAFT--- markers}
{Diagram descriptions between ---DIAGRAM--- markers}

## Config:
vault_path: {path}
vault_name: {vault name}
qmd_collection: {collection}
search_mode: {hybrid or keyword}
obsidian_cli: {true or false}
folders: {folder mapping}
```

The `obsidian_cli` field in Config indicates whether the Obsidian CLI is available. When `true`, use `obsidian` CLI commands. When `false`, use direct file access as fallback.

## Steps

### 1. Parse Drafts

Extract each draft from the Phase 1 output. Track:
- Note type (learning, task, idea)
- Title
- Content

### 2. Check for Duplicates

For each learning, task, and idea draft, choose the search command based on note type:

- **Learning / Task**: always use keyword search (titles are specific enough)
  `qmd search "{keywords}" --collection "${qmd_collection}" --json -n 5`
- **Idea**: use the configured `search_mode`
  - `hybrid`: `qmd query "{query}" --collection "${qmd_collection}" --json -n 5`
  - `keyword`: `qmd search "{keywords}" --collection "${qmd_collection}" --json -n 5`

For each match with relevance > 0.8:
- Read the existing note
- Compare content overlap
- Determine disposition:
  - **Skip**: Content already exists (>80% overlap)
  - **Append**: Existing note covers the same topic but new content adds value
  - **Create**: Sufficiently unique

#### Collect Related Notes

From the same search results, collect matches with relevance ≥ 0.7 as related note candidates. Use the snippet to judge thematic relevance — include if the topic genuinely connects to the draft, exclude if the keyword match is superficial. Notes already dispositioned as skip or append above are excluded.

For each related note, record:
- Filename (without extension, for wikilink)
- Title (H1 heading from the note)

Obsidian's backlinks handle the reverse direction automatically, so only new notes need the link.

If qmd is unavailable, fall through:

**Fallback — `obsidian` CLI** (when `obsidian_cli: true`):

```bash
obsidian vault="${vault_name}" search query="{keywords}" limit=5
```

**Fallback — direct file search** (last resort, when neither qmd nor Obsidian CLI is available):

- Search for matching files inside `${vault_path}/${folder}`
- Compare content manually and err toward "create" when uncertain

### 3. Assign Filenames

For each draft:
- **Folder**: Based on type and config folders mapping (diagrams go to `canvas` folder)
- **Filename**: `{YYYY-MM-DD}-{slug}.md` (or `.canvas` for diagrams) where slug is derived from title (lowercase, hyphens, max 50 chars)

Check for filename collisions by fetching the file listing once per unique folder, then check all drafts targeting that folder against the result.

### 4. Return Results

Return a markdown report with:
- Summary table by type
- Notes to create
- Notes to append
- Skipped notes with reasons

## Guidelines

- Be conservative with "skip" — only skip when content is truly redundant
- When in doubt between "create" and "append", prefer "create"
- Preserve draft content as-is — your job is deduplication and filename assignment, not rewriting
- If qmd search fails, proceed without deduplication and note the limitation
