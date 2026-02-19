import click

from nuon_ext_gen_readme.inputs import inputs_table
from nuon_ext_gen_readme.secrets import secrets_table
from nuon_ext_gen_readme.diagram import generate_diagram


@click.group()
@click.version_option(package_name="nuon-ext-gen-readme")
def main():
    """Generate markdown documentation from Nuon app configuration files."""
    pass


main.add_command(inputs_table)
main.add_command(secrets_table)
main.add_command(generate_diagram)
