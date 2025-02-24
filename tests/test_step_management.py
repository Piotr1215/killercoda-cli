#!/usr/bin/env python3
import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import json
from killercoda_cli.step_management import (
    get_current_steps_dict, get_user_input, plan_renaming,
    calculate_renaming_operations, calculate_new_step_file_operations,
    calculate_index_json_updates
)
from killercoda_cli.file_operations import FileOperation

class TestStepManagement(unittest.TestCase):
    def test_get_current_steps_dict_empty(self):
        """Test get_current_steps_dict with empty directory"""
        self.assertEqual(get_current_steps_dict([]), {})
    
    @patch('os.path.isdir')
    def test_get_current_steps_dict_mixed_items(self, mock_isdir):
        """Test get_current_steps_dict with mixed items"""
        mock_isdir.side_effect = lambda path: path in ["step1", "step10"]
        directory_items = ["step1", "step2.md", "not_a_step.txt", "stepX", "step10"]
        result = get_current_steps_dict(directory_items)
        expected = {1: "step1", 2: "step2.md", 10: "step10"}
        self.assertEqual(result, expected)
    
    def test_get_user_input_valid(self):
        """Test get_user_input with valid inputs"""
        steps_dict = {1: "step1", 2: "step2"}
        step_title, step_number = get_user_input(steps_dict, "New Step", "2")
        self.assertEqual(step_title, "New Step")
        self.assertEqual(step_number, 2)
    
    def test_get_user_input_invalid(self):
        """Test get_user_input with invalid step number"""
        steps_dict = {1: "step1", 2: "step2"}
        with self.assertRaises(ValueError):
            get_user_input(steps_dict, "New Step", "4")
    
    def test_plan_renaming_empty(self):
        """Test plan_renaming with empty steps dict"""
        self.assertEqual(plan_renaming({}, 1), [])
    
    def test_plan_renaming_insert_at_beginning(self):
        """Test plan_renaming when inserting at beginning"""
        steps_dict = {1: "step1", 2: "step2", 3: "step3.md"}
        result = plan_renaming(steps_dict, 1)
        expected = [("step3.md", "step4"), ("step2", "step3"), ("step1", "step2")]
        self.assertEqual(result, expected)
    
    def test_plan_renaming_insert_in_middle(self):
        """Test plan_renaming when inserting in middle"""
        steps_dict = {1: "step1", 2: "step2", 3: "step3.md"}
        result = plan_renaming(steps_dict, 2)
        expected = [("step3.md", "step4"), ("step2", "step3")]
        self.assertEqual(result, expected)
    
    def test_plan_renaming_insert_at_end(self):
        """Test plan_renaming when inserting at end"""
        steps_dict = {1: "step1", 2: "step2", 3: "step3.md"}
        result = plan_renaming(steps_dict, 4)
        expected = []
        self.assertEqual(result, expected)
    
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_calculate_renaming_operations_directories(self, mock_isfile, mock_isdir):
        """Test calculate_renaming_operations with directory steps"""
        mock_isdir.return_value = True
        mock_isfile.side_effect = lambda path: path.endswith("step1.md") or path.endswith("background.sh")
        
        renaming_plan = [("step1", "step2")]
        operations = calculate_renaming_operations(renaming_plan)
        
        # Check for makedirs and file operations
        self.assertEqual(operations[0].operation, "makedirs")
        self.assertEqual(operations[0].path, "step2")
        
        # Check for rename operations for background.sh and step1.md
        self.assertTrue(any(op.operation == "rename" and op.path == "step1/background.sh" for op in operations))
        self.assertTrue(any(op.operation == "rename" and op.path == "step1/step1.md" for op in operations))
    
    @patch('os.path.isdir')
    def test_calculate_renaming_operations_md_files(self, mock_isdir):
        """Test calculate_renaming_operations with .md files"""
        mock_isdir.return_value = False
        
        renaming_plan = [("step1.md", "step2")]
        operations = calculate_renaming_operations(renaming_plan)
        
        # Should have a rename operation for the .md file
        self.assertEqual(len(operations), 2)  # makedirs + rename
        self.assertEqual(operations[1].operation, "rename")
        self.assertEqual(operations[1].path, "step1.md")
        self.assertEqual(operations[1].content, "step2.md")
    
    def test_calculate_new_step_file_operations_regular(self):
        """Test calculate_new_step_file_operations for regular step"""
        operations = calculate_new_step_file_operations(3, "Test Step", "r")
        
        # Check for expected operations (6 operations total)
        # mkdir, md file, bg script, fg script, chmod bg, chmod fg
        self.assertEqual(len(operations), 6)
        
        # Check file paths
        paths = [op.path for op in operations]
        self.assertIn("step3", paths)
        self.assertIn("step3/step3.md", paths)
        self.assertIn("step3/background.sh", paths)
        self.assertIn("step3/foreground.sh", paths)
        
        # Check file contents
        md_op = next(op for op in operations if op.path == "step3/step3.md")
        self.assertEqual(md_op.content, "# Test Step\n")
    
    def test_calculate_new_step_file_operations_verify(self):
        """Test calculate_new_step_file_operations for verify step"""
        operations = calculate_new_step_file_operations(3, "Test Step", "v")
        
        # Check for expected operations (4 operations total)
        # mkdir, md file, verify script, chmod verify
        self.assertEqual(len(operations), 4)
        
        # Check file paths
        paths = [op.path for op in operations]
        self.assertIn("step3", paths)
        self.assertIn("step3/step3.md", paths)
        self.assertIn("step3/verify.sh", paths)
        
        # Verify no background/foreground scripts
        self.assertNotIn("step3/background.sh", paths)
        self.assertNotIn("step3/foreground.sh", paths)
    
    def test_calculate_index_json_updates_regular(self):
        """Test calculate_index_json_updates for regular step"""
        current_data = {
            "details": {
                "steps": [
                    {"title": "Step 1", "text": "step1/step1.md", "background": "step1/background.sh"},
                    {"title": "Step 2", "text": "step2/step2.md", "background": "step2/background.sh"}
                ]
            }
        }
        
        updated_data = calculate_index_json_updates(2, "New Step", current_data, "r")
        
        # Check number of steps increased
        self.assertEqual(len(updated_data["details"]["steps"]), 3)
        
        # Check new step was inserted at position 2
        new_step = updated_data["details"]["steps"][1]
        self.assertEqual(new_step["title"], "New Step")
        self.assertEqual(new_step["text"], "step2/step2.md")
        self.assertEqual(new_step["background"], "step2/background.sh")
        
        # Check original step 2 was moved to position 3
        moved_step = updated_data["details"]["steps"][2]
        self.assertEqual(moved_step["title"], "Step 2")
        self.assertEqual(moved_step["text"], "step3/step3.md")
        self.assertEqual(moved_step["background"], "step3/background.sh")
    
    def test_calculate_index_json_updates_verify(self):
        """Test calculate_index_json_updates for verify step"""
        current_data = {
            "details": {
                "steps": [
                    {"title": "Step 1", "text": "step1/step1.md", "background": "step1/background.sh"},
                    {"title": "Step 2", "text": "step2/step2.md", "verify": "step2/verify.sh"}
                ]
            }
        }
        
        updated_data = calculate_index_json_updates(2, "New Step", current_data, "v")
        
        # Check new step has verify field instead of background
        new_step = updated_data["details"]["steps"][1]
        self.assertEqual(new_step["title"], "New Step")
        self.assertEqual(new_step["text"], "step2/step2.md")
        self.assertEqual(new_step["verify"], "step2/verify.sh")
        self.assertNotIn("background", new_step)

if __name__ == "__main__":
    unittest.main()