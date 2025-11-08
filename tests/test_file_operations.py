#!/usr/bin/env python3
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from killercoda_cli.file_operations import (
    FileOperation,
    execute_file_operations,
    generate_diff,
    get_tree_structure,
)


class TestFileOperations(unittest.TestCase):
    def test_file_operation_repr(self):
        """Test FileOperation __repr__ method"""
        op = FileOperation("makedirs", "test/path", content="test content", mode=0o755)
        repr_string = repr(op)
        self.assertIn("makedirs", repr_string)
        self.assertIn("test/path", repr_string)
        self.assertIn("test content", repr_string)
        self.assertIn("493", repr_string)  # 0o755 in decimal

    def test_file_operation_equality(self):
        """Test FileOperation equality comparison"""
        op1 = FileOperation("makedirs", "test/path", content="test content", mode=0o755)
        op2 = FileOperation("makedirs", "test/path", content="test content", mode=0o755)
        op3 = FileOperation("write_file", "test/path", content="test content", mode=0o755)

        self.assertEqual(op1, op2)
        self.assertNotEqual(op1, op3)
        self.assertNotEqual(op1, "not_an_operation")

    @patch('subprocess.run')
    def test_get_tree_structure(self, mock_run):
        """Test get_tree_structure with mocked subprocess"""
        mock_run.return_value.stdout = b"mock tree output"
        mock_run.return_value.returncode = 0
        result = get_tree_structure()
        mock_run.assert_called_once_with(["tree"], capture_output=True, check=False, timeout=5)
        self.assertEqual(result, "mock tree output")

    def test_generate_diff(self):
        """Test generate_diff with various inputs"""
        old_tree = "line1\nline2\nline3"
        new_tree = "line1\nmodified\nline3"
        diff = generate_diff(old_tree, new_tree)
        self.assertIn("line2", diff)
        self.assertIn("modified", diff)
        self.assertIn("Before changes", diff)
        self.assertIn("After changes", diff)

    def test_execute_file_operations_makedirs(self):
        """Test execute_file_operations with makedirs operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)  # Use relative paths from temp directory
                operations = [FileOperation("makedirs", "test_dir")]

                execute_file_operations(operations)
                self.assertTrue(os.path.isdir("test_dir"))
            finally:
                os.chdir(original_dir)

    def test_execute_file_operations_write_file(self):
        """Test execute_file_operations with write_file operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)  # Use relative paths from temp directory
                test_content = "test content"
                operations = [FileOperation("write_file", "test_file.txt", content=test_content)]

                execute_file_operations(operations)
                with open("test_file.txt") as f:
                    self.assertEqual(f.read(), test_content)
            finally:
                os.chdir(original_dir)

    def test_execute_file_operations_chmod(self):
        """Test execute_file_operations with chmod operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)  # Use relative paths from temp directory
                with open("test_script.sh", 'w') as f:
                    f.write("#!/bin/sh\necho test")

                operations = [FileOperation("chmod", "test_script.sh", mode=0o755)]
                execute_file_operations(operations)

                # Check file permissions (this is platform-dependent)
                self.assertTrue(os.access("test_script.sh", os.X_OK))
            finally:
                os.chdir(original_dir)

    def test_execute_file_operations_rename(self):
        """Test execute_file_operations with rename operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)  # Use relative paths from temp directory
                with open("source.txt", 'w') as f:
                    f.write("test content")

                operations = [FileOperation("rename", "source.txt", content="target.txt")]
                execute_file_operations(operations)

                self.assertFalse(os.path.exists("source.txt"))
                self.assertTrue(os.path.exists("target.txt"))
            finally:
                os.chdir(original_dir)

if __name__ == "__main__":
    unittest.main()
