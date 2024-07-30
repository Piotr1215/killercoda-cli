#!/usr/bin/env python3
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
    Define a type hint for the different types of file operations that can be performed.
    This Union type allows for specifying the operation (as a string literal indicating the type of action),
    and the required arguments for each operation type:
    - 'makedirs': Create a new directory; requires the path of the directory.
    - 'write_file': Write content to a file; requires the file path and the content to write.
    - 'chmod': Change the file mode; requires the file path and the new mode (as an integer).

    """

    def __init__(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        mode: Optional[int] = None,
    ):
        self.operation = operation
        self.path = path
        self.content = content
        self.mode = mode

    def __eq__(self, other):
        if not isinstance(other, FileOperation):
            # don't attempt to compare against unrelated types
            return NotImplemented

        return (
            self.operation == other.operation
            and self.path == other.path
            and self.content == other.content
            and self.mode == other.mode
        )

    def __repr__(self):
        return (f"FileOperation(operation={self.operation}, path={self.path}, "
                f"content={self.content}, mode={self.mode})")


#  TODO:(piotr1215) fallback if tree is not installed
def get_tree_structure():
    """
    Retrieves the current directory structure using the 'tree' command.

    Returns:
        A string representation of the directory structure.
    """
    # Get the current tree structure as a string
    result = subprocess.run(["tree"], stdout=subprocess.PIPE)
    return result.stdout.decode("utf-8")


def generate_diff(old_tree, new_tree):
    """
    Generate a unified diff between two directory tree structures.

    Args:
        old_tree (str): The original directory tree structure.
        new_tree (str): The new directory tree structure after changes.

    Returns:
        str: A string containing the unified diff.
    """
    # Use difflib to print a diff of the two tree outputs
    diff = difflib.unified_diff(
        old_tree.splitlines(keepends=True),
        new_tree.splitlines(keepends=True),
        fromfile="Before changes",
        tofile="After changes",
    )
    return "".join(diff)


def get_current_steps_dict(directory_items):
    """
    Build a dictionary mapping step numbers to their respective paths.

    Args:
        directory_items (list): A list of items (files and directories) in the current directory.

    Returns:
        dict: A dictionary where keys are step numbers and values are the corresponding step paths.
    """
    steps_dict = {}
    for item in directory_items:
        if item.startswith("step") and (os.path.isdir(item) or item.endswith(".md")):
            # Extract the step number from the name
            try:
                step_num = int(item.replace("step", "").replace(".md", ""))
                steps_dict[step_num] = item
            except ValueError:
                pass  # This handles cases where the step name is not a number
    return steps_dict


def get_user_input(steps_dict, step_title_input, step_number_input):
    """
    Prompt the user for the new step's title and the desired step number, then validate the input.

    Args:
        steps_dict (dict): A dictionary mapping existing step numbers to their paths.
        step_title_input (str): The title for the new step provided by the user.
        step_number_input (str): The step number where the new step should be inserted, provided by the user.

    Returns:
        tuple: A tuple containing the validated step title and step number.
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
    Create a plan for renaming step directories and files after inserting a new step.

    Args:
        steps_dict (dict): A dictionary mapping existing step numbers to their paths.
        insert_step_num (int): The step number at which the new step will be inserted.

    Returns:
        list: A list of tuples representing the renaming operations required.
    """
    # Sort the keys to ensure we rename in the correct order
    sorted_step_nums = sorted(steps_dict.keys())
    renaming_plan = []

    # Determine which steps need to be shifted
    for step_num in sorted_step_nums:
        if step_num >= insert_step_num:
            renaming_plan.append((steps_dict[step_num], f"step{step_num + 1}"))

    # Reverse the plan to avoid overwriting any steps
    renaming_plan.reverse()
    return renaming_plan


#  TODO:(piotr1215) replace os calls with data structure
def calculate_renaming_operations(renaming_plan):
    """
    Calculate the file operations required to execute the renaming plan.

    Args:
        renaming_plan (list): A list representing the renaming operations required, where each item
                              is a tuple of the form (old_name, new_name).

    Returns:
        list: A list of FileOperation objects to be performed for renaming.
    """
    file_operations = []
    for old_name, new_name in renaming_plan:
        # Create the new directory if it doesn't exist
        file_operations.append(FileOperation("makedirs", new_name))

        # If it's a directory, we need to check for and move necessary files
        if os.path.isdir(old_name):
            # Paths for background and foreground scripts
            old_background = os.path.join(old_name, "background.sh")
            new_background = os.path.join(new_name, "background.sh")
            old_foreground = os.path.join(old_name, "foreground.sh")
            new_foreground = os.path.join(new_name, "foreground.sh")
            old_verify = os.path.join(old_name, "verify.sh")
            new_verify = os.path.join(new_name, "verify.sh")

            # Check and move background.sh if it exists
            if os.path.isfile(old_background):
                file_operations.append(
                    FileOperation("rename", old_background, content=new_background)
                )

            # Check and move foreground.sh if it exists
            if os.path.isfile(old_foreground):
                file_operations.append(
                    FileOperation("rename", old_foreground, content=new_foreground)
                )

            # Check and move verify.sh if it exists
            if os.path.isfile(old_verify):
                file_operations.append(
                    FileOperation("rename", old_verify, content=new_verify)
                )

            # Rename the step markdown file
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
            # If it's just a markdown file without a directory, prepare to rename it
            new_step_md = f"{new_name}.md"
            file_operations.append(
                FileOperation("rename", old_name, content=new_step_md)
            )

    return file_operations



def calculate_new_step_file_operations(
    insert_step_num: int, step_title: str, step_type: str
) -> List[FileOperation]:
    """
    Calculate the file operations needed to add a new step to the scenario.

    This function builds a list of file operations (as tuples) to create the necessary files
    and directories for a new step in a structured and automated manner.

    Args:
        insert_step_num (int): The step number where the new step will be inserted.
        step_title (str): The title for the new step.
        step_type (str): The type of the step, either "regular" or "verify".

    Returns:
        List[FileOperation]: A list of file operations that, when executed, will set up
                             the new step's directory, markdown file, and script files.
    """
    new_step_folder = f"step{insert_step_num}"
    new_step_md = f"{new_step_folder}/step{insert_step_num}.md"

    file_operations = [
        FileOperation("makedirs", new_step_folder),
        FileOperation("write_file", new_step_md, content=f"# {step_title}\n"),
    ]

    if step_type == "r":
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
    Update the index.json structure after inserting a new step.

    Args:
        insert_step_num (int): The step number where the new step will be inserted.
        step_title (str): The title for the new step.
        current_index_data (dict): The current data from index.json.
        step_type (str): The type of the step, either "verify" or "regular".

    Returns:
        dict: The updated index.json data reflecting the new step insertion.
    """
    # Load the index.json file
    data = current_index_data

    # Create new step entry based on the step type
    new_step_data = {
        "title": step_title,
        "text": f"step{insert_step_num}/step{insert_step_num}.md",
    }
    if step_type == "v":
        new_step_data["verify"] = f"step{insert_step_num}/verify.sh"
    else:  # Default to "regular"
        new_step_data["background"] = f"step{insert_step_num}/background.sh"

    # Insert the new step data into the steps list
    data["details"]["steps"].insert(insert_step_num - 1, new_step_data)

    # Update the step numbers in the JSON structure
    for i in range(insert_step_num, len(data["details"]["steps"])):
        step = data["details"]["steps"][i]
        step_number = i + 1  # Convert to 1-based index
        step["text"] = f"step{step_number}/step{step_number}.md"
        if "verify" in step:
            step["verify"] = f"step{step_number}/verify.sh"
        else:
            step["background"] = f"step{step_number}/background.sh"

    # Write the updated data back to index.json
    return data


