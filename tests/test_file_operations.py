#!/usr/bin/env python3
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import tempfile
import subprocess
import shutil
from killercoda_cli.file_operations import FileOperation, get_tree_structure, generate_diff, execute_file_operations

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
        result = get_tree_structure()
        mock_run.assert_called_once_with(["tree"], stdout=subprocess.PIPE)
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
            test_dir = os.path.join(tmpdir, "test_dir")
            operations = [FileOperation("makedirs", test_dir)]
            
            execute_file_operations(operations)
            self.assertTrue(os.path.isdir(test_dir))
    
    def test_execute_file_operations_write_file(self):
        """Test execute_file_operations with write_file operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_file.txt")
            test_content = "test content"
            operations = [FileOperation("write_file", test_file, content=test_content)]
            
            execute_file_operations(operations)
            with open(test_file, 'r') as f:
                self.assertEqual(f.read(), test_content)
    
    def test_execute_file_operations_chmod(self):
        """Test execute_file_operations with chmod operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_script.sh")
            with open(test_file, 'w') as f:
                f.write("#!/bin/sh\necho test")
            
            operations = [FileOperation("chmod", test_file, mode=0o755)]
            execute_file_operations(operations)
            
            # Check file permissions (this is platform-dependent)
            self.assertTrue(os.access(test_file, os.X_OK))
    
    def test_execute_file_operations_rename(self):
        """Test execute_file_operations with rename operation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = os.path.join(tmpdir, "source.txt")
            target_file = os.path.join(tmpdir, "target.txt")
            with open(source_file, 'w') as f:
                f.write("test content")
            
            operations = [FileOperation("rename", source_file, content=target_file)]
            execute_file_operations(operations)
            
            self.assertFalse(os.path.exists(source_file))
            self.assertTrue(os.path.exists(target_file))

if __name__ == "__main__":
    unittest.main()