# nuon-ext-gen-readme

Generate markdown documentation from Nuon app configuration files.

<!-- nuon-ext-gen-readme --help -->

```
Usage: nuon-ext-gen-readme [OPTIONS] COMMAND [ARGS]...

  Generate markdown documentation from Nuon app configuration files.

Options:
  --version            Show the version and exit.
  --app-dir DIRECTORY  Path to the Nuon app configuration directory.
  --help               Show this message and exit.

Commands:
  component-diagram  Generate a dependency diagram of components.
  inputs-table       Generate a markdown table from inputs configuration.
  populate    Populate README sections between Nuon docs markers.
  secrets-table      Generate a markdown table from secrets configuration.
```

## Installation

```
nuon ext install nuonco/nuon-ext-gen-readme
```

## Usage

Run commands from your Nuon app directory. If `--app-dir` is omitted, the command now uses the directory you invoked it
from.

You can still pass `--app-dir` to point at a different app config:

```
nuon gen-readme --app-dir /path/to/app <command>
```

### `inputs-table`

Generate a markdown table of inputs. Supports `inputs.toml`, `inputs/`, and `input_groups/` (including mixed layouts).

```
nuon gen-readme inputs-table
```

### `secrets-table`

Generate a markdown table of secrets. Supports `secrets.toml`, `secrets/`, and mixed layouts.

```
nuon gen-readme secrets-table
```

### `component-diagram`

Emit the native `<nuon-config-graph></nuon-config-graph>` tag, which renders the component dependency graph in Nuon-aware
viewers.

```
nuon gen-readme component-diagram
```

Pass `--mermaid` to render a Mermaid dependency diagram from the component TOML files in `components/` instead:

```
nuon gen-readme component-diagram --mermaid
```

### `populate`

Populate your README directly by replacing content between these marker pairs:

```
<!-- nuon-docs components-diagram-start -->
<!-- nuon-docs components-diagram-end -->

<!-- nuon-docs inputs-table-start -->
<!-- nuon-docs inputs-table-end -->

<!-- nuon-docs secrets-table-start -->
<!-- nuon-docs secrets-table-end -->
```

Run it in your app directory:

```
nuon gen-readme populate
```

Or target a different README path:

```
nuon gen-readme populate --readme-path docs/README.md
```

To populate the components diagram with a Mermaid graph instead of the native `<nuon-config-graph>` tag:

```
nuon gen-readme populate --mermaid
```

Pipe any command to the clipboard:

```
nuon gen-readme inputs-table | pbcopy
```

## Development

```
git clone https://github.com/nuon/nuon-ext-gen-readme.git
cd nuon-ext-gen-readme
uv sync
```

Run commands locally:

```
uv run nuon-ext-gen-readme --help
uv run nuon-ext-gen-readme --app-dir ../my-app inputs-table
```
