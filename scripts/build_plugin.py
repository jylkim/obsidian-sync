#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "jinja2>=3.1",
#   "PyYAML>=6.0",
# ]
# ///

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
DATA_DIR = ROOT / "data"


TARGETS: dict[str, list[tuple[str, str]]] = {
    "claude": [
        ("claude/plugin.json.j2", "claude/obsidian-sync/.claude-plugin/plugin.json"),
        ("claude/marketplace.json.j2", ".claude-plugin/marketplace.json"),
        ("claude/skills/configure.md.j2", "claude/obsidian-sync/skills/configure/SKILL.md"),
        ("claude/skills/recall.md.j2", "claude/obsidian-sync/skills/recall/SKILL.md"),
        ("claude/skills/session-sync.md.j2", "claude/obsidian-sync/skills/session-sync/SKILL.md"),
        ("claude/skills/config.default.yaml.j2", "claude/obsidian-sync/skills/configure/config.default.yaml"),
        (
            "claude/skills/dashboard-templates.md.j2",
            "claude/obsidian-sync/skills/configure/references/dashboard-templates.md",
        ),
        (
            "claude/skills/note-templates.md.j2",
            "claude/obsidian-sync/skills/session-sync/references/note-templates.md",
        ),
        ("claude/agents/session-drafter.md.j2", "claude/obsidian-sync/agents/session-drafter.md"),
        ("claude/agents/til-drafter.md.j2", "claude/obsidian-sync/agents/til-drafter.md"),
        ("claude/agents/task-drafter.md.j2", "claude/obsidian-sync/agents/task-drafter.md"),
        ("claude/agents/idea-drafter.md.j2", "claude/obsidian-sync/agents/idea-drafter.md"),
        ("claude/agents/note-reviewer.md.j2", "claude/obsidian-sync/agents/note-reviewer.md"),
    ],
    "codex": [
        ("codex/plugin.json.j2", "codex/plugins/obsidian-sync/.codex-plugin/plugin.json"),
        ("codex/marketplace.json.j2", "codex/.agents/plugins/marketplace.json"),
        ("codex/skills/configure.md.j2", "codex/plugins/obsidian-sync/skills/configure/SKILL.md"),
        ("codex/skills/recall.md.j2", "codex/plugins/obsidian-sync/skills/recall/SKILL.md"),
        ("codex/skills/session-sync.md.j2", "codex/plugins/obsidian-sync/skills/session-sync/SKILL.md"),
        (
            "codex/skills/config.default.yaml.j2",
            "codex/plugins/obsidian-sync/skills/configure/config.default.yaml",
        ),
        (
            "codex/skills/dashboard-templates.md.j2",
            "codex/plugins/obsidian-sync/skills/configure/references/dashboard-templates.md",
        ),
        (
            "codex/skills/note-templates.md.j2",
            "codex/plugins/obsidian-sync/skills/session-sync/references/note-templates.md",
        ),
        (
            "codex/support/agents/session-drafter.md.j2",
            "codex/plugins/obsidian-sync/support/agents/session-drafter.md",
        ),
        (
            "codex/support/agents/til-drafter.md.j2",
            "codex/plugins/obsidian-sync/support/agents/til-drafter.md",
        ),
        (
            "codex/support/agents/task-drafter.md.j2",
            "codex/plugins/obsidian-sync/support/agents/task-drafter.md",
        ),
        (
            "codex/support/agents/idea-drafter.md.j2",
            "codex/plugins/obsidian-sync/support/agents/idea-drafter.md",
        ),
        (
            "codex/support/agents/note-reviewer.md.j2",
            "codex/plugins/obsidian-sync/support/agents/note-reviewer.md",
        ),
    ],
}

TARGET_ROOTS: dict[str, Path] = {
    "claude": ROOT / "claude",
    "codex": ROOT / "codex",
}

GENERATED_SUPPORT_ROOTS: dict[str, tuple[Path, ...]] = {
    "claude": (ROOT / ".claude-plugin",),
    "codex": (ROOT / "codex" / ".agents",),
}

LEGACY_PATHS: tuple[Path, ...] = (
    ROOT / ".agents",
    ROOT / "obsidian-sync",
    ROOT / "plugins",
)


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(PROMPTS_DIR)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tojson_pretty"] = lambda value: json.dumps(value, indent=2, ensure_ascii=False)
    return env


def render_target(env: Environment, target: str, check: bool) -> list[Path]:
    plugin = load_yaml(DATA_DIR / "plugin.yaml")
    runtime = load_yaml(DATA_DIR / "runtime" / f"{target}.yaml")
    rendered_or_changed: list[Path] = []
    context = {"plugin": plugin, "runtime": runtime}

    for template_name, relative_output in TARGETS[target]:
        template = env.get_template(template_name)
        output_path = ROOT / relative_output
        rendered = template.render(**context).rstrip() + "\n"

        if check:
            current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
            if current != rendered:
                rendered_or_changed.append(output_path)
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        if current != rendered:
            output_path.write_text(rendered, encoding="utf-8")
            rendered_or_changed.append(output_path)

    return rendered_or_changed


def clean_target_outputs(targets: list[str]) -> None:
    for target in targets:
        target_root = TARGET_ROOTS[target]
        if target_root.exists():
            shutil.rmtree(target_root)
        for support_root in GENERATED_SUPPORT_ROOTS[target]:
            if support_root.exists():
                shutil.rmtree(support_root)

    for legacy_path in LEGACY_PATHS:
        if legacy_path.exists():
            shutil.rmtree(legacy_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Claude and Codex plugin artifacts.")
    parser.add_argument(
        "--target",
        choices=["claude", "codex", "all"],
        default="all",
        help="Render a single target or all targets.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether generated files are up to date without writing them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env = build_environment()
    targets = ["claude", "codex"] if args.target == "all" else [args.target]

    if not args.check:
        clean_target_outputs(targets)

    changed: list[Path] = []
    for target in targets:
        changed.extend(render_target(env, target, args.check))

    if args.check:
        if changed:
            print("Generated files are out of date:")
            for path in changed:
                print(path.relative_to(ROOT))
            return 1
        print("Generated files are up to date.")
        return 0

    if changed:
        print("Updated generated files:")
        for path in changed:
            print(path.relative_to(ROOT))
    else:
        print("No generated files changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
