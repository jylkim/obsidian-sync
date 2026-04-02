---
name: recall
description: Search and retrieve knowledge from the user's Obsidian vault using qmd semantic search.
---

# Obsidian Sync Recall

Search your Obsidian vault for past knowledge using qmd. All search runs locally — no data leaves your machine.

## Prerequisites

- **qmd** installed (`npm install -g @tobilu/qmd`)
- Config exists at `resolved obsidian-sync config path` (run `/configure` if missing)

## Workflow

### Step 1: Load Config

Read the config from `resolved obsidian-sync config path`.

Extract `vault_name`, `vault_path`, `qmd_collection`, `search_mode`.

If config is missing, tell the user:

```text
Config not found. Run /configure to set up your vault.
```

### Step 2: Parse Query

Extract the search intent from the user's message. If the user provided a `/recall` argument, use it directly. Otherwise, distill based on `search_mode`:

- **hybrid**: keep natural phrasing — semantic search benefits from intent and context. e.g. "how did we implement the retry pattern back then" → `"retry pattern implementation"`
- **keyword**: extract 2–3 core keywords only — BM25 scores drop with filler words. e.g. "how did we implement the retry pattern back then" → `"retry pattern implement"`

### Step 3: Search

Choose the search method based on `search_mode` in config:

#### If `search_mode: hybrid`

Start with the simplest form — short keywords, single collection, no advanced options:

```bash
qmd query "${query}" --collection "${qmd_collection}" --json -n 5
```

**Do not use** `intent`, `candidate-limit`, structured query, or `--explain` on the first attempt.

If top results are mostly irrelevant, escalate in order:
1. Rewrite the query shorter and more direct
2. Use exact phrase matching if needed
3. Only then try `intent` or structured query

If hybrid returns fewer than 3 results, supplement with keyword search (extract keywords from the original query per the keyword rule in Step 2):

```bash
qmd search "${keywords}" --collection "${qmd_collection}" --json -n 10
```

#### If `search_mode: keyword`

```bash
qmd search "${keywords}" --collection "${qmd_collection}" --json -n 10
```

### Step 4: Read Top Results

For the top 3–5 results from Step 3, read the actual note files to get full content.

Focus on sections most relevant to the query. For long notes, read selectively rather than loading the entire file.

### Step 5: Synthesize and Present

Present findings differently depending on how the skill was triggered:

**Explicit invocation** (`/recall` or "search my notes"):

```markdown
## Recall: "{query}"

### 1. [[Note Title]] (score: 0.92)
**Path**: Agent/Sessions/{YYYY-MM-DD}-api-refactor.md
**Tags**: #api, #refactoring
**Relevant excerpt**:
> [Key paragraph from the note]

### 2. [[Note Title]] (score: 0.85)
...

---

*{N} notes searched in collection "{qmd_collection}"*
```

**Proactive invocation**:

Answer the user's question or continue the conversation directly, weaving in relevant information from the retrieved notes. Cite sources inline as wikilinks (e.g. "Based on [[{note title}]], ..."). Do not use the formatted recall block unless the user explicitly asked for a search report.

## Fallback Chain

qmd is the expected primary tool. If it is unavailable, fall through automatically — do not stop to ask the user to install it.

### Levels

| Level | Method | Trigger |
|-------|--------|---------|
| 1 | `qmd query` / `qmd search` | Primary — always try first |
| 2 | `obsidian search` | qmd not installed or command fails |
| 3 | `Grep` or shell grep | Neither qmd nor Obsidian CLI available |

### Level 2: `obsidian` CLI

```bash
obsidian vault="${vault_name}" search query="${query}" limit=10
```

### Level 3: Grep (last resort)

Search for `"${query}"` across `${vault_path}` Markdown files.

After a successful fallback search, continue to Step 4 (Read Top Results) as normal.

## Error Handling

| Situation | Response |
|-----------|----------|
| qmd not installed | Fall through to Level 2/3. Mention once: `qmd not found — using fallback search.` |
| Collection not found | `Collection "${qmd_collection}" not registered. Run /configure.` |
| Embeddings not built | `Run: qmd embed --collection "${qmd_collection}"` (keyword search still works) |
| No results | Suggest broader terms, try keyword-only search, or offer to browse vault folders |

## Tips

- **hybrid**: natural language queries work well — "that retry pattern we discovered" works better than "retry"
- **keyword**: concise keywords work best — strip filler and keep content words only
- For exact matches, quote terms: `"ConnectionPool timeout"`
- Results include a relevance score (0–1); scores above 0.7 are typically strong matches
