import os
from pathlib import Path

import click

from nuon_ext_gen_readme.inputs import inputs_table
from nuon_ext_gen_readme.secrets import secrets_table
from nuon_ext_gen_readme.diagram import generate_diagram


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


main.add_command(inputs_table)
main.add_command(secrets_table)
main.add_command(generate_diagram)
