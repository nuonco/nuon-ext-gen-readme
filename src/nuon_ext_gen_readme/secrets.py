"""Generate a markdown table of secrets from Nuon app secret definitions."""

from pathlib import Path
from typing import Any

import click
import tomli


NO_SECRETS_MESSAGE = "_This app does not define any secrets._"


def _read_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomli.load(f)


def _extract_sync_targets(data: dict) -> list[dict]:
    """Normalize kubernetes_sync_targets entries into namespaces/name/key dicts."""
    targets: list[dict] = []
    for target in data.get("kubernetes_sync_targets", []) or []:
        if not isinstance(target, dict):
            continue

        namespaces = target.get("namespaces", [])
        if isinstance(namespaces, str):
            namespaces = [namespaces]

        targets.append(
            {
                "namespaces": [str(ns) for ns in namespaces],
                "name": target.get("name", ""),
                "key": target.get("key", ""),
            }
        )
    return targets


def _extract_secret(data: dict) -> dict:
    targets = _extract_sync_targets(data)

    # Sync is enabled by the legacy kubernetes_sync flag or by the presence of any
    # sync target, which supersedes the single-valued kubernetes_secret_* fields.
    return {
        "name": data.get("name", ""),
        "display_name": data.get("display_name", ""),
        "description": data.get("description", ""),
        "required": data.get("required", False),
        "k8s_sync": bool(data.get("kubernetes_sync", False)) or bool(targets),
        "k8s_namespace": data.get("kubernetes_secret_namespace", ""),
        "k8s_secret": data.get("kubernetes_secret_name", ""),
        "k8s_sync_targets": targets,
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
    """Discover secrets from supported app configuration layouts.

    Apps are not required to define secrets, so a missing secrets.toml and a missing
    secrets/ directory are both normal and yield an empty list rather than an error.
    """
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

    return _dedupe_secrets(secrets), ", ".join(sources)


def _format_sync_destinations(secret: dict) -> str:
    """Render a secret's Kubernetes destinations as a single markdown table cell."""
    destinations = [
        f"{', '.join(f'`{ns}`' for ns in target['namespaces'])} → `{target['name']}`:`{target['key']}`"
        for target in secret["k8s_sync_targets"]
    ]

    # Fall back to the legacy single-valued fields, which only apply when no
    # kubernetes_sync_targets are set. They carry no key, so none is rendered.
    if not destinations and (secret["k8s_namespace"] or secret["k8s_secret"]):
        destinations.append(f"`{secret['k8s_namespace']}` → `{secret['k8s_secret']}`")

    return "<br>".join(destinations) if destinations else "_none_"


def build_secrets_table(root: Path) -> str:
    """Build the markdown table from secrets configuration."""
    secrets, _source = _discover_secrets(root)

    if not secrets:
        return NO_SECRETS_MESSAGE

    lines = [
        "| Name | Display Name | Description | Required | K8s Sync | K8s Sync Targets |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for secret in sorted(secrets, key=lambda x: x["name"]):
        lines.append(
            f"| `{secret['name']}` | {secret['display_name']} | {secret['description']} | {secret['required']} | {secret['k8s_sync']} | {_format_sync_destinations(secret)} |"
        )

    return "\n".join(lines)


@click.command("secrets-table")
@click.pass_context
def secrets_table(ctx):
    """Generate a markdown table from secrets configuration."""
    root = Path(ctx.obj["app_dir"])
    click.echo(build_secrets_table(root))
