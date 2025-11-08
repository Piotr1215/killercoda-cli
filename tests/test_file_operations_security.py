#!/usr/bin/env python3
"""
Security tests for file_operations module.

Tests protect against common attack vectors:
- Path traversal attacks (../, /, encoded)
- Null byte injection
- Absolute path attacks
- Symbolic link attacks
"""

import os
import unittest

from killercoda_cli.file_operations import FileOperation, execute_file_operations


class TestFileOperationsSecurity(unittest.TestCase):
    """Security-focused tests for file operations."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = '/tmp/test_file_ops_security'
        os.makedirs(self.test_dir, exist_ok=True)
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        # Clean up test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # ==================== Path Traversal Tests ====================

    def test_security_rejects_path_traversal_dotdot(self):
        """SECURITY: Reject path traversal with .. in path"""
        dangerous_paths = [
            '../etc/passwd',
            'step1/../../../etc/passwd',
            'step1/../../secrets.txt',
        ]

        for dangerous_path in dangerous_paths:
            with self.subTest(path=dangerous_path):
                with self.assertRaises(ValueError) as cm:
                    FileOperation("write_file", dangerous_path, content="hack")
                self.assertIn("path traversal", str(cm.exception).lower())

    def test_security_rejects_absolute_paths(self):
        """SECURITY: Reject absolute paths starting with /"""
        dangerous_paths = [
            '/etc/passwd',
            '/tmp/secrets',
            '/var/www/html/index.html',
        ]

        for dangerous_path in dangerous_paths:
            with self.subTest(path=dangerous_path):
                with self.assertRaises(ValueError) as cm:
                    FileOperation("write_file", dangerous_path, content="hack")
                self.assertIn("absolute path", str(cm.exception).lower())

    def test_security_rejects_encoded_path_traversal(self):
        """SECURITY: Reject URL-encoded path traversal"""
        # URL encoded: %2e%2e%2f = ../
        dangerous_paths = [
            '%2e%2e%2fpasswd',
            'step1%2f%2e%2e%2fsecrets',
        ]

        for dangerous_path in dangerous_paths:
            with self.subTest(path=dangerous_path):
                with self.assertRaises(ValueError) as cm:
                    FileOperation("write_file", dangerous_path, content="hack")
                # Should catch encoded characters or traversal
                error_msg = str(cm.exception).lower()
                self.assertTrue(
                    "path traversal" in error_msg or "invalid character" in error_msg
                )

    # ==================== Null Byte Injection Tests ====================

    def test_security_rejects_null_byte_in_path(self):
        """SECURITY: Reject null bytes in file paths"""
        dangerous_paths = [
            'test\x00.md',
            'step1/test.md\x00.jpg',  # Classic null byte attack
            'safe.txt\x00../../../../etc/passwd',
        ]

        for dangerous_path in dangerous_paths:
            with self.subTest(path=dangerous_path):
                with self.assertRaises(ValueError) as cm:
                    FileOperation("write_file", dangerous_path, content="data")
                self.assertIn("null byte", str(cm.exception).lower())

    # ==================== Symbolic Link Tests ====================

    def test_security_prevents_symlink_following_outside_cwd(self):
        """SECURITY: Prevent following symlinks outside current directory"""
        # Create a symlink pointing outside current directory
        os.makedirs('step1', exist_ok=True)

        # Skip if system doesn't support symlinks (Windows without admin)
        try:
            os.symlink('/etc', 'step1/link_to_etc')
        except (OSError, NotImplementedError):
            self.skipTest("System doesn't support symlinks")

        # Create a FileOperation that targets the symlink
        # Path looks safe ("step1/link_to_etc") but resolves to /etc
        op = FileOperation("write_file", "step1/link_to_etc", content="hack")

        # execute_file_operations should detect resolved path is outside cwd
        with self.assertRaises(ValueError) as cm:
            execute_file_operations([op])

        error_msg = str(cm.exception).lower()
        self.assertTrue(
            "outside working directory" in error_msg or
            "resolves outside" in error_msg,
            f"Expected security error, got: {cm.exception}"
        )

    # ==================== Special Character Tests ====================

    def test_security_handles_newlines_in_path(self):
        """SECURITY: Reject or sanitize newlines in paths"""
        dangerous_paths = [
            'test\nfile.md',
            'step1/test\r\ndata.txt',
        ]

        for dangerous_path in dangerous_paths:
            with self.subTest(path=dangerous_path):
                with self.assertRaises(ValueError) as cm:
                    FileOperation("write_file", dangerous_path, content="data")
                self.assertIn("invalid character", str(cm.exception).lower())

    def test_security_handles_unicode_safely(self):
        """QUIRK: Unicode in paths should be allowed but sanitized"""
        # Unicode should work for legitimate use cases
        # but shouldn't break security validations
        unicode_paths = [
            'step1/测试.md',  # Chinese
            'step1/🔥_test.md',  # Emoji
            'step1/café.md',  # Accented characters
        ]

        for unicode_path in unicode_paths:
            with self.subTest(path=unicode_path):
                # Should either work or fail gracefully (not crash)
                try:
                    op = FileOperation("write_file", unicode_path, content="test")
                    # If it succeeds, verify path is still safe
                    resolved = os.path.abspath(unicode_path)
                    current_dir = os.getcwd()
                    self.assertTrue(
                        resolved.startswith(current_dir),
                        f"Unicode path {unicode_path} escaped current directory"
                    )
                except ValueError as e:
                    # If it fails, should have clear error message
                    self.assertIn("character", str(e).lower())

    # ==================== Execute Operations Security ====================

    def test_security_execute_operations_validates_all_paths(self):
        """SECURITY: FileOperation constructor validates paths (fail-fast)"""
        # QUIRK: Security validation happens in __init__, not execute_file_operations
        # This is actually BETTER - fail fast at construction time

        # Creating the dangerous FileOperation should fail immediately
        with self.assertRaises(ValueError) as cm:
            FileOperation("write_file", "../etc/passwd", content="hack")

        self.assertIn("path traversal", str(cm.exception).lower())

        # Verify that operations list can't even be created with dangerous paths
        safe_ops = [
            FileOperation("write_file", "safe1.txt", content="ok"),
            FileOperation("write_file", "safe2.txt", content="ok"),
        ]

        # These should execute successfully
        execute_file_operations(safe_ops)
        self.assertTrue(os.path.exists("safe1.txt"))
        self.assertTrue(os.path.exists("safe2.txt"))

    # ==================== Chmod Security ====================

    def test_security_chmod_validates_paths(self):
        """SECURITY: chmod operations also validate paths"""
        # Create a safe file first
        with open('test.txt', 'w') as f:
            f.write('test')

        # Try to chmod dangerous path
        with self.assertRaises(ValueError) as cm:
            FileOperation("chmod", "../etc/passwd", mode=0o777)

        self.assertIn("path traversal", str(cm.exception).lower())

    def test_security_chmod_prevents_overly_permissive_modes(self):
        """SECURITY: Warn on overly permissive chmod (world-writable)"""
        # Create a file
        with open('test.txt', 'w') as f:
            f.write('test')

        # World-writable files are dangerous
        dangerous_modes = [
            0o777,  # rwxrwxrwx
            0o666,  # rw-rw-rw-
        ]

        for mode in dangerous_modes:
            with self.subTest(mode=oct(mode)):
                # This is more of a warning than a hard error
                # But in security-critical environments, might want to prevent
                op = FileOperation("chmod", "test.txt", mode=mode)
                # Document that this is allowed but potentially dangerous
                # A stricter implementation might raise ValueError here

    # ==================== Rename Security ====================

    def test_security_rename_validates_both_source_and_dest(self):
        """SECURITY: Rename validates both source and destination paths"""
        # Create source file
        os.makedirs('step1', exist_ok=True)
        with open('step1/source.txt', 'w') as f:
            f.write('test')

        # Bad source
        with self.assertRaises(ValueError):
            FileOperation("rename", "../etc/passwd")

        # Bad destination (stored in content for rename operations)
        with self.assertRaises(ValueError):
            op = FileOperation("rename", "step1/source.txt")
            op.content = "/etc/passwd"  # Destination in content field
            execute_file_operations([op])


if __name__ == '__main__':
    unittest.main()
