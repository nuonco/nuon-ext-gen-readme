"""Generate a markdown table of secrets from Nuon app secret definitions."""

import sys
from pathlib import Path
from typing import Any

import click
import tomli


def _read_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomli.load(f)


def _extract_secret(data: dict) -> dict:
    return {
        "name": data.get("name", ""),
        "display_name": data.get("display_name", ""),
        "description": data.get("description", ""),
        "k8s_sync": data.get("kubernetes_sync", False),
        "k8s_namespace": data.get("kubernetes_secret_namespace", ""),
        "k8s_secret": data.get("kubernetes_secret_name", ""),
    }


def _load_secrets_from_file(path: Path) -> list[dict]:
    """Load secrets from a single secrets.toml file."""
    data = _read_toml(path)
    return [_extract_secret(secret) for secret in data.get("secret", [])]


def _load_secrets_from_dir(secrets_dir: Path) -> list[dict]:
    """Load secrets from a directory of TOML files."""
    secrets: list[dict] = []
    for toml_file in sorted(secrets_dir.rglob("*.toml")):
        data = _read_toml(toml_file)
        if "secret" in data:
            secrets.extend(_extract_secret(secret) for secret in data["secret"])
            continue

        secrets.append(_extract_secret(data))
    return secrets


def _dedupe_secrets(secrets: list[dict]) -> list[dict]:
    """Deduplicate secrets by name, preserving later definitions as overrides."""
    deduped: dict[str, dict] = {}
    for secret in secrets:
        name = secret.get("name")
        if not name:
            continue
        deduped[name] = secret
    return list(deduped.values())


def _discover_secrets(root: Path) -> tuple[list[dict], str]:
    """Discover secrets from supported app configuration layouts."""
    secrets_dir = root / "secrets"
    secrets_file = root / "secrets.toml"

    secrets: list[dict] = []
    sources: list[str] = []

    if secrets_file.is_file():
        secrets.extend(_load_secrets_from_file(secrets_file))
        sources.append("secrets.toml")

    if secrets_dir.is_dir():
        secrets.extend(_load_secrets_from_dir(secrets_dir))
        sources.append("secrets/")

    if not secrets:
        click.echo("No secrets/ directory or secrets.toml file found.", err=True)
        sys.exit(1)

    return _dedupe_secrets(secrets), ", ".join(sources)


@click.command("secrets-table")
@click.pass_context
def secrets_table(ctx):
    """Generate a markdown table from secrets configuration."""
    root = Path(ctx.obj["app_dir"])
    secrets, _source = _discover_secrets(root)

    if not secrets:
        click.echo("No secrets found.", err=True)
        sys.exit(1)

    click.echo(
        "| Name | Display Name | Description | K8s Sync | K8s Namespace | K8s Secret |"
    )
    click.echo("| --- | --- | --- | --- | --- | --- |")
    for secret in sorted(secrets, key=lambda x: x["name"]):
        click.echo(
            f"| `{secret['name']}` | {secret['display_name']} | {secret['description']} | {secret['k8s_sync']} | `{secret['k8s_namespace']}` | `{secret['k8s_secret']}` |"
        )
