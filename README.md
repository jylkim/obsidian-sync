# Obsidian Sync Plugin

A Claude Code plugin that bridges your coding sessions with your Obsidian vault. Sync session knowledge as structured notes, then recall it later with semantic search.

## Features

- **Multi-Agent Sync Pipeline**: 4 specialized agents analyze your session from different angles
- **2-Phase Architecture**: Parallel analysis followed by sequential validation
- **Session Reports**: Structured notes capturing what you accomplished, decided, and solved
- **TIL Notes**: Automatically extracted learnings with code examples
- **Task Tracking**: Follow-up tasks synced to daily notes and standalone task notes
- **Creative Ideas**: Architecture improvements, product concepts, and visual diagrams
- **Semantic Recall**: Search past notes with qmd's hybrid retrieval (BM25 + vector + LLM re-ranking)
- **Obsidian-Native**: Wikilinks, callouts, frontmatter, tags, and .canvas files

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| [Obsidian](https://obsidian.md) | Note-taking app | [obsidian.md](https://obsidian.md) |
| Obsidian CLI | Vault CRUD operations | Enable in Obsidian Settings → CLI |
| [obsidian-skills](https://github.com/kepano/obsidian-skills) | Obsidian formatting patterns | Claude Code plugin |
| [qmd](https://github.com/tobi/qmd) | Semantic search engine | `npm install -g @tobilu/qmd` |

Obsidian CLI is recommended but not required — the plugin falls back to direct file writes when it's unavailable.

## Installation

### From GitHub

```bash
# Add as marketplace
/plugin marketplace add jylkim/obsidian-sync

# Install
/plugin install obsidian-sync@jylkim-obsidian-sync
```

### Local Development

```bash
claude --plugin-dir /path/to/obsidian-sync
```

## Setup

```
/obsidian-config
```

This will prompt you for:
- Vault name and path
- qmd collection name
- Folder structure preferences

## Usage

### Sync Session to Obsidian

```
/obsidian-sync
```

Runs the full sync workflow:
1. Gather session context (git status, conversation history)
2. Phase 1: 4 agents analyze in parallel (session report, TILs, tasks, ideas)
3. Phase 2: Validate and deduplicate against existing vault
4. Preview notes and select which to save
5. Write to Obsidian vault
6. Index with qmd for future recall

### Recall Past Knowledge

```
/obsidian-recall what was that retry pattern we used?
```

Searches your vault using qmd's hybrid search and presents relevant notes with excerpts.

## Architecture

```
Phase 1: Analysis (Parallel)
┌──────────────────┬──────────────────┐
│  session-drafter   │  til-drafter      │  sonnet
│  (session report) │  (learnings)     │
├──────────────────┼──────────────────┤
│  task-drafter      │  idea-drafter     │  sonnet / opus
│  (follow-ups)     │  (creative ideas)│
└──────────────────┴──────────────────┘
                    │
                    ▼
Phase 2: Validation (Sequential)
┌────────────────────────────────────────┐
│            note-reviewer               │  sonnet
│  (validate, deduplicate, finalize)     │
└────────────────────────────────────────┘
                    │
                    ▼
              User Selection
                    │
                    ▼
         Write to Obsidian Vault
                    │
                    ▼
           qmd update & embed
```

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `session-drafter` | sonnet | Compose structured session report |
| `til-drafter` | sonnet | Extract learnings as TIL notes |
| `task-drafter` | sonnet | Identify follow-up tasks with priorities |
| `idea-drafter` | opus | Generate creative ideas and visual diagrams |
| `note-reviewer` | sonnet | Validate, deduplicate, and finalize all notes |

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| obsidian-sync | `/obsidian-sync` | Full session sync workflow |
| obsidian-recall | `/obsidian-recall` | Semantic vault search |
| obsidian-config | `/obsidian-config` | Plugin configuration |

## Vault Structure

Default folder layout (customizable via `/obsidian-config`):

```
Your Vault/
└── Claude/
    ├── Sessions/     # Session report notes
    ├── Learnings/    # TIL notes
    ├── Tasks/        # Task notes
    └── Ideas/        # Idea notes
        └── canvas/   # .canvas diagram files
```

## When to Use

**Use `/obsidian-sync` when:**
- Ending a productive work session
- After completing a feature or fixing a significant bug
- Before switching to a different project
- When you want to capture knowledge for future reference

**Use `/obsidian-recall` when:**
- Starting a new session and need context from past work
- Trying to remember how you solved a similar problem
- Looking for past decisions or architectural notes
- Searching for code patterns you've encountered before

**Skip when:**
- Very short session with trivial changes
- Only reading/exploring code
- Quick one-off question

## Acknowledgements

This plugin is heavily inspired by [session-wrap](https://github.com/team-attention/plugins-for-claude-natives#session-wrap) from [plugins-for-claude-natives](https://github.com/team-attention/plugins-for-claude-natives).

## License

MIT
