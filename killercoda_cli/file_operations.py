#!/usr/bin/env python3

"""
File operations module for killercoda-cli.
Defines classes and functions for file system operations.
"""

import difflib
import os
import subprocess
from typing import Optional


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


def _tree_fallback(directory=".", prefix=""):
    """
    Python-based directory tree generator (fallback when 'tree' is not available).

    Args:
        directory: Directory to display tree for
        prefix: Prefix for the current line (used for recursion)

    Returns:
        str: Directory tree as formatted string
    """
    import os
    output = []
    try:
        entries = sorted(os.listdir(directory))
    except PermissionError:
        return f"{prefix}[Permission Denied]\n"

    # Filter out hidden files/dirs and common ignore patterns
    entries = [e for e in entries if not e.startswith('.') and e not in ['__pycache__', 'node_modules']]

    for i, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "

        if os.path.isdir(path):
            output.append(f"{prefix}{connector}{entry}/\n")
            extension = "    " if is_last else "│   "
            output.append(_tree_fallback(path, prefix + extension))
        else:
            output.append(f"{prefix}{connector}{entry}\n")

    return "".join(output)


def get_tree_structure():
    """
    Get directory structure using 'tree' command (with Python fallback).

    Returns:
        str: Directory tree as formatted string
    """
    try:
        result = subprocess.run(
            ["tree"],
            capture_output=True,
            check=False,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback to Python implementation
    cwd = os.getcwd()
    tree_output = f"{os.path.basename(cwd) or cwd}/\n"
    tree_output += _tree_fallback()
    return tree_output


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
