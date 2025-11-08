#!/usr/bin/env python3

"""
File operations module for killercoda-cli.
Defines classes and functions for file system operations.
"""

import difflib
import os
import subprocess
import urllib.parse
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
            content: File content for write operations, or destination path for rename
            mode: Permission mode for chmod operations

        Raises:
            ValueError: If path contains security vulnerabilities
        """
        # Validate path security BEFORE storing
        self._validate_path_security(path)

        # For rename operations, also validate destination path (stored in content)
        if operation == "rename" and content:
            self._validate_path_security(content)

        self.operation = operation
        self.path = path
        self.content = content
        self.mode = mode

    @staticmethod
    def _validate_path_security(path: str) -> None:
        """
        Validate path for security vulnerabilities.

        Checks for:
        - Path traversal attacks (..)
        - Absolute paths (/)
        - Null bytes
        - Invalid characters

        Args:
            path: Path to validate

        Raises:
            ValueError: If path contains security vulnerabilities
        """
        if not path:
            raise ValueError("Path cannot be empty")

        # Check for null bytes
        if '\x00' in path:
            raise ValueError(f"Path contains null byte: {path}")

        # Check for newlines and other control characters
        if '\n' in path or '\r' in path:
            raise ValueError(f"Path contains invalid character: {path}")

        # Decode URL-encoded characters to detect hidden path traversal
        decoded_path = urllib.parse.unquote(path)

        # Check for absolute paths
        if os.path.isabs(decoded_path):
            raise ValueError(f"Absolute path not allowed: {path}")

        # Check for path traversal
        if '..' in decoded_path:
            raise ValueError(f"Path traversal not allowed: {path}")

        # Normalize path and verify it doesn't escape current directory
        try:
            normalized = os.path.normpath(decoded_path)
            if normalized.startswith('..') or os.path.isabs(normalized):
                raise ValueError(f"Path traversal not allowed: {path}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid path: {path}") from e

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

    Raises:
        ValueError: If any path escapes the current working directory
    """
    current_dir = os.path.realpath(os.getcwd())

    for operation in file_operations:
        # Verify resolved path stays within current directory
        # Use realpath to follow symlinks
        try:
            resolved_path = os.path.realpath(operation.path)
        except (OSError, ValueError):
            # If path doesn't exist yet or is invalid, use abspath
            resolved_path = os.path.abspath(operation.path)

        if not resolved_path.startswith(current_dir + os.sep) and resolved_path != current_dir:
            raise ValueError(
                f"Path {operation.path} resolves outside working directory: {resolved_path}"
            )

        # For rename, also check destination
        if operation.operation == "rename" and operation.content:
            try:
                resolved_dest = os.path.realpath(operation.content)
            except (OSError, ValueError):
                resolved_dest = os.path.abspath(operation.content)

            if not resolved_dest.startswith(current_dir + os.sep) and resolved_dest != current_dir:
                raise ValueError(
                    f"Rename destination {operation.content} resolves outside working directory: {resolved_dest}"
                )

        # Execute the operation
        if operation.operation == "makedirs":
            os.makedirs(operation.path, exist_ok=True)
        elif operation.operation == "write_file":
            with open(operation.path, "w") as file:
                file.write(operation.content)
        elif operation.operation == "chmod":
            os.chmod(operation.path, operation.mode)
        elif operation.operation == "rename":
            os.rename(operation.path, operation.content)
