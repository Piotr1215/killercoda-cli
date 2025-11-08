#!/usr/bin/env python3

"""
Validation module for killercoda-cli.
Provides functions for validating scenario structure and content.
"""

import json
import os


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

    Args:
        base_path: Path to validate

    Returns:
        bool: True if valid, False otherwise
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
            print("\nValidation Status: PASSED")
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
