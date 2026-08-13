import os
from pathlib import Path

import click

from nuon_ext_gen_readme.app_branches import (
    app_branches_diagram,
    build_app_branches_diagram,
)
from nuon_ext_gen_readme.diagram import build_component_diagram, generate_diagram
from nuon_ext_gen_readme.inputs import build_inputs_table, inputs_table
from nuon_ext_gen_readme.secrets import build_secrets_table, secrets_table


SECTION_MARKERS = {
    "components-diagram": (
        "<!-- nuon-docs components-diagram-start -->",
        "<!-- nuon-docs components-diagram-end -->",
    ),
    "inputs-table": (
        "<!-- nuon-docs inputs-table-start -->",
        "<!-- nuon-docs inputs-table-end -->",
    ),
    "secrets-table": (
        "<!-- nuon-docs secrets-table-start -->",
        "<!-- nuon-docs secrets-table-end -->",
    ),
    "app-branches-diagram": (
        "<!-- nuon-docs app-branches-diagram-start -->",
        "<!-- nuon-docs app-branches-diagram-end -->",
    ),
}


def _build_readme(app_root: Path, name: str, mermaid: bool) -> str:
    sections: list[str] = [f"# {name}\n"]

    sections.append("## Description\n\n_Add a description of this app configuration here._\n")

    try:
        inputs = build_inputs_table(app_root)
        start, end = SECTION_MARKERS["inputs-table"]
        sections.append(f"## Inputs\n\n{start}\n{inputs}\n{end}\n")
    except click.ClickException:
        pass

    try:
        secrets = build_secrets_table(app_root)
        start, end = SECTION_MARKERS["secrets-table"]
        sections.append(f"## Secrets\n\n{start}\n{secrets}\n{end}\n")
    except click.ClickException:
        pass

    diagram = build_component_diagram(app_root, mermaid=mermaid)
    start, end = SECTION_MARKERS["components-diagram"]
    sections.append(f"## Components\n\n{start}\n{diagram}\n{end}\n")

    try:
        app_branches = build_app_branches_diagram(app_root)
        start, end = SECTION_MARKERS["app-branches-diagram"]
        sections.append(f"## App Branches\n\n{start}\n{app_branches}\n{end}\n")
    except click.ClickException:
        pass

    return "\n".join(sections)


def _replace_between_markers(content: str, start_marker: str, end_marker: str, block: str) -> str:
    start_index = content.find(start_marker)
    if start_index == -1:
        raise click.ClickException(f"Missing start marker: {start_marker}")

    end_index = content.find(end_marker, start_index + len(start_marker))
    if end_index == -1:
        raise click.ClickException(f"Missing end marker: {end_marker}")

    block_start = start_index + len(start_marker)
    replacement = f"\n{block.strip()}\n"
    return f"{content[:block_start]}{replacement}{content[end_index:]}"


@click.group()
@click.version_option(package_name="nuon-ext-gen-readme")
@click.option(
    "--app-dir",
    type=click.Path(file_okay=False),
    default=None,
    help="Path to the Nuon app configuration directory.",
)
@click.pass_context
def main(ctx, app_dir):
    """Generate markdown documentation from Nuon app configuration files."""
    invocation_dir = Path(os.environ.get("PWD", str(Path.cwd())))

    app_path = invocation_dir if app_dir is None else Path(app_dir)
    if not app_path.is_absolute():
        app_path = invocation_dir / app_path
    app_path = app_path.resolve()

    if not app_path.exists() or not app_path.is_dir():
        raise click.BadParameter(
            f"App directory does not exist or is not a directory: {app_path}",
            param_hint="--app-dir",
        )

    ctx.ensure_object(dict)
    ctx.obj["app_dir"] = str(app_path)


@click.command("populate")
@click.option(
    "--readme-path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=Path("README.md"),
    show_default=True,
    help="Path to README file to update. Relative paths are resolved from --app-dir.",
)
@click.option(
    "--mermaid",
    is_flag=True,
    default=False,
    help="Render the components diagram as Mermaid instead of the native <nuon-config-graph> tag.",
)
@click.pass_context
def populate_readme(ctx, readme_path: Path, mermaid: bool):
    """Populate README sections between Nuon docs markers."""
    app_root = Path(ctx.obj["app_dir"])
    resolved_readme = readme_path if readme_path.is_absolute() else app_root / readme_path

    if not resolved_readme.exists() or not resolved_readme.is_file():
        raise click.BadParameter(
            f"README file does not exist or is not a file: {resolved_readme}",
            param_hint="--readme-path",
        )

    readme_contents = resolved_readme.read_text()
    rendered_sections = {
        "components-diagram": build_component_diagram(app_root, mermaid=mermaid),
        "inputs-table": build_inputs_table(app_root),
        "secrets-table": build_secrets_table(app_root),
    }

    # Only rendered when the app defines branches/, and only written when the
    # README opts in with the markers, so existing READMEs keep working.
    try:
        rendered_sections["app-branches-diagram"] = build_app_branches_diagram(app_root)
    except click.ClickException:
        pass

    updated_contents = readme_contents
    for key, section in rendered_sections.items():
        start_marker, end_marker = SECTION_MARKERS[key]
        if key == "app-branches-diagram" and start_marker not in readme_contents:
            continue
        updated_contents = _replace_between_markers(
            updated_contents, start_marker, end_marker, section
        )

    resolved_readme.write_text(updated_contents)
    click.echo(f"Updated README sections in {resolved_readme}")


@click.command("create-readme")
@click.option(
    "--name",
    default=None,
    help="App name for the README title. Defaults to the app directory name.",
)
@click.option(
    "--readme-path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=Path("README.md"),
    show_default=True,
    help="Output path for the README. Relative paths are resolved from --app-dir.",
)
@click.option(
    "--mermaid",
    is_flag=True,
    default=False,
    help="Render the components diagram as Mermaid instead of the native <nuon-config-graph> tag.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite an existing README file.",
)
@click.pass_context
def create_readme(ctx, name: str | None, readme_path: Path, mermaid: bool, force: bool):
    """Create a new README populated with available Nuon app configuration sections."""
    app_root = Path(ctx.obj["app_dir"])
    resolved_readme = readme_path if readme_path.is_absolute() else app_root / readme_path

    if resolved_readme.exists() and not force:
        raise click.ClickException(
            f"{resolved_readme} already exists. Use --force to overwrite."
        )

    app_name = name or app_root.name
    content = _build_readme(app_root, app_name, mermaid)
    resolved_readme.write_text(content)
    click.echo(f"Created {resolved_readme}")


main.add_command(inputs_table)
main.add_command(secrets_table)
main.add_command(generate_diagram)
main.add_command(app_branches_diagram)
main.add_command(populate_readme)
main.add_command(create_readme)