def display_help():
    """
    Display the help text for the CLI tool.

    This function prints the usage and help information for the tool.
    """
    help_text = """
        Usage: killercoda-cli [OPTIONS]

        A CLI helper for writing KillerCoda scenarios and managing steps. This tool facilitates the addition, renaming, and renumbering of step files and directories in a structured and automated manner.

        Options:
          -h, --help    Show this message and exit.
          -v, --version Display the version of the tool.

        Basic Commands:
          Running 'killercoda-cli' starts the interactive process.
          init: Initialize a new project by creating an 'index.json' file.
          assets: Generate the predefined assets folder structure.

        Requirements:
          - The tool must be run in a directory containing step files or directories (e.g., step1.md, step2/).
          - An 'index.json' file must be present in the directory, which contains metadata about the steps.

        Functionality:
          - Renames and renumbers step files and directories based on user input.
          - Updates the 'index.json' file to reflect changes in step order and titles.
    """
    print(help_text)


def execute_file_operations(file_operations):
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


def main():
    """
    This function orchestrates the entire process of adding a new step to the scenario,
    from taking user input to updating the file system and the index.json file.
    It ensures that the 'index.json' file is present, gathers the current directory structure,
    prompts the user for the new step's title and number, calculates the necessary file operations,
    and applies those changes to the file system and the index.json file.
    Finally, it outputs the changes to the directory structure for the user to review.
    """
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
            display_help()
            return
        if len(sys.argv) > 1 and sys.argv[1] in ["-v", "--version"]:
            print(f"killercoda-cli v{__version__}")
            return
        if len(sys.argv) > 1 and sys.argv[1] in ["init"]:
            init_project()
            return
        if len(sys.argv) > 1 and sys.argv[1] in ["assets"]:
            generate_assets()
            return
        
        old_tree_structure = get_tree_structure()
        directory_items = os.listdir(".")
        steps_dict = get_current_steps_dict(directory_items)
        if "index.json" not in directory_items:
            print(
                "The 'index.json' file is missing. Please ensure it is present in the current directory."
            )
            return
        step_title_input = input("Enter the title for the new step: ")
        highest_step_num = max(steps_dict.keys(), default=0)
        step_number_input = input(
            f"Enter the step number to insert the new step at (1-{highest_step_num+1}): "
        )
        step_type = input("Enter the type of step (r for regular or v for verify): ")
        step_title, insert_step_num = get_user_input(
            steps_dict, step_title_input, step_number_input
        )
        renaming_plan = plan_renaming(steps_dict, insert_step_num)
        renaming_operations = calculate_renaming_operations(renaming_plan)
        new_step_operations = calculate_new_step_file_operations(
            insert_step_num, step_title, step_type
        )
        index_file_path = "index.json"
        with open(index_file_path, "r") as index_file:
            current_index_data = json.load(index_file)
        updated_index_data = calculate_index_json_updates(
            insert_step_num, step_title, current_index_data, step_type
        )
        execute_file_operations(renaming_operations + new_step_operations)
        with open(index_file_path, "w") as index_file:
            json.dump(updated_index_data, index_file, ensure_ascii=False, indent=4)
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
