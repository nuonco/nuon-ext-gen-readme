"""Generate a markdown table of inputs from Nuon app input definitions."""

from pathlib import Path
from typing import Any

import click
import tomli


def _read_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomli.load(f)


def _load_inputs_from_file(path: Path) -> list[dict]:
    """Load inputs from a single inputs.toml file."""
    data = _read_toml(path)
    return data.get("input", [])


def _load_groups_from_file(path: Path) -> dict[str, dict]:
    """Load input groups from a single inputs.toml file."""
    data = _read_toml(path)
    groups: dict[str, dict] = {}
    for group in data.get("group", []):
        name = group.get("name")
        if name:
            groups[name] = group
    return groups


def _load_inputs_from_dir(inputs_dir: Path) -> list[dict]:
    """Load inputs from a directory of TOML files."""
    inputs: list[dict] = []
    for toml_file in sorted(inputs_dir.rglob("*.toml")):
        data = _read_toml(toml_file)
        if "input" in data:
            inputs.extend(data["input"])
            continue

        if "name" in data:
            inputs.append(data)
    return inputs


def _load_groups_from_dir(groups_dir: Path) -> dict[str, dict]:
    """Load input groups from input_groups/ TOML files."""
    groups: dict[str, dict] = {}
    for toml_file in sorted(groups_dir.rglob("*.toml")):
        data = _read_toml(toml_file)
        if "group" in data:
            for group in data["group"]:
                name = group.get("name")
                if name:
                    groups[name] = group
            continue

        name = data.get("name")
        if name:
            groups[name] = data
    return groups


def _dedupe_inputs(inputs: list[dict]) -> list[dict]:
    """Deduplicate inputs by name, preserving later definitions as overrides."""
    deduped: dict[str, dict] = {}
    for item in inputs:
        name = item.get("name")
        if not name:
            continue
        deduped[name] = item
    return list(deduped.values())


def _discover_inputs(root: Path) -> tuple[list[dict], dict[str, dict], str]:
    """Discover inputs and groups from supported app configuration layouts."""
    inputs_dir = root / "inputs"
    inputs_file = root / "inputs.toml"
    groups_dir = root / "input_groups"

    inputs: list[dict] = []
    groups: dict[str, dict] = {}
    sources: list[str] = []

    if inputs_file.is_file():
        inputs.extend(_load_inputs_from_file(inputs_file))
        groups.update(_load_groups_from_file(inputs_file))
        sources.append("inputs.toml")

    if inputs_dir.is_dir():
        inputs.extend(_load_inputs_from_dir(inputs_dir))
        sources.append("inputs/")

    if groups_dir.is_dir():
        groups.update(_load_groups_from_dir(groups_dir))
        sources.append("input_groups/")

    if not inputs:
        raise click.ClickException("No inputs/ directory or inputs.toml file found.")

    return _dedupe_inputs(inputs), groups, ", ".join(sources)


def build_inputs_table(root: Path) -> str:
    """Build the markdown table from inputs configuration."""
    inputs, groups, _source = _discover_inputs(root)

    if not inputs:
        raise click.ClickException("No inputs found.")

    lines = [
        "| Name | Display Name | Description | Group | Type | Default |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for item in sorted(inputs, key=lambda x: (x.get("group", ""), x.get("name", ""))):
        name = item.get("name", "")
        display_name = item.get("display_name", "")
        description = item.get("description", "")
        group = item.get("group", "")
        group_display = groups.get(group, {}).get("display_name", group)
        input_type = item.get("type", "string")
        default = item.get("default", "")
        default_display = f"`{default}`" if default else "_none_"
        lines.append(
            f"| `{name}` | {display_name} | {description} | {group_display} | {input_type} | {default_display} |"
        )

    return "\n".join(lines)


@click.command("inputs-table")
@click.pass_context
def inputs_table(ctx):
    """Generate a markdown table from inputs configuration."""
    root = Path(ctx.obj["app_dir"])
    click.echo(build_inputs_table(root))
