"""Generate a Mermaid diagram of app branches and their install groups."""

import json
import sys
from pathlib import Path
from typing import Any

import click
import tomli

# Cycled by install group order so each stage in a promotion chain is distinct.
GROUP_PALETTE = [
    "fill:#D6B0FC,stroke:#8040BF,color:#000;",
    "fill:#A8E6A3,stroke:#4C9A48,color:#000;",
    "fill:#FCA04A,stroke:#CC803A,color:#000;",
    "fill:#9FD3FC,stroke:#3E7FB2,color:#000;",
]


def _escape(value: str) -> str:
    """Escape characters that break Mermaid node labels."""
    return str(value).replace('"', "&quot;").replace("#", "&#35;")


def _match_labels(label_selector: Any) -> dict[str, str]:
    """Read labels from either the TOML or API shape of a label selector.

    TOML nests them directly under ``[install_groups.label_selector]`` while the
    API wraps them in ``match_labels``.
    """
    if not isinstance(label_selector, dict):
        return {}

    match_labels = label_selector.get("match_labels")
    if isinstance(match_labels, dict):
        return {str(k): str(v) for k, v in match_labels.items()}

    return {str(k): str(v) for k, v in label_selector.items()}


def _normalize_groups(raw_groups: Any) -> list[dict]:
    """Normalize install groups into ``{name, order, labels}`` sorted by order."""
    if not isinstance(raw_groups, list):
        return []

    groups: list[dict] = []
    for index, group in enumerate(raw_groups):
        if not isinstance(group, dict):
            continue

        name = group.get("name")
        if not name:
            continue

        order = group.get("order")
        groups.append(
            {
                "name": str(name),
                "order": order if isinstance(order, int) else index + 1,
                "labels": _match_labels(group.get("label_selector")),
            }
        )

    return sorted(groups, key=lambda g: (g["order"], g["name"]))


def _branch_title(name: str, repo: Any, config_number: Any = None) -> str:
    """Build the subgraph title from the branch name and connected repo."""
    parts = [f"app branch · {name}"]

    if isinstance(repo, dict):
        repo_name = repo.get("repo")
        branch = repo.get("branch")
        directory = repo.get("directory")

        if repo_name:
            parts.append(f"{repo_name}@{branch}" if branch else str(repo_name))
        if directory:
            parts.append(str(directory))

    if config_number is not None:
        parts.append(f"config #{config_number}")

    return " · ".join(parts)


def _load_branches_from_toml(root: Path) -> list[dict]:
    """Load branch definitions from the branches/ directory."""
    branches_dir = root / "branches"

    if not branches_dir.is_dir():
        raise click.ClickException("No branches/ directory found.")

    branches: list[dict] = []
    for toml_file in sorted(branches_dir.glob("*.toml")):
        with open(toml_file, "rb") as f:
            data = tomli.load(f)

        name = data.get("name") or toml_file.stem
        branches.append(
            {
                "name": str(name),
                "title": _branch_title(str(name), data.get("connected_repo")),
                "groups": _normalize_groups(data.get("install_groups")),
            }
        )

    if not branches:
        raise click.ClickException("No TOML files found in branches/")

    return branches


def _load_branches_from_json(payload: Any) -> list[dict]:
    """Load branch definitions from an app branch config API payload."""
    configs = payload if isinstance(payload, list) else [payload]

    branches: list[dict] = []
    for config in configs:
        if not isinstance(config, dict):
            continue

        repo = config.get("connected_github_vcs_config")
        name = config.get("name")
        if not name and isinstance(repo, dict):
            name = repo.get("branch")

        name = str(name or config.get("app_branch_id") or "branch")
        branches.append(
            {
                "name": name,
                "title": _branch_title(name, repo, config.get("config_number")),
                "groups": _normalize_groups(config.get("install_groups")),
            }
        )

    if not branches:
        raise click.ClickException("No app branch configs found in JSON payload.")

    return branches


def _read_json_source(source: str) -> Any:
    """Read an API payload from a file path or stdin when passed ``-``."""
    raw = sys.stdin.read() if source == "-" else Path(source).read_text()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Could not parse JSON payload: {e}")


def build_app_branches_diagram(
    root: Path, branch: str | None = None, from_json: str | None = None
) -> str:
    """Build a Mermaid diagram of app branches, install groups, and label selectors."""
    if from_json:
        branches = _load_branches_from_json(_read_json_source(from_json))
    else:
        branches = _load_branches_from_toml(root)

    if branch:
        branches = [b for b in branches if b["name"] == branch]
        if not branches:
            raise click.ClickException(f"No branch named {branch} found.")

    lines = ["```mermaid", "flowchart LR"]
    used_palette: set[int] = set()

    for branch_index, branch_config in enumerate(branches):
        groups = branch_config["groups"]

        lines.append(f'  subgraph b{branch_index}["{_escape(branch_config["title"])}"]')
        lines.append("    direction LR")

        if not groups:
            lines.append(f'    b{branch_index}empty["<i>No install groups</i>"]')
            lines.append("  end")
            lines.append("")
            continue

        for group_index, group in enumerate(groups):
            label = [f"<b>{_escape(group['name'])}</b> <i>(order {group['order']})</i>"]

            if group["labels"]:
                label.append("─────────────")
                label.extend(
                    f"{_escape(key)}={_escape(value)}"
                    for key, value in sorted(group["labels"].items())
                )
            else:
                label.append("<i>no label selector</i>")

            node_id = f"b{branch_index}g{group_index}"
            lines.append(f'    {node_id}["{"<br/>".join(label)}"]')

        lines.append("")

        for group_index in range(len(groups) - 1):
            lines.append(
                f"    b{branch_index}g{group_index} -.->|promote| "
                f"b{branch_index}g{group_index + 1}"
            )

        lines.append("  end")
        lines.append("")

        for group_index in range(len(groups)):
            palette_index = group_index % len(GROUP_PALETTE)
            used_palette.add(palette_index)
            lines.append(f"  class b{branch_index}g{group_index} abClass{palette_index};")

    lines.append("")

    for palette_index in sorted(used_palette):
        lines.append(f"  classDef abClass{palette_index} {GROUP_PALETTE[palette_index]}")

    lines.append("```")
    return "\n".join(lines)


@click.command("app-branches-diagram")
@click.option(
    "--branch",
    default=None,
    help="Only render the named app branch. Defaults to every branch found.",
)
@click.option(
    "--from-json",
    default=None,
    help="Read app branch configs from a JSON file, or - for stdin, instead of branches/.",
)
@click.pass_context
def app_branches_diagram(ctx, branch: str | None, from_json: str | None):
    """Generate a Mermaid diagram of app branches and their install groups."""
    root = Path(ctx.obj["app_dir"])
    click.echo(build_app_branches_diagram(root, branch=branch, from_json=from_json))
