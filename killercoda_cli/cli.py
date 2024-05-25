#!/usr/bin/env python3
import difflib
import json
import os
import subprocess
import sys
from typing import List, Optional


class FileOperation:
    def __init__(self, operation: str, path: str, content: Optional[str] = None, mode: Optional[int] = None):
        self.operation = operation
        self.path = path
        self.content = content
        self.mode = mode

    def __eq__(self, other):
        if not isinstance(other, FileOperation):
            return NotImplemented

        return (
            self.operation == other.operation
            and self.path == other.path
            and self.content == other.content
            and self.mode == other.mode
        )


def get_tree_structure():
    result = subprocess.run(["tree"], stdout=subprocess.PIPE)
    return result.stdout.decode("utf-8")


def generate_diff(old_tree, new_tree):
    diff = difflib.unified_diff(
        old_tree.splitlines(keepends=True),
        new_tree.splitlines(keepends=True),
        fromfile="Before changes",
        tofile="After changes",
    )
    return "".join(diff)


def get_current_steps_dict(directory_items):
    steps_dict = {}
    for item in directory_items:
        if item.startswith("step") and (os.path.isdir(item) or item.endswith(".md")):
            try:
                step_num = int(item.replace("step", "").replace(".md", ""))
                steps_dict[step_num] = item
            except ValueError:
                pass
    return steps_dict


def get_user_input(steps_dict, step_title_input, step_number_input, step_type_input):
    step_title = step_title_input
    highest_step_num = max(steps_dict.keys(), default=0)

    while True:
        step_number = int(step_number_input)
        if 1 <= step_number <= highest_step_num + 1:
            break
        else:
            raise ValueError(f"Invalid step number: {step_number_input}. Please enter a valid step number between 1 and {highest_step_num+1}.")

    step_type = step_type_input if step_type_input else 'regular'
    return step_title, step_number, step_type


def plan_renaming(steps_dict, insert_step_num):
    sorted_step_nums = sorted(steps_dict.keys())
    renaming_plan = []

    for step_num in sorted_step_nums:
        if step_num >= insert_step_num:
            renaming_plan.append((steps_dict[step_num], f"step{step_num + 1}"))

    renaming_plan.reverse()
    return renaming_plan


def calculate_renaming_operations(renaming_plan):
    file_operations = []
    for old_name, new_name in renaming_plan:
        file_operations.append(FileOperation("makedirs", new_name))

        if os.path.isdir(old_name):
            old_background = os.path.join(old_name, "background.sh")
            new_background = os.path.join(new_name, "background.sh")
            old_foreground = os.path.join(old_name, "foreground.sh")
            new_foreground = os.path.join(new_name, "foreground.sh")
            old_verify = os.path.join(old_name, "verify.sh")
            new_verify = os.path.join(new_name, "verify.sh")

            if os.path.isfile(old_background):
                file_operations.append(FileOperation("rename", old_background, content=new_background))
            if os.path.isfile(old_foreground):
                file_operations.append(FileOperation("rename", old_foreground, content=new_foreground))
            if os.path.isfile(old_verify):
                file_operations.append(FileOperation("rename", old_verify, content=new_verify))

            old_step_md = os.path.join(old_name, f"step{old_name.replace('step', '')}.md")
            new_step_md = os.path.join(new_name, f"step{new_name.replace('step', '')}.md")
            if os.path.isfile(old_step_md):
                file_operations.append(FileOperation("rename", old_step_md, content=new_step_md))

        else:
            new_step_md = f"{new_name}.md"
            file_operations.append(FileOperation("rename", old_name, content=new_step_md))

    return file_operations


