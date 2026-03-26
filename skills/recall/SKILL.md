---
name: recall
description: Search and retrieve knowledge from the user's Obsidian vault using qmd semantic search. Use proactively whenever past notes, decisions, or context could be relevant — not just on explicit search requests. Triggers include "recall", "search my notes", "what did I write about", "find in vault", "didn't I…", "wasn't there…", referencing prior work, trying to remember something, or starting a task where historical context would reduce rework. When in doubt, search.
version: 0.1.0
user-invocable: true
allowed-tools: Bash(qmd *), Bash(obsidian *), Read, Glob, Grep
---

# Obsidian Recall

Search your Obsidian vault for past knowledge using qmd. All search runs locally — no data leaves your machine.

## Prerequisites

- **qmd** installed (`npm install -g @tobilu/qmd`)
- Config exists at `~/.claude/plugins/obsidian-sync/config.yaml` (run `/configure` if missing)

## Workflow

### Step 1: Load Config

```
Read: ~/.claude/plugins/obsidian-sync/config.yaml
```

Extract `vault_name`, `vault_path`, `qmd_collection`, `search_mode`.

If config is missing, tell the user:
```
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

For the top 3–5 results from Step 3, read the actual note files to get full content:

```
Read: ${result.filepath}
```

Focus on sections most relevant to the query. For long notes, read selectively rather than loading the entire file.

### Step 5: Synthesize and Present

Present findings differently depending on how the skill was triggered:

**Explicit invocation** (`/recall` or "search my notes"):

```markdown
## Recall: "{query}"

### 1. [[Note Title]] (score: 0.92)
**Path**: Claude/Sessions/{YYYY-MM-DD}-api-refactor.md
**Tags**: #api, #refactoring
**Relevant excerpt**:
> [Key paragraph from the note]

### 2. [[Note Title]] (score: 0.85)
...

---

*{N} notes searched in collection "{qmd_collection}"*
```

**Proactive invocation** (triggered by context — the user didn't ask to search, but past notes are relevant):

Answer the user's question or continue the conversation directly, weaving in relevant information from the retrieved notes. Cite sources inline as wikilinks (e.g., "Based on [[{note title}]], ..."). Do not use the formatted recall block — the user didn't ask for a search, so the results should feel like helpful context, not a search report.

In both cases, if the retrieved notes directly answer the user's question, provide the answer rather than just listing sources.

## Fallback Chain

If the primary search method fails, fall back gracefully:

| Method | When |
|--------|------|
| `qmd query` (hybrid) | `search_mode: hybrid` |
| `qmd search` (keyword) | `search_mode: keyword`, or hybrid returns few results |
| `obsidian search` | qmd fails entirely |
| `Grep` in vault_path | Neither qmd nor `obsidian` CLI available |

### `obsidian` CLI fallback

```bash
obsidian vault="${vault_name}" search query="${query}" limit=10
```

### Grep fallback (last resort)

```bash
Grep: "${query}" in ${vault_path}/ --type md
```

## Error Handling

| Situation | Response |
|-----------|----------|
| qmd not installed | `qmd CLI required. Install: npm install -g @tobilu/qmd` |
| Collection not found | `Collection "${qmd_collection}" not registered. Run /configure.` |
| Embeddings not built | `Run: qmd embed --collection "${qmd_collection}"` (keyword search still works) |
| No results | Suggest broader terms, try keyword-only search, or offer to browse vault folders |

## Tips

- **hybrid**: natural language queries work well — "that retry pattern we discovered" works better than "retry"
- **keyword**: concise keywords work best — strip filler and keep content words only
- For exact matches, quote terms: `"ConnectionPool timeout"`
- Results include a relevance score (0–1); scores above 0.7 are typically strong matches
