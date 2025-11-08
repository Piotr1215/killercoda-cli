#!/usr/bin/env python3

"""
Assets module for killercoda-cli.
Provides functionality for generating scenario assets.
"""

import os

from cookiecutter.main import cookiecutter


def generate_assets():
    """
    Generate scenario assets from cookiecutter template.

    Downloads and instantiates the killercoda-assets cookiecutter template
    in the current working directory. The template provides predefined
    folder structures and files for interactive scenarios.

    Raises:
        Exception: If template generation fails
    """
    try:
        template_repo = 'https://github.com/Piotr1215/cookiecutter-killercoda-assets'
        output_dir = os.getcwd()

        print(f"Generating assets from template: {template_repo}")
        print(f"Output directory: {output_dir}")

        cookiecutter(template_repo, no_input=True, extra_context={"project_name": "killercoda-assets"}, output_dir=output_dir)

        print("Assets generated successfully.")
    except Exception as e:
        print(f"An error occurred in generate_assets: {e}")
        raise
