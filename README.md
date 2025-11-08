# killercoda-cli

[![PyPI - Version](https://img.shields.io/pypi/v/killercoda-cli.svg)](https://pypi.org/project/killercoda-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/killercoda-cli.svg)](https://pypi.org/project/killercoda-cli)
[![codecov](https://codecov.io/gh/Piotr1215/killercoda-cli/graph/badge.svg?token=2NVHJY2T3L)](https://codecov.io/gh/Piotr1215/killercoda-cli)
[![CI](https://github.com/piotr1215/killercoda-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/piotr1215/killercoda-cli/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful CLI tool for creating and managing [Killercoda](https://killercoda.com/) interactive scenarios with ease.

**Table of Contents**

* [Installation](#installation)
* [Introduction](#introduction)
* [Documentation](#documentation)
  * [Requirements](#requirements)
* [Usage](#usage)
  * [Initialize a new scenario](#initialize-a-new-scenario)
  * [Add a new step](#add-a-new-step)
  * [Adding assets](#adding-assets)
* [Development](#development)
* [Testing](#testing)
* [Disclaimer](#disclaimer)
* [License](#license)

## Installation

```console
pip install killercoda-cli
```

> [!NOTE]
>
> If there is an installation permissions error [Error 13], consider installing
> with `--user` flag or adding `./local/bin` to the `PATH` variable.

## Introduction

[Killercoda](https://killercoda.com/) interactive scenarios are a great way to learn new technologies through a hands-on approach. However, creating and managing these scenarios can be tedious and time-consuming.

The `killercoda-cli` streamlines this process by providing:

- Adding a new step after the existing last step and creating a directory for
  including foreground and background scripts placeholders.
- Adding a regular step with `background.sh` and `foreground.sh` scripts or a verify
  step with `verify.sh` script.
- Renaming and re indexing step files and directories allowing for inserting a
  step in between existing steps and moving content _down_
- Updating the `index.json` file to reflect changes in step order and titles.

## Features

- **Scenario Initialization**: Quickly bootstrap new Killercoda scenarios with proper structure
- **Step Management**: Add, insert, and renumber steps effortlessly
- **Asset Generation**: Generate predefined assets and folder structures using templates
- **Validation**: Validate scenario structure and configuration before deployment
- **Interactive CLI**: User-friendly prompts for all operations

## Documentation

- **API Documentation**: [Auto-generated API docs](https://piotr1215.github.io/killercoda-cli/killercoda_cli/cli.html) available via pdoc
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

### Requirements

- The tool must be run in a directory containing step files or directories (e.g. step1.md, step2/).
- An `index.json` file must be present in the directory, which contains metadata about the steps.

## Usage

### Initialize a new scenario

In a new directory run `killercoda-cli init`. This command will trigger a wizard
to create a new scenario. After answering all the questions, the directory will
contain the following structure:

    .
    ├── index.json
    ├── intro.md
    ├── finish.md

### Add a new step

From here run `killercoda-cli` without arguments. This command will trigger a
wizard to add a new step. After answering all the questions, the directory will
contain steps in the similar structure:

    .
    ├── index.json
    ├── step1.md
    └── step2
        └── step2.md

And you want to insert a new step between `step1.md` and `step2/`, titled "New Step".

1. Run `killercoda-cli`.
2. Enter the title for the new step: "New Step".
3. Enter the step number to insert the new step at: 2.
4. Enter the step type (regular or verify): regular.

After running the tool, your directory structure will be updated to:

    .
    ├── index.json
    ├── step1.md
    ├── step2
        └── step2.md (previously step1.md content)
    └── step3
        └── step3.md (previously step2.md content)

The `index.json` file will also be updated to include the new step and renumber existing steps accordingly.

Before:

```json
{
  "steps": [
    {
      "title": "Step 1",
      "text": "step1.md"
    },
    {
      "title": "Step 2",
      "text": "step2/step2.md"
    }
  ]
}
```

After:

```json
{
  "steps": [
    {
      "title": "Step 1",
      "text": "step1.md"
    },
    {
      "title": "New Step",
      "text": "step2/step2.md"
    },
    {
      "title": "Step 2",
      "text": "step3/step3.md"
    }
  ]
}
```

### Adding assets

The `killercoda-cli assets` command has been added to facilitate the generation of necessary assets and folder structures in the current working directory using a predefined [cookiecutter template](https://github.com/Piotr1215/cookiecutter-killercoda-assets).

> [!NOTE]
> The assets are opinionated and may not fit all use cases, but it's a good
> starting point to add some interactivity to the scenario.

This command will generate the required folder structure and files directly in
the current working directory and **remove** the temporary directory.

Assets are NOT automatically added to the `index.json` to leave the decision to
the user how to bring the assets into the scenario.

### Validating courses

The `killercoda-cli validate` command allows you to validate the structure and configuration of your scenarios:

```console
➜ killercoda-cli validate

=== Scenario Validation ===
[+]json-syntax                                        ok
[+]step-1                                             ok
[+]step-2                                             ok

Validation Status: PASSED
Location: /scenario/folder
```

This command checks:
- Presence and validity of index.json files
- Required fields in configuration
- Existence of all referenced files
- Step structure and consistency

The validation command is useful for CI/CD pipelines to ensure course integrity before deployment.

## Development

For local development, install the package in editable mode:

```bash
pip install -e .
```

This project uses [Hatch](https://hatch.pypa.io/) for development workflow management.

### Running Tests

```bash
# Run unit tests
hatch run test:unit

# Generate coverage report
hatch run test:coverage-report
```

### Code Quality

```bash
# Run linting checks
hatch run lint:check

# Format code
hatch run lint:format

# Type checking
hatch run types:check
```

For more detailed information, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Disclaimer

This is a community project to make creating and managing Killercoda scenarios easier. It is not officially affiliated with Killercoda. Check out [Killercoda](https://killercoda.com/) to learn more about the service.

## License

`killercoda-cli` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
