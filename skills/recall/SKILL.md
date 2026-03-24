---
name: obsidian-recall
description: Search and retrieve knowledge from your Obsidian vault using qmd semantic search. Use when the user says "recall", "search my notes", "what did I write about", "find in vault", "look up in obsidian", or asks a question that might be answered by their past notes. This skill is fully independent and can be used at any time, not just during session wrap-up.
version: 0.1.0
user-invocable: true
allowed-tools: Bash(qmd *), Bash(obsidian *), Read, Glob, Grep
---

# Obsidian Recall

Search your Obsidian vault for past knowledge using qmd's hybrid retrieval (BM25 + vector + LLM re-ranking). All search runs locally — no data leaves your machine.

## Prerequisites

- **qmd** installed (`npm install -g @tobilu/qmd`)
- Config exists at `~/.claude/plugins/obsidian-sync/config.yaml` (run `/obsidian-config` if missing)

## Workflow

### Step 1: Load Config

```
Read: ~/.claude/plugins/obsidian-sync/config.yaml
```

Extract `vault_name`, `vault_path`, `qmd_collection`.

If config is missing, tell the user:
```
Config not found. Run /obsidian-config to set up your vault.
```

### Step 2: Parse Query

Extract the search intent from the user's message. If the user provided a `/obsidian-recall` argument, use it directly. Otherwise, distill their question into a concise search query.

### Step 3: Search

**Primary — qmd hybrid search** (best quality):

```bash
qmd query "${query}" --collection "${qmd_collection}" --json -n 10
```

This combines keyword matching, semantic similarity, and LLM re-ranking for the most relevant results.

**If hybrid returns fewer than 3 results, supplement with keyword search:**

```bash
qmd search "${query}" --collection "${qmd_collection}" --json -n 10
```

### Step 4: Read Top Results

For the top 3–5 results from Step 3, read the actual note files to get full content:

```
Read: ${result.filepath}
```

Focus on sections most relevant to the query. For long notes, read selectively rather than loading the entire file.

### Step 5: Synthesize and Present

Present findings with enough context for the user to act on them:

```markdown
## Recall: "{query}"

### 1. [[Note Title]] (score: 0.92)
**Path**: Claude/Sessions/2026-03-20-api-refactor.md
**Tags**: #api, #refactoring
**Relevant excerpt**:
> [Key paragraph from the note]

### 2. [[Note Title]] (score: 0.85)
...

---

*{N} notes searched in collection "{qmd_collection}"*
```

If the user's question can be answered directly from the retrieved notes, provide the answer along with the source references.

## Fallback Chain

If the primary search method fails, fall back gracefully:

| Method | When |
|--------|------|
| `qmd query` (hybrid) | Default — best quality |
| `qmd search` (keyword) | Hybrid returns few results |
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
| Collection not found | `Collection "${qmd_collection}" not registered. Run /obsidian-config.` |
| Embeddings not built | `Run: qmd embed --collection "${qmd_collection}"` (keyword search still works) |
| No results | Suggest broader terms, try keyword-only search, or offer to browse vault folders |

## Tips

- Use natural language queries for best semantic results: "that retry pattern we discovered" works better than "retry"
- For exact matches, quote terms: `"ConnectionPool timeout"`
- Results include a relevance score (0–1); scores above 0.7 are typically strong matches
