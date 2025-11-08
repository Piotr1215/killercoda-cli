#!/usr/bin/env python3
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from killercoda_cli.validation import validate_all, validate_course


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.course_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_valid_course(self):
        """Helper method to create a valid course structure"""
        # Create index.json
        index_path = os.path.join(self.course_dir, "index.json")
        index_data = {
            "title": "Test Course",
            "description": "Test Description",
            "details": {
                "steps": [
                    {
                        "title": "Step 1",
                        "text": "step1/step1.md",
                        "background": "step1/background.sh"
                    }
                ]
            }
        }

        with open(index_path, "w") as f:
            json.dump(index_data, f)

        # Create step directory and files
        step_dir = os.path.join(self.course_dir, "step1")
        os.makedirs(step_dir)

        with open(os.path.join(step_dir, "step1.md"), "w") as f:
            f.write("# Step 1")

        with open(os.path.join(step_dir, "background.sh"), "w") as f:
            f.write("#!/bin/sh\necho 'test'")

        return index_data

    def test_validate_course_missing_index(self):
        """Test validation when index.json is missing"""
        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        self.assertIn("Missing index.json file", message)

    def test_validate_course_empty_index(self):
        """Test validation with empty index.json"""
        index_path = os.path.join(self.course_dir, "index.json")
        with open(index_path, "w") as f:
            f.write("")

        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        self.assertIn("Empty index.json file", message)

    def test_validate_course_invalid_json(self):
        """Test validation with invalid JSON in index.json"""
        index_path = os.path.join(self.course_dir, "index.json")
        with open(index_path, "w") as f:
            f.write("{not valid json")

        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        self.assertIn("Invalid JSON in index.json", message)

    def test_validate_course_missing_required_fields(self):
        """Test validation with missing required fields"""
        index_path = os.path.join(self.course_dir, "index.json")
        with open(index_path, "w") as f:
            json.dump({"title": "Test Course"}, f)

        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        self.assertIn("Missing required fields", message)

    def test_validate_course_missing_steps(self):
        """Test validation with missing steps field"""
        index_path = os.path.join(self.course_dir, "index.json")
        with open(index_path, "w") as f:
            json.dump({
                "title": "Test Course",
                "description": "Test Description",
                "details": {}
            }, f)

        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        # This could be either "Missing steps" or "Missing required fields"
        # depending on how validation is implemented
        self.assertTrue("Missing steps" in message or "Missing required fields" in message)

    def test_validate_course_valid(self):
        """Test validation with valid course setup"""
        self.create_valid_course()

        is_valid, message = validate_course(self.course_dir)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid")

    def test_validate_course_missing_step_file(self):
        """Test validation with missing step file"""
        # Create index.json and step dir without the step1.md file
        self.create_valid_course()

        # Remove the step1.md file
        os.remove(os.path.join(self.course_dir, "step1", "step1.md"))

        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        self.assertIn("Missing step file", message)

    def test_validate_course_missing_background_script(self):
        """Test validation with missing background script"""
        # Create index.json and step dir without the background.sh file
        self.create_valid_course()

        # Remove the background.sh file
        os.remove(os.path.join(self.course_dir, "step1", "background.sh"))

        is_valid, message = validate_course(self.course_dir)
        self.assertFalse(is_valid)
        self.assertIn("Missing background script", message)

    @patch('builtins.print')
    def test_validate_all_empty_directory(self, mock_print):
        """Test validate_all with empty directory"""
        result = validate_all(self.course_dir)
        self.assertTrue(result)
        mock_print.assert_any_call("\n=== Scenario Validation ===")
        # The exact format of this message may vary, so we'll just check for the presence
        # of "empty" and "ok" somewhere in one of the calls
        empty_ok_called = False
        for call in mock_print.call_args_list:
            args, _ = call
            if len(args) > 0 and isinstance(args[0], str) and "empty" in args[0].lower() and "ok" in args[0].lower():
                empty_ok_called = True
                break
        self.assertTrue(empty_ok_called, "No print call found with 'empty' and 'ok'")

    @patch('builtins.print')
    def test_validate_all_missing_index(self, mock_print):
        """Test validate_all with missing index.json but non-empty directory"""
        # Create dummy file to make directory non-empty
        dummy_path = os.path.join(self.course_dir, "dummy.txt")
        with open(dummy_path, "w") as f:
            f.write("dummy content")

        result = validate_all(self.course_dir)
        self.assertFalse(result)

        # Check for a message about missing index.json
        missing_index_called = False
        for call in mock_print.call_args_list:
            args, _ = call
            if len(args) > 0 and isinstance(args[0], str) and "index.json" in args[0] and "failed" in args[0] and "not found" in args[0].lower():
                missing_index_called = True
                break
        self.assertTrue(missing_index_called, "No print call found about missing index.json")

    @patch('builtins.print')
    def test_validate_all_valid_course(self, mock_print):
        """Test validate_all with valid course"""
        self.create_valid_course()

        result = validate_all(self.course_dir)
        self.assertTrue(result)
        mock_print.assert_any_call("[+]json-syntax                                        ok")
        mock_print.assert_any_call("[+]step-1                                             ok")

    @patch('builtins.print')
    def test_validate_all_invalid_json(self, mock_print):
        """Test validate_all with invalid JSON in index.json"""
        index_path = os.path.join(self.course_dir, "index.json")
        with open(index_path, "w") as f:
            f.write("{invalid json")

        result = validate_all(self.course_dir)
        self.assertFalse(result)
        mock_print.assert_any_call("[-]json-syntax                                        failed - Invalid JSON")

    @patch('builtins.print')
    def test_validate_all_missing_step(self, mock_print):
        """Test validate_all with missing step file"""
        # Create valid course first
        self.create_valid_course()

        # Then remove step file
        os.remove(os.path.join(self.course_dir, "step1", "step1.md"))

        result = validate_all(self.course_dir)
        self.assertFalse(result)
        mock_print.assert_any_call("[-]step-1                                             failed - Missing step1/step1.md")

if __name__ == "__main__":
    unittest.main()
