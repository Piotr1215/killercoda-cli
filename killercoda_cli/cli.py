#!/usr/bin/env python3

"""
Main CLI module for the killercoda-cli tool.
This module provides functionality for managing KillerCoda scenario steps,
including step creation, renumbering, and file management.
"""

import difflib
import json
import os
import subprocess
import sys
from typing import List, Optional
from cookiecutter.main import cookiecutter
from killercoda_cli.__about__ import __version__
from killercoda_cli.scenario_init import init_project

class FileOperation:
    """
    Defines file operation types and their parameters.
    Each operation represents a specific file system action:
    
    Operations:
    - 'makedirs': Create directory hierarchy
    - 'write_file': Write content to file
    - 'chmod': Change file permissions
    - 'rename': Rename file or directory
    """
    def __init__(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        mode: Optional[int] = None,
    ):
        """
        Initialize a file operation with required parameters.
        
        Args:
            operation: Type of operation ('makedirs', 'write_file', 'chmod', 'rename')
            path: Target file/directory path
            content: File content for write operations
            mode: Permission mode for chmod operations
        """
        self.operation = operation
        self.path = path
        self.content = content
        self.mode = mode

    def __eq__(self, other):
        """
        Compare two FileOperation instances for equality.
        Compares all attributes: operation, path, content, and mode.
        """
        if not isinstance(other, FileOperation):
            return NotImplemented
        return (
            self.operation == other.operation
            and self.path == other.path
            and self.content == other.content
            and self.mode == other.mode
        )

    def __repr__(self):
        """
        String representation of the FileOperation instance.
        Includes all attributes for debugging purposes.
        """
        return (f"FileOperation(operation={self.operation}, path={self.path}, "
                f"content={self.content}, mode={self.mode})")

#  TODO:(piotr1215) fallback if tree is not installed
def get_tree_structure():
    """
    Get directory structure using 'tree' command.
    
    Returns:
        str: Directory tree as formatted string
    """
    result = subprocess.run(["tree"], stdout=subprocess.PIPE)
    return result.stdout.decode("utf-8")

def generate_diff(old_tree, new_tree):
    """
    Generate unified diff between directory trees.
    
    Args:
        old_tree: Original directory structure
        new_tree: New directory structure
        
    Returns:
        str: Unified diff output
    """
    diff = difflib.unified_diff(
        old_tree.splitlines(keepends=True),
        new_tree.splitlines(keepends=True),
        fromfile="Before changes",
        tofile="After changes",
    )
    return "".join(diff)

def get_current_steps_dict(directory_items):
    """
    Map step numbers to file paths.
    
    Args:
        directory_items: List of directory contents
        
    Returns:
        dict: {step_number: file_path}
    """
    steps_dict = {}
    for item in directory_items:
        if item.startswith("step") and (os.path.isdir(item) or item.endswith(".md")):
            try:
                step_num = int(item.replace("step", "").replace(".md", ""))
                steps_dict[step_num] = item
            except ValueError:
                pass
    return steps_dict

def get_user_input(steps_dict, step_title_input, step_number_input):
    """
    Process and validate user input for new step.
    
    Args:
        steps_dict: Current step mapping
        step_title_input: New step title
        step_number_input: Desired step number
        
    Returns:
        tuple: (step_title, step_number)
    
    Raises:
        ValueError: If step number invalid
    """
    step_title = step_title_input
    highest_step_num = max(steps_dict.keys(), default=0)
    while True:
        step_number = int(step_number_input)
        if 1 <= step_number <= highest_step_num + 1:
            break
        else:
            raise ValueError(
                f"Invalid step number: {step_number_input}. Please enter a valid step number between 1 and {highest_step_num+1}."
            )
    return step_title, step_number

def plan_renaming(steps_dict, insert_step_num):
    """
    Plan step renaming operations.
    
    Args:
        steps_dict: Current step mapping
        insert_step_num: New step position
        
    Returns:
        list: [(old_name, new_name), ...]
    """
    sorted_step_nums = sorted(steps_dict.keys())
    renaming_plan = []
    for step_num in sorted_step_nums:
        if step_num >= insert_step_num:
            renaming_plan.append((steps_dict[step_num], f"step{step_num + 1}"))
    renaming_plan.reverse()
    return renaming_plan

