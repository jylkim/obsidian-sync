# Obsidian Sync

Obsidian Sync turns coding sessions into structured notes inside an Obsidian vault and lets you recall that knowledge later with local search.

This repository now builds two plugin targets from a shared prompt source:

- Claude plugin output in [`claude`](claude)
- Codex plugin output in [`codex`](codex)

The plugin payloads live under those target directories. The only repo-root exception is Claude's `.claude-plugin`, which stays at the root for production use:

- `claude/obsidian-sync/.claude-plugin` + [`.claude-plugin`](.claude-plugin)
- `codex/plugins/obsidian-sync` + `codex/.agents`

## Features

- Multi-agent session capture for reports, learnings, follow-up tasks, and ideas
- qmd-based local recall with semantic and keyword search
- Obsidian-native output with wikilinks, callouts, frontmatter, and `.canvas` files
- Dashboard and Bases templates for sessions, learnings, tasks, and ideas
- Shared template source for Claude and Codex runtimes

## Installation

Generate the target artifacts first:

```bash
uv run scripts/build_plugin.py --target all
```

### Claude

If you publish this plugin through Claude's marketplace flow, the legacy install commands from the original README still apply:

```bash
/plugin marketplace add jylkim/obsidian-sync
/plugin install obsidian-sync@jylkim-obsidian-sync
```

For local development or local use from this repository, point Claude at the repository root. The root [`.claude-plugin`](.claude-plugin) metadata resolves the actual plugin payload under `claude/obsidian-sync`.

```bash
claude --plugin-dir /path/to/repo
```

### Codex

The generated Codex target is namespaced under [`codex`](codex). For a home-local install, use the generated marketplace entry from `codex/.agents` and the generated plugin payload from `codex/plugins/obsidian-sync`.

If you do not already have a Codex marketplace file:

```bash
mkdir -p ~/.agents/plugins ~/plugins
cp codex/.agents/plugins/marketplace.json ~/.agents/plugins/marketplace.json
ln -sfn "$(pwd)/codex/plugins/obsidian-sync" ~/plugins/obsidian-sync
```

If you already have `~/.agents/plugins/marketplace.json`, merge the `obsidian-sync` plugin entry from [`codex/.agents/plugins/marketplace.json`](codex/.agents/plugins/marketplace.json) into your existing file instead of overwriting it, then copy or symlink the payload:

```bash
mkdir -p ~/plugins
ln -sfn "$(pwd)/codex/plugins/obsidian-sync" ~/plugins/obsidian-sync
```

After updating the marketplace file and plugin path, restart Codex or reopen the workspace so it reloads the plugin registry.

## Repository Layout

- [`data`](data) contains shared plugin metadata and runtime profiles
- [`prompts`](prompts) contains shared and target-specific Jinja templates
- [`scripts/build_plugin.py`](scripts/build_plugin.py) renders generated artifacts
- [`claude`](claude) contains the generated Claude plugin payload
- [`codex`](codex) contains the generated Codex plugin payload
- [`.claude-plugin`](.claude-plugin) contains the Claude marketplace metadata
- `codex/.agents` contains the Codex marketplace metadata

## Build

```bash
uv run scripts/build_plugin.py --target all
uv run scripts/build_plugin.py --check
```

`--target claude` and `--target codex` are also supported.

Running the build rewrites the selected target roots and removes legacy generated outputs from older layouts.

## Runtime Notes

- Config resolves from `OBSIDIAN_SYNC_CONFIG` first.
- On non-Windows systems, the default config path is `${XDG_CONFIG_HOME:-~/.config}/obsidian-sync/config.yaml`.
- On Windows, the Codex target documents `%APPDATA%\obsidian-sync\config.yaml`.
- Default vault folders are `Agent/Sessions`, `Agent/Learnings`, `Agent/Tasks`, `Agent/Ideas`, `Agent/Ideas/canvas`, and `Agent/Dashboard`.

## Prerequisites

| Tool | Purpose |
|------|---------|
| [Obsidian](https://obsidian.md) | Note-taking app and vault host |
| Obsidian CLI | Vault CRUD operations and daily note integration |
| [qmd](https://github.com/tobi/qmd) | Local indexing and recall |
| `obsidian:obsidian-markdown` skill | Obsidian-native note formatting |
| `obsidian:json-canvas` skill | `.canvas` generation for idea diagrams |

## License

MIT
