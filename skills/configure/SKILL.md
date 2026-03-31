---
name: configure
description: Configure obsidian-sync plugin settings — vault name, vault path, qmd collection, and folder structure. Use when the user says "configure obsidian", "set vault path", "obsidian config", "change vault", "switch vault", or when another obsidian-sync skill reports that config is missing. Also use when the user first installs the plugin, wants to reconfigure settings, or mentions that sync or recall isn't working due to missing config.
version: 0.1.0
user-invocable: true
allowed-tools: Bash(qmd *), Bash(obsidian *), Bash(pgrep *), Bash(mkdir *), Bash(nohup *), Read, Write, Glob, AskUserQuestion
---

# Obsidian Sync Configuration

Interactive setup for obsidian-sync. Saves configuration to a fixed path so all skills can find it.

## Config File Location

```
~/.claude/plugins/obsidian-sync/config.yaml
```

## Workflow

### Step 1: Check Existing Config

```
Read: ~/.claude/plugins/obsidian-sync/config.yaml
```

- If found: display current values and ask what to change
- If not found: proceed to interactive setup

### Step 2: Check Prerequisites

#### qmd

```bash
qmd --help 2>/dev/null
```

- Fails: display install instructions (`npm install -g @tobilu/qmd`) and stop
- Succeeds: continue

### Step 3: Detect Vault

First check if Obsidian is running (CLI requires the app to be open — calling it when Obsidian is closed will launch the app and block):

```bash
pgrep -xi obsidian >/dev/null 2>&1
```

#### If Obsidian is running — try auto-detect

```bash
obsidian vaults verbose 2>/dev/null | grep -v "^[0-9]" | grep -v "installer"
```

Output is tab-separated: `{vault_name}\t{vault_path}`, one line per vault.

- **1 vault found**: use it automatically, confirm with the user
- **Multiple vaults**: present the list and let the user choose via AskUserQuestion
- **Command fails or 0 vaults**: CLI is not enabled. Fall through to manual input

#### If Obsidian is not running or CLI fails — manual input

```
AskUserQuestion:
  question: "Enter your Obsidian vault name (as shown in Obsidian app):"
  → vault_name

AskUserQuestion:
  question: "Enter the absolute path to your vault directory:"
  → vault_path
```

Warn the user that `obsidian` CLI is not available — direct file write will be used as fallback for /session-sync.

### Step 4: Remaining Settings

```
AskUserQuestion:
  question: "Choose a name for the qmd collection (used for search indexing):"
  default: derived from vault_name (lowercase, hyphens)
  → qmd_collection
```

```
AskUserQuestion:
  question: "Search mode?"
  options:
    - "hybrid (BM25 + vector + LLM re-ranking — requires embedding, slower setup)"
    - "keyword (BM25 only — no embedding needed, faster and lighter)"
  default: "hybrid"
  → search_mode
```

```
AskUserQuestion:
  question: "Language for note content? (templates and structure stay the same)"
  default: "English"
  → content_language
```

For folder structure, offer defaults with option to customize:

```
AskUserQuestion:
  question: "Use default folder structure?"
  options:
    - "Yes (Claude/Sessions, Claude/Learnings, Claude/Tasks, Claude/Ideas, Claude/Ideas/canvas, Claude/Dashboard)"
    - "Customize folders"
```

### Step 5: Save Config

```bash
mkdir -p ~/.claude/plugins/obsidian-sync
```

Write the YAML config to `~/.claude/plugins/obsidian-sync/config.yaml`.

Reference `${CLAUDE_SKILL_DIR}/config.default.yaml` for the template structure.

### Step 6: Register qmd Collection

```bash
qmd collection list --json
```

- Collection exists: skip
- Collection missing: register it:
  ```bash
  qmd collection add "${vault_path}" --name "${qmd_collection}"
  ```

Then run initial indexing:

```bash
qmd update --collection "${qmd_collection}"
```

If `search_mode` is `hybrid`, also generate embeddings:
```bash
nohup qmd embed --collection "${qmd_collection}" > /dev/null 2>&1 &
echo "Embedding generation started in background."
```

If `search_mode` is `keyword`, skip embedding entirely.

### Step 7: Create Vault Folders

```bash
mkdir -p "${vault_path}/Claude/Sessions"
mkdir -p "${vault_path}/Claude/Learnings"
mkdir -p "${vault_path}/Claude/Tasks"
mkdir -p "${vault_path}/Claude/Ideas"
mkdir -p "${vault_path}/Claude/Ideas/canvas"
mkdir -p "${vault_path}/Claude/Dashboard"
```

### Step 8: Create Dashboard

Create dashboard files that provide live database views of all synced notes.
Reference `${CLAUDE_SKILL_DIR}/references/dashboard-templates.md` for complete file contents.

#### 8a. Check for Existing Dashboard

```
Glob: ${vault_path}/${folders.sessions}/sessions.base
Glob: ${vault_path}/${folders.dashboard}/Dashboard.md
```

If files exist:

```
AskUserQuestion:
  question: "Dashboard files already exist. Overwrite?"
  options:
    - "Keep existing (skip)"
    - "Regenerate all (overwrites customizations)"
  default: "Keep existing (skip)"
```

- "Keep existing" → skip to Output
- "Regenerate" → proceed to 8b
- No files found → proceed to 8b without asking

#### 8b. Write Dashboard Files

Write 6 files using the Write tool. Each `.base` file goes into its respective note folder. Replace folder path placeholders (`${folders.sessions}`, `${folders.learnings}`, etc.) in `.base` filter expressions with actual config values.

1. `${vault_path}/${folders.sessions}/sessions.base`
2. `${vault_path}/${folders.learnings}/learnings.base`
3. `${vault_path}/${folders.tasks}/tasks.base`
4. `${vault_path}/${folders.ideas}/ideas.base`
5. `${vault_path}/${folders.dashboard}/recent.base`
6. `${vault_path}/${folders.dashboard}/Dashboard.md`

### Output

```
Configuration saved to ~/.claude/plugins/obsidian-sync/config.yaml

  Vault:      {vault_name}
  Path:       {vault_path}
  Collection: {qmd_collection}
  Write mode: `obsidian` CLI | direct file write
  Folders:    Claude/Sessions, Claude/Learnings, Claude/Tasks, Claude/Ideas
  Dashboard:  {folders.dashboard}/Dashboard.md

Ready to use /session-sync and /recall.
```
