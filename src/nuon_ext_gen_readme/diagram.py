"""Generate a Mermaid dependency diagram from Nuon component TOML files."""

import re
from pathlib import Path

import click
import tomli


def get_dependencies(content: str) -> set[str]:
    """Extract component names referenced via .nuon.components.<name>.outputs."""
    pattern = r"\.nuon\.components\.([a-zA-Z0-9_-]+)\.outputs"
    return set(re.findall(pattern, content))


def parse_dependency_file(
    component_name: str, component_file: Path, contents_path: str, source_name: str
) -> set[str]:
    """Parse a referenced file and extract component dependency references."""
    full_path = component_file.parent / contents_path
    if full_path.exists():
        return get_dependencies(full_path.read_text())

    click.echo(
        f"Warning: {source_name} {full_path} not found for component {component_name}",
        err=True,
    )
    return set()


def build_component_diagram(root: Path) -> str:
    """Build a Mermaid dependency diagram of components."""
    components_path = root / "components"

    if not components_path.is_dir():
        raise click.ClickException("No components/ directory found.")
    toml_files = sorted(components_path.glob("*.toml"))

    if not toml_files:
        raise click.ClickException("No TOML files found in components/")

    components: dict[str, dict] = {}

    for file_path in toml_files:
        try:
            with open(file_path, "rb") as f:
                data = tomli.load(f)

            name = data.get("name")
            comp_type = data.get("type")
            if not name:
                continue

            components[name] = {
                "type": comp_type,
                "file": file_path.name,
                "deps": set(),
            }

            # Check explicit depends_on declarations.
            depends_on = data.get("depends_on", [])
            if isinstance(depends_on, list):
                components[name]["deps"].update(dep for dep in depends_on if isinstance(dep, str))

            # Check [vars] block
            vars_block = data.get("vars", {})
            for key, value in vars_block.items():
                if isinstance(value, str):
                    components[name]["deps"].update(get_dependencies(value))

            # Check [[var_file]] block
            var_files = data.get("var_file", [])
            for vf in var_files:
                contents_path = vf.get("contents")
                if contents_path:
                    components[name]["deps"].update(
                        parse_dependency_file(name, file_path, contents_path, "var_file")
                    )

            # Helm components can also reference dependencies in [[values_file]] templates.
            if comp_type in {"helm_component", "helm_chart"}:
                values_files = data.get("values_file", [])
                for vf in values_files:
                    contents_path = vf.get("contents")
                    if contents_path:
                        components[name]["deps"].update(
                            parse_dependency_file(
                                name, file_path, contents_path, "values_file"
                            )
                        )

        except Exception as e:
            click.echo(f"Error parsing {file_path}: {e}", err=True)

    lines = ["```mermaid", "graph TD"]

    for name, info in components.items():
        label = f"{name}<br/>{info['file']}"
        lines.append(f'  {name}["{label}"]')

    lines.append("")

    for name, info in components.items():
        for dep in info["deps"]:
            if dep in components:
                lines.append(f"  {dep} --> {name}")

    lines.append("")

    tf_components = [n for n, i in components.items() if i["type"] != "container_image"]
    img_components = [n for n, i in components.items() if i["type"] == "container_image"]

    if tf_components:
        lines.append(f"  class {','.join(tf_components)} tfClass;")
    if img_components:
        lines.append(f"  class {','.join(img_components)} imgClass;")

    lines.append("")
    lines.append("  classDef tfClass fill:#D6B0FC,stroke:#8040BF,color:#000;")
    lines.append("  classDef imgClass fill:#FCA04A,stroke:#CC803A,color:#000;")
    lines.append("```")
    return "\n".join(lines)


@click.command("component-diagram")
@click.pass_context
def generate_diagram(ctx):
    """Generate a Mermaid dependency diagram of components.

    Searches for a components/ directory in the app config directory.
    """
    root = Path(ctx.obj["app_dir"])
    click.echo(build_component_diagram(root))
