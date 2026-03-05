import os
from pathlib import Path

import click

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
}


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


@click.command("populate-readme")
@click.option(
    "--readme-path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    default=Path("README.md"),
    show_default=True,
    help="Path to README file to update. Relative paths are resolved from --app-dir.",
)
@click.pass_context
def populate_readme(ctx, readme_path: Path):
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
        "components-diagram": build_component_diagram(app_root),
        "inputs-table": build_inputs_table(app_root),
        "secrets-table": build_secrets_table(app_root),
    }

    updated_contents = readme_contents
    for key, section in rendered_sections.items():
        start_marker, end_marker = SECTION_MARKERS[key]
        updated_contents = _replace_between_markers(
            updated_contents, start_marker, end_marker, section
        )

    resolved_readme.write_text(updated_contents)
    click.echo(f"Updated README sections in {resolved_readme}")


main.add_command(inputs_table)
main.add_command(secrets_table)
main.add_command(generate_diagram)
main.add_command(populate_readme)
