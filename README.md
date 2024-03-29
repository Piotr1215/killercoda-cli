# killercoda-cli

[![PyPI - Version](https://img.shields.io/pypi/v/killercoda-cli.svg)](https://pypi.org/project/killercoda-cli)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/killercoda-cli.svg)](https://pypi.org/project/killercoda-cli)
[![codecov](https://codecov.io/gh/Piotr1215/killercoda-cli/graph/badge.svg?token=2NVHJY2T3L)](https://codecov.io/gh/Piotr1215/killercoda-cli)
[![CI](https://github.com/piotr1215/killercoda-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/piotr1215/killercoda-cli/actions/workflows/ci.yml)

**Table of Contents**

* [Installation](#installation)
* [Introduction](#introduction)
* [Documentation](#documentation)
  * [Requirements](#requirements)
  * [Example usage](#example-usage)
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

The interactive [killercoda] scenarios are a great way learn new technologies in
an _hands-on_ approach. However, creating the scenarios and managing can be
tedious and time consuming.

The `killercoda-cli` solves some of those problems by:

- Adding a new step after the existing last step and creating a directory for
  including foreground and background scripts placeholders.
- Renaming and re indexing step files and directories allowing for inserting a
  step in between existing steps and moving content _down_
- Updating the `index.json` file to reflect changes in step order and titles.

## Documentation

Autogenerated API documentation generated in [pdoc](https://pdoc.dev/docs/pdoc.html) available
at: https://piotr1215.github.io/killercoda-cli/killercoda_cli/cli.html.

### Requirements

- The tool must be run in a directory containing step files or directories (e.g. step1.md, step2/).
- An `index.json` file must be present in the directory, which contains metadata about the steps.

### Example usage

Suppose you have a scenario directory with the following structure:

    .
    ├── index.json
    ├── step1.md
    └── step2
        └── step2.md

And you want to insert a new step between `step1.md` and `step2/`, titled "New Step".

1. Run `killercoda-cli`.
2. Enter the title for the new step: "New Step".
3. Enter the step number to insert the new step at: 2.

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

## Disclaimer

This is an my personal project to easier create and manage killercoda scenarios.
Check out [killercoda] interactive scenarios to learn more about
the service.

## License

`killercoda-cli` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

[killercoda]: https://killercoda.com/
