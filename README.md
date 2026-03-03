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
  component-diagram  Generate a Mermaid dependency diagram of components.
  inputs-table       Generate a markdown table from inputs configuration.
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

Generate a Mermaid dependency diagram from component TOML files in `components/`.

```
nuon gen-readme component-diagram
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