#  TODO:(piotr1215) replace os calls with data structure
def calculate_renaming_operations(renaming_plan):
    """
    Generate file operations for renaming.
    
    Args:
        renaming_plan: List of rename operations
        
    Returns:
        list: FileOperation instances
    """
    file_operations = []
    for old_name, new_name in renaming_plan:
        file_operations.append(FileOperation("makedirs", new_name))
        if os.path.isdir(old_name):
            # Handle step directory contents
            for script in ["background.sh", "foreground.sh", "verify.sh"]:
                old_script = os.path.join(old_name, script)
                new_script = os.path.join(new_name, script)
                if os.path.isfile(old_script):
                    file_operations.append(
                        FileOperation("rename", old_script, content=new_script)
                    )
            
            # Handle step markdown file
            old_step_md = os.path.join(
                old_name, f"step{old_name.replace('step', '')}.md"
            )
            new_step_md = os.path.join(
                new_name, f"step{new_name.replace('step', '')}.md"
            )
            if os.path.isfile(old_step_md):
                file_operations.append(
                    FileOperation("rename", old_step_md, content=new_step_md)
                )
        else:
            # Handle standalone markdown file
            new_step_md = f"{new_name}.md"
            file_operations.append(
                FileOperation("rename", old_name, content=new_step_md)
            )
    return file_operations

def calculate_new_step_file_operations(
    insert_step_num: int, step_title: str, step_type: str
) -> List[FileOperation]:
    """
    Generate operations for new step creation.
    
    Args:
        insert_step_num: Step number to insert
        step_title: New step title
        step_type: Step type ('r' or 'v')
        
    Returns:
        List[FileOperation]: Creation operations
    """
    new_step_folder = f"step{insert_step_num}"
    new_step_md = f"{new_step_folder}/step{insert_step_num}.md"
    file_operations = [
        FileOperation("makedirs", new_step_folder),
        FileOperation("write_file", new_step_md, content=f"# {step_title}\n"),
    ]
    
    if step_type == "r":
        # Regular step with background/foreground scripts
        new_step_background = f"{new_step_folder}/background.sh"
        new_step_foreground = f"{new_step_folder}/foreground.sh"
        file_operations += [
            FileOperation(
                "write_file",
                new_step_background,
                content=f'#!/bin/sh\necho "{step_title} script"\n',
            ),
            FileOperation(
                "write_file",
                new_step_foreground,
                content=f'#!/bin/sh\necho "{step_title} script"\n',
            ),
            FileOperation("chmod", new_step_background, mode=0o755),
            FileOperation("chmod", new_step_foreground, mode=0o755),
        ]
    elif step_type == "v":
        # Verify step with verify script
        new_step_verify = f"{new_step_folder}/verify.sh"
        file_operations += [
            FileOperation(
                "write_file",
                new_step_verify,
                content=f'#!/bin/sh\necho "{step_title} script"\n',
            ),
            FileOperation("chmod", new_step_verify, mode=0o755),
        ]
    return file_operations

def calculate_index_json_updates(insert_step_num, step_title, current_index_data, step_type):
    """
    Update index.json for new step.
    
    Args:
        insert_step_num: Step number to insert
        step_title: New step title
        current_index_data: Current index.json content
        step_type: Step type ('r' or 'v')
        
    Returns:
        dict: Updated index.json data
    """
    data = current_index_data
    new_step_data = {
        "title": step_title,
        "text": f"step{insert_step_num}/step{insert_step_num}.md",
    }
    
    if step_type == "v":
        new_step_data["verify"] = f"step{insert_step_num}/verify.sh"
    else:
        new_step_data["background"] = f"step{insert_step_num}/background.sh"
        
    data["details"]["steps"].insert(insert_step_num - 1, new_step_data)
    
    # Update subsequent step numbers
    for i in range(insert_step_num, len(data["details"]["steps"])):
        step = data["details"]["steps"][i]
        step_number = i + 1
        step["text"] = f"step{step_number}/step{step_number}.md"
        if "verify" in step:
            step["verify"] = f"step{step_number}/verify.sh"
        else:
            step["background"] = f"step{step_number}/background.sh"
            
    return data

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

