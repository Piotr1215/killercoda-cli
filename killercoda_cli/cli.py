#!/usr/bin/env python3

"""
Main CLI module for the killercoda-cli tool.
This module provides the main entry point and command processing for the CLI.
"""

import json
import os
import sys
import traceback

from killercoda_cli.__about__ import __version__
from killercoda_cli.file_operations import FileOperation, get_tree_structure, generate_diff, execute_file_operations
from killercoda_cli.step_management import (
    get_current_steps_dict, get_user_input, plan_renaming, 
    calculate_renaming_operations, calculate_new_step_file_operations, 
    calculate_index_json_updates
)
from killercoda_cli.scenario_init import init_project
from killercoda_cli.validation import validate_course, validate_all
from killercoda_cli.assets import generate_assets


def display_help():
    """Display CLI usage information."""
    help_text = """
        Usage: killercoda-cli [OPTIONS]
        A CLI helper for writing KillerCoda scenarios and managing steps.
        
        Options:
          -h, --help    Show this message and exit.
          -v, --version Display the version of the tool.
          
        Commands:
          Running 'killercoda-cli' starts the interactive process.
          init: Initialize a new project by creating an 'index.json' file.
          assets: Generate the predefined assets folder structure.
          validate [--path PATH]: Validate courses in the specified path
                                (defaults to current directory)
                                
        Requirements:
          - The tool must be run in a directory containing step files or directories
          - An 'index.json' file must be present in the directory
          
        Functionality:
          - Renames and renumbers step files and directories based on user input
          - Updates the 'index.json' file to reflect changes in step order and titles
          - Validates course structure and configuration
    """
    print(help_text)


def main():
    """
    Main CLI entry point.
    Handles command processing and orchestrates operations:
    - Step addition/management
    - Project initialization
    - Asset generation
    - Scenario validation
    """
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] in ["-h", "--help"]:
                display_help()
                return
            elif sys.argv[1] in ["-v", "--version"]:
                print(f"killercoda-cli v{__version__}")
                return
            elif sys.argv[1] == "init":
                init_project()
                return
            elif sys.argv[1] == "assets":
                generate_assets()
                return
            elif sys.argv[1] == "validate":
                # Get path argument or use current directory
                path = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--path" else "."
                success = validate_all(path)
                sys.exit(0 if success else 1)
                return
        
        # Interactive mode for step management
        old_tree_structure = get_tree_structure()
        directory_items = os.listdir(".")
        steps_dict = get_current_steps_dict(directory_items)
        
        if "index.json" not in directory_items:
            print(
                "The 'index.json' file is missing. Please ensure it is present in the current directory."
            )
            return
            
        # Get user input for new step
        step_title_input = input("Enter the title for the new step: ")
        highest_step_num = max(steps_dict.keys(), default=0)
        step_number_input = input(
            f"Enter the step number to insert the new step at (1-{highest_step_num+1}): "
        )
        step_type = input("Enter the type of step (r for regular or v for verify): ")
        
        # Process step addition
        step_title, insert_step_num = get_user_input(
            steps_dict, step_title_input, step_number_input
        )
        renaming_plan = plan_renaming(steps_dict, insert_step_num)
        renaming_operations = calculate_renaming_operations(renaming_plan)
        new_step_operations = calculate_new_step_file_operations(
            insert_step_num, step_title, step_type
        )
        
        # Update index.json
        index_file_path = "index.json"
        with open(index_file_path, "r") as index_file:
            current_index_data = json.load(index_file)
            
        updated_index_data = calculate_index_json_updates(
            insert_step_num, step_title, current_index_data, step_type
        )
        
        # Execute file operations
        execute_file_operations(renaming_operations + new_step_operations)
        with open(index_file_path, "w") as index_file:
            json.dump(updated_index_data, index_file, ensure_ascii=False, indent=4)
            
        # Show changes
        new_tree_structure = get_tree_structure()
        tree_diff = generate_diff(old_tree_structure, new_tree_structure)
        print("\nFile structure changes:")
        print(tree_diff, end="")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
