"""Generate a markdown table of secrets from a secrets directory or secrets.toml file."""

import sys
from pathlib import Path

import click
import tomli
from rich.console import Console


def _load_secrets_from_file(path: Path) -> list[dict]:
    """Load secrets from a single secrets.toml file."""
    with open(path, "rb") as f:
        data = tomli.load(f)

    secrets = []
    for s in data.get("secret", []):
        secrets.append(_extract_secret(s))
    return secrets


def _load_secrets_from_dir(secrets_dir: Path) -> list[dict]:
    """Load secrets from a directory of TOML files."""
    toml_files = sorted(secrets_dir.rglob("*.toml"))
    if not toml_files:
        return []

    secrets = []
    for toml_file in toml_files:
        with open(toml_file, "rb") as f:
            data = tomli.load(f)
        secrets.append(_extract_secret(data))
    return secrets


def _extract_secret(data: dict) -> dict:
    return {
        "name": data.get("name", ""),
        "display_name": data.get("display_name", ""),
        "description": data.get("description", ""),
        "k8s_sync": data.get("kubernetes_sync", False),
        "k8s_namespace": data.get("kubernetes_secret_namespace", ""),
        "k8s_secret": data.get("kubernetes_secret_name", ""),
    }


def _discover_secrets() -> tuple[list[dict], str]:
    """Discover secrets from the current directory.

    Returns a tuple of (secrets, source_description).
    """
    secrets_dir = Path("secrets")
    secrets_file = Path("secrets.toml")

    if secrets_dir.is_dir():
        return _load_secrets_from_dir(secrets_dir), "secrets/"

    stderr = Console(stderr=True)

    if secrets_file.is_file():
        stderr.print(
            "[yellow]Warning: Using secrets.toml — consider migrating to a secrets/ "
            "directory with one file per secret for better organization.[/yellow]"
        )
        return _load_secrets_from_file(secrets_file), "secrets.toml"

    stderr.print("[red]No secrets/ directory or secrets.toml file found.[/red]")
    sys.exit(1)


@click.command("secrets-table")
def secrets_table():
    """Generate a markdown table from secrets configuration.

    Searches for a secrets/ directory first, then falls back to secrets.toml.
    """
    secrets, _source = _discover_secrets()

    if not secrets:
        click.echo("No secrets found.", err=True)
        sys.exit(1)

    click.echo(
        "| Name | Display Name | Description | K8s Sync | K8s Namespace | K8s Secret |"
    )
    click.echo("| --- | --- | --- | --- | --- | --- |")
    for s in sorted(secrets, key=lambda x: x["name"]):
        click.echo(
            f"| `{s['name']}` | {s['display_name']} | {s['description']} | {s['k8s_sync']} | `{s['k8s_namespace']}` | `{s['k8s_secret']}` |"
        )
