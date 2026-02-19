import click

from nuon_ext_gen_readme.inputs import inputs_table
from nuon_ext_gen_readme.secrets import secrets_table
from nuon_ext_gen_readme.diagram import generate_diagram


@click.group()
@click.version_option(package_name="nuon-ext-gen-readme")
@click.option(
    "--app-dir",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Path to the Nuon app configuration directory.",
)
@click.pass_context
def main(ctx, app_dir):
    """Generate markdown documentation from Nuon app configuration files."""
    ctx.ensure_object(dict)
    ctx.obj["app_dir"] = app_dir


main.add_command(inputs_table)
main.add_command(secrets_table)
main.add_command(generate_diagram)
