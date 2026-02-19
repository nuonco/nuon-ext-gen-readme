"""Generate a markdown table of inputs from an inputs directory or inputs.toml file."""

import sys
from pathlib import Path

import click
import tomli
from rich.console import Console


def _load_inputs_from_file(path: Path) -> list[dict]:
    """Load inputs from a single inputs.toml file."""
    with open(path, "rb") as f:
        data = tomli.load(f)
    return data.get("input", [])


def _load_inputs_from_dir(inputs_dir: Path) -> list[dict]:
    """Load inputs from a directory of TOML files."""
    toml_files = sorted(inputs_dir.rglob("*.toml"))
    if not toml_files:
        return []

    inputs = []
    for toml_file in toml_files:
        with open(toml_file, "rb") as f:
            data = tomli.load(f)
        # Each file may define a single input or have an [[input]] array
        if "input" in data:
            inputs.extend(data["input"])
        else:
            # Treat the file itself as a single input definition
            if "name" in data:
                inputs.append(data)
    return inputs


def _discover_inputs() -> tuple[list[dict], str]:
    """Discover inputs from the current directory.

    Returns a tuple of (inputs, source_description).
    """
    inputs_dir = Path("inputs")
    inputs_file = Path("inputs.toml")

    if inputs_dir.is_dir():
        return _load_inputs_from_dir(inputs_dir), "inputs/"

    stderr = Console(stderr=True)

    if inputs_file.is_file():
        stderr.print(
            "[yellow]Warning: Using inputs.toml — consider migrating to an inputs/ "
            "directory with one file per input for better organization.[/yellow]"
        )
        return _load_inputs_from_file(inputs_file), "inputs.toml"

    stderr.print("[red]No inputs/ directory or inputs.toml file found.[/red]")
    sys.exit(1)


@click.command("inputs-table")
def inputs_table():
    """Generate a markdown table from inputs configuration.

    Searches for an inputs/ directory first, then falls back to inputs.toml.
    """
    inputs, _source = _discover_inputs()

    if not inputs:
        click.echo("No inputs found.", err=True)
        sys.exit(1)

    click.echo("| Name | Display Name | Description | Group | Type | Default |")
    click.echo("| --- | --- | --- | --- | --- | --- |")
    for i in sorted(inputs, key=lambda x: (x.get("group", ""), x.get("name", ""))):
        name = i.get("name", "")
        display_name = i.get("display_name", "")
        description = i.get("description", "")
        group = i.get("group", "")
        input_type = i.get("type", "string")
        default = i.get("default", "")
        default_display = f"`{default}`" if default else "_none_"
        click.echo(
            f"| `{name}` | {display_name} | {description} | {group} | {input_type} | {default_display} |"
        )
