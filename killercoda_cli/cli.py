#!/usr/bin/env python3
import os
import json
import subprocess
import difflib
import sys

def get_tree_structure():
    """
    Retrieves the current directory structure using the 'tree' command.

    Returns:
        A string representation of the directory structure.
    """
    # Get the current tree structure as a string
    result = subprocess.run(['tree'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

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
        fromfile='Before changes',
        tofile='After changes',
    )
    return ''.join(diff)

# 1. Traverse the current directory and build a dictionary mapping step numbers to paths
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
        if item.startswith('step') and (os.path.isdir(item) or item.endswith('.md')):
            # Extract the step number from the name
            try:
                step_num = int(item.replace('step', '').replace('.md', ''))
                steps_dict[step_num] = item
            except ValueError:
                pass  # This handles cases where the step name is not a number
    return steps_dict

# 2. Take input from the user for the new step's name and the desired step number
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
            raise ValueError(f"Invalid step number: {step_number_input}. Please enter a valid step number between 1 and {highest_step_num+1}.")

    return step_title, step_number

# 3. Determine the renaming and shifting required based on user input
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

def calculate_renaming_operations(renaming_plan):
    """
    Calculate the file operations required to execute the renaming plan.

    Args:
        renaming_plan (list): A list of tuples representing the renaming operations required.

    Returns:
        list: A list of file operations (as tuples) to be performed for renaming.
    """
    # Execute the renaming plan
    file_operations = []
    for old_name, new_name in renaming_plan:
        # Make the new directory if it doesn't exist
        file_operations.append(('makedirs', new_name))
        # If it's a directory, we need to check for background.sh and foreground.sh
        if os.path.isdir(old_name):
            # Check and move background.sh if it exists
            old_background = f"{old_name}/background.sh"
            new_background = f"{new_name}/background.sh"
            if os.path.isfile(old_background):
                file_operations.append(('rename', old_background, new_background))
            # Check and move foreground.sh if it exists
            old_foreground = f"{old_name}/foreground.sh"
            new_foreground = f"{new_name}/foreground.sh"
            if os.path.isfile(old_foreground):
                file_operations.append(('rename', old_foreground, new_foreground))
            # Rename the step markdown file
            old_step_md = f"{old_name}/step{old_name.replace('step', '')}.md"
            new_step_md = f"{new_name}/step{new_name.replace('step', '')}.md"
            if os.path.isfile(old_step_md):
                file_operations.append(('rename', old_step_md, new_step_md))
        else:
            # If it's just a markdown file without a directory
            new_step_md = f"{new_name}.md"
            file_operations.append(('rename', old_name, new_step_md))
    return file_operations

def calculate_new_step_file_operations(insert_step_num, step_title):
    """
    Calculate the file operations for adding a new step with the given title and step number.

    Args:
        insert_step_num (int): The step number where the new step will be inserted.
        step_title (str): The title for the new step.

    Returns:
        list: A list of file operations (as tuples) to create the new step's files and directories.
    """
    # Add the new step folder and files
    new_step_folder = f"step{insert_step_num}"
    new_step_md = f"{new_step_folder}/step{insert_step_num}.md"
    new_step_background = f"{new_step_folder}/background.sh"
    new_step_foreground = f"{new_step_folder}/foreground.sh"

    file_operations = [('makedirs', new_step_folder)]
    
    # Write the step markdown file
    file_operations.append(('write_file', new_step_md, f"# {step_title}\n"))
    
    # Write a simple echo command to the background and foreground scripts
    script_content = f"#!/bin/sh\necho \"{step_title} script\"\n"
    
    file_operations.append(('write_file', new_step_background, script_content))
    file_operations.append(('write_file', new_step_foreground, script_content))
    
    file_operations.append(('chmod', new_step_background, 0o755))
    file_operations.append(('chmod', new_step_foreground, 0o755))

    return file_operations

def calculate_index_json_updates(steps_dict, insert_step_num, step_title, current_index_data):
    """
    Update the index.json structure after inserting a new step.

    Args:
        steps_dict (dict): A dictionary mapping existing step numbers to their paths.
        insert_step_num (int): The step number where the new step will be inserted.
        step_title (str): The title for the new step.
        current_index_data (dict): The current data from index.json.

    Returns:
        dict: The updated index.json data reflecting the new step insertion.
    """
    # Load the index.json file
    data = current_index_data

    # Create new step entry
    new_step_data = {
        "title": step_title,
        "text": f"step{insert_step_num}/step{insert_step_num}.md",
        "background": f"step{insert_step_num}/background.sh"
    }

    # Insert the new step data into the steps list
    data['details']['steps'].insert(insert_step_num - 1, new_step_data)

    # Update the step numbers in the JSON structure
    for i in range(insert_step_num, len(data['details']['steps'])):
        step = data['details']['steps'][i]
        step_number = i + 1  # Convert to 1-based index
        step["text"] = f"step{step_number}/step{step_number}.md"
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

def main():
    """
    The main entry point for the CLI tool.

    This function orchestrates the entire process of adding a new step to the scenario,
    from taking user input to updating the file system and the index.json file.
    It ensures that the 'index.json' file is present, gathers the current directory structure,
    prompts the user for the new step's title and number, calculates the necessary file operations,
    and applies those changes to the file system and the index.json file.
    Finally, it outputs the changes to the directory structure for the user to review.
    """
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        display_help()
        sys.exit()
    # Check for the presence of an 'index.json' file
    old_tree_structure = get_tree_structure()
    directory_items = os.listdir('.')
    steps_dict = get_current_steps_dict(directory_items)
    if not steps_dict:
        print("No step files or directories found. Please run this command in a directory containing step files or directories.")
        sys.exit(1)
    if 'index.json' not in os.listdir('.'):
        print("The 'index.json' file is missing. Please ensure it is present in the current directory.")
        sys.exit(1)
    if not steps_dict:
        print("No step files or directories found. Please run this command in a directory containing step files or directories.")
        sys.exit(1)
    step_title_input = input("Enter the title for the new step: ")
    highest_step_num = max(steps_dict.keys(), default=0)
    while True:
        try:
            step_number_input = input(f"Enter the step number to insert the new step at (1-{highest_step_num+1}): ")
            insert_step_num = int(step_number_input)
            if 1 <= insert_step_num <= highest_step_num + 1:
                break
            else:
                print(f"Please enter a valid step number between 1 and {highest_step_num+1}.")
        except ValueError:
            print("That's not a valid number. Please try again.")
    step_title, insert_step_num = get_user_input(steps_dict, step_title_input, step_number_input)
    renaming_plan = plan_renaming(steps_dict, insert_step_num)

    # Calculate the file operations for the renaming plan
    file_operations = calculate_renaming_operations(renaming_plan)
    # Execute the file operations
    for operation in file_operations:
        if operation[0] == 'makedirs':
            os.makedirs(operation[1], exist_ok=True)
        elif operation[0] == 'rename':
            os.rename(operation[1], operation[2])

    # Calculate the file operations for the new step
    new_step_operations = calculate_new_step_file_operations(insert_step_num, step_title)
    # Execute the file operations for the new step
    for operation in new_step_operations:
        if operation[0] == 'makedirs':
            os.makedirs(operation[1], exist_ok=True)
        elif operation[0] == 'write_file':
            with open(operation[1], 'w') as file:
                file.write(operation[2])
        elif operation[0] == 'chmod':
            os.chmod(operation[1], operation[2])

    # Read the current index.json data
    index_file_path = 'index.json'
    with open(index_file_path, 'r') as index_file:
        current_index_data = json.load(index_file)

    # Calculate the updates to the index.json data
    updated_index_data = calculate_index_json_updates(steps_dict, insert_step_num, step_title, current_index_data)

    # Write the updated index.json data back to the file
    with open(index_file_path, 'w') as index_file:
        json.dump(updated_index_data, index_file, ensure_ascii=False, indent=4)
    new_tree_structure = get_tree_structure()
    # Print out the new file structure for confirmation
    tree_diff = generate_diff(old_tree_structure, new_tree_structure)
    print("\nFile structure changes:")
    print(tree_diff, end="")

if __name__ == "__main__":
    main()
