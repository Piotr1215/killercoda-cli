# Contributing to killercoda-cli

Thank you for your interest in contributing to killercoda-cli! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows a standard Code of Conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/killercoda-cli.git
   cd killercoda-cli
   ```
3. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

This project uses [Hatch](https://hatch.pypa.io/) for development workflow management.

### Install Hatch

```bash
pip install hatch
```

### Install the package in development mode

```bash
pip install -e .
```

### Available Development Environments

- **default**: Basic development environment
- **test**: Testing environment with coverage tools
- **lint**: Linting and formatting with ruff
- **types**: Type checking with mypy
- **docs**: Documentation generation with pdoc

## Running Tests

### Unit Tests

```bash
hatch run test:unit
```

### Coverage Report

```bash
hatch run test:unit
hatch run test:coverage-report
```

### Type Checking

```bash
hatch run types:check
```

## Code Style

This project uses [ruff](https://github.com/astral-sh/ruff) for both linting and formatting.

### Format Code

```bash
hatch run lint:format
```

### Check Linting

```bash
hatch run lint:check
```

### Check Formatting

```bash
hatch run lint:format-check
```

### Run All Linting Checks

```bash
hatch run lint:all
```

### Code Style Guidelines

- Follow PEP 8 style guidelines
- Maximum line length: 100 characters
- Use type hints where appropriate
- Write clear, descriptive docstrings for all public functions and classes
- Keep functions focused and single-purpose

## Submitting Changes

1. Ensure all tests pass and code is properly formatted:
   ```bash
   hatch run lint:all
   hatch run test:unit
   hatch run types:check
   ```

2. Commit your changes with a clear, descriptive commit message:
   ```bash
   git commit -m "feat: add new feature X"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `chore:` for maintenance tasks
   - `refactor:` for code refactoring

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request on GitHub with:
   - Clear description of the changes
   - Reference to any related issues
   - Screenshots/examples if applicable

## Reporting Issues

When reporting issues, please include:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment information (OS, Python version, killercoda-cli version)
- Relevant error messages or logs

## Documentation

- Update documentation for any changed functionality
- Add docstrings to new functions and classes
- Update the README.md if necessary
- Generate and review documentation:
  ```bash
  hatch run docs:pdoc killercoda_cli -o docs
  ```

## Questions?

If you have questions or need help, feel free to:
- Open an issue on GitHub
- Reach out to the maintainers

Thank you for contributing!
