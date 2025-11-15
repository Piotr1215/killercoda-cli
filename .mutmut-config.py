#!/usr/bin/env python3
"""
Mutation testing configuration for killercoda-cli.

This configuration skips test files and focuses on production code.
"""


def pre_mutation(context):
    """
    Skip test files from mutation testing.

    We only want to mutate production code in killercoda_cli/,
    not the test files themselves.
    """
    # Skip test files
    if 'test_' in context.filename:
        context.skip = True

    # Skip __about__.py (version info)
    if '__about__' in context.filename:
        context.skip = True
