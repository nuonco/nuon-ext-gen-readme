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
  app-branches-diagram  Generate a Mermaid diagram of app branches and their
                        install groups.
  component-diagram     Generate a dependency diagram of components.
  create-readme         Create a new README populated with available sections.
  inputs-table          Generate a markdown table from inputs configuration.
  populate              Populate README sections between Nuon docs markers.
  secrets-table         Generate a markdown table from secrets configuration.
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

The `K8s Sync Targets` column renders each `kubernetes_sync_targets` entry as `namespaces → name:key`, with one line per
target. In a `secrets.toml` the targets are nested under the secret:

```toml
[[secret]]
name         = "rds_secret"
display_name = "Database password"
description  = "Database password"
required     = true

[[secret.kubernetes_sync_targets]]
namespaces = ["workers", "control-plane"]
name       = "storage"
key        = "db-password"
```

In the `secrets/` layout, where each file defines one secret, they are declared at the top level as
`[[kubernetes_sync_targets]]`.

`K8s Sync` is true when either `kubernetes_sync = true` or at least one sync target is defined, matching how Nuon
resolves sync. The legacy single-valued `kubernetes_secret_namespace` / `kubernetes_secret_name` fields still render in
the same column when no targets are set.

Apps are not required to define secrets: if there is no `secrets.toml` and no `secrets/` directory, the command prints a
placeholder instead of failing, and `populate` and `create-readme` still write the section.

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

### `app-branches-diagram`

Render a Mermaid diagram of the app branches in `branches/`, showing each install group, its label selector, and the
promotion order between groups.

```
nuon gen-readme app-branches-diagram
```

Given a `branches/main.toml` like this:

```toml
name = "main"

[connected_repo]
repo = "lovablelabs/lovable-enterprise"
directory = "nuon/lovable-enterprise-aws"
branch = "main"

[[install_groups]]
name = "canary"
order = 1

[install_groups.label_selector]
canary = "true"
auto-deploy = "true"

[[install_groups]]
name = "stable"
order = 2

[install_groups.label_selector]
stable = "true"
auto-deploy = "true"
```

it renders `canary` and `stable` as nodes, each listing its label selector, with a dashed `promote` edge between them.

Limit the output to a single branch:

```
nuon gen-readme app-branches-diagram --branch main
```

Render from an app branch config API payload instead of `branches/` — pass a file path, or `-` for stdin:

```
nuon apps branches configs get <id> -o json | nuon gen-readme app-branches-diagram --from-json -
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

<!-- nuon-docs app-branches-diagram-start -->
<!-- nuon-docs app-branches-diagram-end -->
```

Each section is optional and is only written when its marker pair is present. The app-branches section additionally
requires the app to have a `branches/` directory.

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
