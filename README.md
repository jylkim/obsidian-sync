# Obsidian Sync Plugin

A Claude Code plugin that bridges your coding sessions with your Obsidian vault. Sync session knowledge as structured notes, then recall it later with semantic search.

## Features

- **Multi-Agent Sync Pipeline**: 4 specialized agents analyze your session from different angles
- **2-Phase Architecture**: Parallel analysis followed by sequential validation
- **Session Reports**: Structured notes capturing what you accomplished, decided, and solved
- **TIL Notes**: Automatically extracted learnings with code examples
- **Task Tracking**: Follow-up tasks as standalone task notes with priorities
- **Creative Ideas**: Architecture improvements, product concepts, and visual diagrams
- **Semantic Recall**: Search past notes with qmd's hybrid retrieval (BM25 + vector + LLM re-ranking)
- **Live Dashboard**: Obsidian Bases-powered database views for sessions, tasks, learnings, and ideas
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
claude --plugin-dir /path/to/repo/obsidian-sync
```

## Setup

```
/configure
```

This will prompt you for:
- Vault name and path
- qmd collection name
- Folder structure preferences

## Usage

### Sync Session to Obsidian

```
/session-sync
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
/recall what was that retry pattern we used?
```

Searches your vault using qmd's hybrid search and presents relevant notes with excerpts.

## Architecture

```
Phase 1: Analysis (Parallel)
┌──────────────────┬──────────────────┐
│  session-drafter │  til-drafter     │  sonnet
│  (session report)│  (learnings)     │
├──────────────────┼──────────────────┤
│  task-drafter    │  idea-drafter    │  sonnet / opus
│  (follow-ups)    │  (creative ideas)│
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
| session-sync | `/session-sync` | Full session sync workflow |
| recall | `/recall` | Semantic vault search |
| configure | `/configure` | Plugin configuration |

## Vault Structure

Default folder layout (customizable via `/configure`):

```
Your Vault/
└── Claude/
    ├── Dashboard/      # Hub page and cross-type view
    │   ├── Dashboard.md
    │   └── recent.base
    ├── Sessions/       # Session report notes
    │   ├── sessions.base
    │   └── *.md
    ├── Learnings/      # TIL notes
    │   ├── learnings.base
    │   └── *.md
    ├── Tasks/          # Task notes
    │   ├── tasks.base
    │   └── *.md
    └── Ideas/          # Idea notes
        ├── ideas.base
        ├── canvas/     # .canvas diagram files
        └── *.md
```

### Dashboard

`/configure` creates a dashboard with live database views of all synced notes. Each `.base` file lives alongside its notes for contextual access.

| File | Location | Views |
|------|----------|-------|
| `Dashboard.md` | Dashboard/ | Hub page embedding all views |
| `sessions.base` | Sessions/ | Recent Sessions, By Project |
| `learnings.base` | Learnings/ | All Learnings, By Project |
| `tasks.base` | Tasks/ | Active Tasks, Completed, All Tasks |
| `ideas.base` | Ideas/ | Idea Board (cards), All Ideas |
| `recent.base` | Dashboard/ | By Session, Last 30 Days |

Open `Dashboard.md` in Obsidian for a unified overview.
Open individual `.base` files for full sorting, filtering, and grouping.

Requires Obsidian 1.9.0+ (Bases is a core feature, no community plugins needed).

## When to Use

**Use `/session-sync` when:**
- Ending a productive work session
- After completing a feature or fixing a significant bug
- Before switching to a different project
- When you want to capture knowledge for future reference

**Use `/recall` when:**
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