def execute_file_operations(file_operations):
    """
    Execute file system operations.
    
    Args:
        file_operations: List of FileOperation instances
    """
    for operation in file_operations:
        if operation.operation == "makedirs":
            os.makedirs(operation.path, exist_ok=True)
        elif operation.operation == "write_file":
            with open(operation.path, "w") as file:
                file.write(operation.content)
        elif operation.operation == "chmod":
            os.chmod(operation.path, operation.mode)
        elif operation.operation == "rename":
            os.rename(operation.path, operation.content)

def generate_assets():
    """Generate asset directory from template."""
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

def validate_course(course_path: str) -> tuple[bool, str]:
    """
    Validate course structure and content.
    
    Args:
        course_path: Path to course directory
        
    Returns:
        tuple[bool, str]: (is_valid, message)
    """
    try:
        # Check index.json existence and content
        index_path = os.path.join(course_path, "index.json")
        if not os.path.exists(index_path):
            return False, "Missing index.json file"
            
        with open(index_path) as f:
            content = f.read().strip()
            if not content:
                return False, "Empty index.json file"
                
            try:
                index_data = json.loads(content)
            except json.JSONDecodeError:
                return False, "Invalid JSON in index.json"
                
            if not index_data:
                return False, "Empty JSON object in index.json"
                
        # Validate required fields
        if not all(key in index_data and index_data[key] for key in ["title", "description", "details"]):
            return False, "Missing required fields"
            
        if "steps" not in index_data["details"] or not index_data["details"]["steps"]:
            return False, "Missing steps in index.json"
            
        # Validate each step
        steps = index_data["details"]["steps"]
        for i, step in enumerate(steps, 1):
            if not all(key in step and step[key] for key in ["title", "text"]):
                return False, f"Step {i} missing required fields"
                
            step_file = os.path.join(course_path, step["text"])
            if not os.path.exists(step_file):
                return False, f"Missing step file: {step['text']}"
                
            if "verify" in step:
                verify_file = os.path.join(course_path, step["verify"])
                if not os.path.exists(verify_file):
                    return False, f"Missing verify script: {step['verify']}"
            if "background" in step:
                background_file = os.path.join(course_path, step["background"])
                if not os.path.exists(background_file):
                    return False, f"Missing background script: {step['background']}"
                    
        return True, "Valid"
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_all(base_path: str) -> bool:
    """
    Validate killercoda scenario structure:
    - index.json exists and is valid JSON
    - Referenced step files exist
    """
    def print_status(check: str, status: bool, message: str = ""):
        symbol = "[+]" if status else "[-]"
        result = "ok" if status else "failed"
        if message:
            print(f"{symbol}{check:<50} {result} - {message}")
        else:
            print(f"{symbol}{check:<50} {result}")

    print("\n=== Scenario Validation ===")

    # Empty directory without index.json is valid
    if not os.path.exists(os.path.join(base_path, "index.json")):
        if not os.listdir(base_path):
            print_status("empty-directory", True)
            print(f"\nValidation Status: PASSED")
            print(f"Location: {os.path.abspath(base_path)}")
            return True
        print_status("index.json", False, "File not found")
        return False

    all_valid = True
    index_path = os.path.join(base_path, "index.json")

    try:
        with open(index_path) as f:
            content = f.read().strip()
            if not content:
                print_status("index.json", False, "Empty file")
                return False
                
            try:
                index_data = json.loads(content)
                print_status("json-syntax", True)
            except json.JSONDecodeError:
                print_status("json-syntax", False, "Invalid JSON")
                return False

            if "details" not in index_data or "steps" not in index_data["details"]:
                print_status("steps-structure", False, "Missing steps array")
                return False

            for i, step in enumerate(index_data["details"]["steps"], 1):
                if "text" not in step:
                    print_status(f"step-{i}", False, "Missing text field")
                    all_valid = False
                    continue

                file_path = os.path.join(base_path, step["text"])
                exists = os.path.exists(file_path)
                print_status(f"step-{i}", exists, "" if exists else f"Missing {step['text']}")
                all_valid = all_valid and exists

    except Exception as e:
        print_status("validation", False, str(e))
        return False

    print(f"\nValidation Status: {'PASSED' if all_valid else 'FAILED'}")
    print(f"Location: {os.path.abspath(base_path)}")
    return all_valid

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
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
