#!/usr/bin/env python3

"""
Step management module for killercoda-cli.
Provides functionality for managing scenario steps, including renaming, addition, and planning.
"""

import os
import json
from typing import List, Dict, Tuple, Any
from killercoda_cli.file_operations import FileOperation


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


# TODO:(piotr1215) replace os calls with data structure
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