def calculate_new_step_file_operations(insert_step_num: int, step_title: str, step_type: str) -> List[FileOperation]:
    new_step_folder = f"step{insert_step_num}"
    new_step_md = f"{new_step_folder}/step{insert_step_num}.md"
    new_step_verify = f"{new_step_folder}/verify.sh"
    new_step_background = f"{new_step_folder}/background.sh"
    new_step_foreground = f"{new_step_folder}/foreground.sh"

    file_operations = [
        FileOperation("makedirs", new_step_folder),
        FileOperation("write_file", new_step_md, content=f"# {step_title}\n"),
    ]

    if step_type == 'verify':
        file_operations.append(FileOperation("write_file", new_step_verify, content=f'#!/bin/sh\necho "{step_title} verification script"\n'))
        file_operations.append(FileOperation("chmod", new_step_verify, mode=0o755))
    else:
        file_operations.append(FileOperation("write_file", new_step_background, content=f'#!/bin/sh\necho "{step_title} background script"\n'))
        file_operations.append(FileOperation("write_file", new_step_foreground, content=f'#!/bin/sh\necho "{step_title} foreground script"\n'))
        file_operations.append(FileOperation("chmod", new_step_background, mode=0o755))
        file_operations.append(FileOperation("chmod", new_step_foreground, mode=0o755))

    return file_operations


def calculate_index_json_updates(insert_step_num, step_title, current_index_data, step_type):
    data = current_index_data

    if step_type == "verify":
        new_step_data = {
            "title": step_title,
            "text": f"step{insert_step_num}/step{insert_step_num}.md",
            "verify": f"step{insert_step_num}/verify.sh",
        }
    else:
        new_step_data = {
            "title": step_title,
            "text": f"step{insert_step_num}/step{insert_step_num}.md",
            "background": f"step{insert_step_num}/background.sh",
            "foreground": f"step{insert_step_num}/foreground.sh",
        }

    data["details"]["steps"].insert(insert_step_num - 1, new_step_data)

    for i in range(insert_step_num, len(data["details"]["steps"])):
        step = data["details"]["steps"][i]
        step_number = i + 1
        step["text"] = f"step{step_number}/step{step_number}.md"
        if "verify" in step:
            step["verify"] = f"step{step_number}/verify.sh"
        if "background" in step:
            step["background"] = f"step{step_number}/background.sh"
        if "foreground" in step:
            step["foreground"] = f"step{step_number}/foreground.sh"

    return data


def display_help():
    help_text = """
        Usage: killercoda-cli [OPTIONS]

        A CLI helper for writing KillerCoda scenarios and managing steps. This tool facilitates the addition, renaming, and renumbering of step files and directories in a structured and automated manner.

        Options:
          -h, --help    Show this message and exit.

        Basic Commands:
          No specific commands needed. Running 'killercoda-cli' starts the interactive process.

        Requirements:
          - The tool must be run in a directory containing step files or directories (e.g., step1.md, step2/).
          - An 'index.json' file must be present in the directory, which contains metadata about the steps.

        Functionality:
          - Renames and renumbers step files and directories based on user input.
          - Updates the 'index.json' file to reflect changes in step order and titles.
    """
    print(help_text)


def execute_file_operations(file_operations):
    for op in file_operations:
        print(op)
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
        old_tree_structure = get_tree_structure()
        directory_items = os.listdir(".")
        steps_dict = get_current_steps_dict(directory_items)
        if "index.json" not in directory_items:
            print("The 'index.json' file is missing. Please ensure it is present in the current directory.")
            sys.exit(1)
        step_title_input = input("Enter the title for the new step: ")
        step_type_input = input("Enter the type of the new step (default: 'regular', options: 'regular', 'verify'): ")
        highest_step_num = max(steps_dict.keys(), default=0)
        step_number_input = input(f"Enter the step number to insert the new step at (1-{highest_step_num+1}): ")
        try:
            step_title, insert_step_num, step_type = get_user_input(
                steps_dict, step_title_input, step_number_input, step_type_input
            )
        except ValueError as e:
            print(f"Invalid step number: {e}")
            return
        renaming_plan = plan_renaming(steps_dict, insert_step_num)
        renaming_operations = calculate_renaming_operations(renaming_plan)
        new_step_operations = calculate_new_step_file_operations(insert_step_num, step_title, step_type)
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
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
