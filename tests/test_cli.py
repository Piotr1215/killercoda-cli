#!/usr/bin/env python3
import unittest
from unittest import TestCase, mock
from unittest.mock import patch, MagicMock
from killercoda_cli.cli import FileOperation
from killercoda_cli import cli


class TestCLI(unittest.TestCase):
    def test_get_tree_structure(self):
        # Mock the subprocess.run to return a predefined tree output
        mock_output = """.
        ├── step1
        │   ├── background.sh
        │   └── step1.md
        └── step2
            ├── background.sh
            └── step2.md
        """
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = mock_output.encode("utf-8")
            tree_structure = cli.get_tree_structure()
            expected_output = mock_output
            assert (
                tree_structure == expected_output
            ), "The tree structure output was not as expected."

    def test_generate_diff(self):
        old_tree = "old\nstructure\n"
        new_tree = "new\nstructure\n"
        expected_diff = "Expected diff output"
        with patch("difflib.unified_diff", return_value=expected_diff) as mock_diff:
            diff = cli.generate_diff(old_tree, new_tree)
            mock_diff.assert_called_once()
            assert (
                diff == expected_diff
            ), "The generated diff output was not as expected."

    def test_get_current_steps_dict(self):
        directory_items = ["step1", "step2", "step3.md", "not_a_step", "stepX"]
        expected_dict = cli.get_current_steps_dict(directory_items)
        steps_dict = cli.get_current_steps_dict(directory_items)
        assert (
            steps_dict == expected_dict
        ), "The steps dictionary did not match the expected output."

    @mock.patch("os.path.isdir", return_value=True)
    def test_get_current_steps_dict_ignores_invalid(self, mock_isdir):
        directory_items = ["step1", "stepnotanumber.md", "step2"]
        expected = {1: "step1", 2: "step2"}
        result = cli.get_current_steps_dict(directory_items)
        self.assertEqual(result, expected)

    def test_get_user_input(self):
        steps_dict = {1: "step1", 2: "step2", 3: "step3.md"}
        step_title_input = "New Step Title"
        step_number_input = "4"
        expected_output = (step_title_input, int(step_number_input))
        user_input = cli.get_user_input(steps_dict, step_title_input, step_number_input)
        assert (
            user_input == expected_output
        ), "The user input did not match the expected output."

    def test_plan_renaming(self):
        steps_dict = {1: "step1", 2: "step2", 3: "step3.md"}
        insert_step_num = 2
        expected_plan = [("step3.md", "step4"), ("step2", "step3")]
        renaming_plan = cli.plan_renaming(steps_dict, insert_step_num)
        assert (
            renaming_plan == expected_plan
        ), "The renaming plan did not match the expected output."

    def test_calculate_renaming_operations_with_verify(self):
        renaming_plan = [("step2", "step3"), ("step1", "step2")]
        expected_operations = [
            FileOperation("makedirs", "step3"),
            FileOperation("rename", "step2/background.sh", "step3/background.sh"),
            FileOperation("rename", "step2/foreground.sh", "step3/foreground.sh"),
            FileOperation("rename", "step2/verify.sh", "step3/verify.sh"),
            FileOperation("rename", "step2/step2.md", "step3/step3.md"),
            FileOperation("makedirs", "step2"),
            FileOperation("rename", "step1/background.sh", "step2/background.sh"),
            FileOperation("rename", "step1/foreground.sh", "step2/foreground.sh"),
            FileOperation("rename", "step1/verify.sh", "step2/verify.sh"),
            FileOperation("rename", "step1/step1.md", "step2/step2.md"),
        ]
        
        # Mock os.path.isdir and os.path.isfile
        with patch("os.path.isdir", return_value=True), patch("os.path.isfile") as mock_isfile:
            # Mock os.path.isfile to return True for specific files
            def isfile_side_effect(path):
                if path in [
                    "step2/background.sh", "step2/foreground.sh", "step2/step2.md", "step2/verify.sh",
                    "step1/background.sh", "step1/foreground.sh", "step1/step1.md", "step1/verify.sh"
                ]:
                    return True
                return False
            mock_isfile.side_effect = isfile_side_effect

            operations = cli.calculate_renaming_operations(renaming_plan)
            assert operations == expected_operations, "The calculated file operations did not match the expected output."
    def test_calculate_renaming_operations(self):
        renaming_plan = [("step2", "step3"), ("step1", "step2")]
        expected_operations = [
            FileOperation("makedirs", "step3"),
            FileOperation("rename", "step2/background.sh", "step3/background.sh"),
            FileOperation("rename", "step2/foreground.sh", "step3/foreground.sh"),
            FileOperation("rename", "step2/step2.md", "step3/step3.md"),
            FileOperation("makedirs", "step2"),
            FileOperation("rename", "step1/background.sh", "step2/background.sh"),
            FileOperation("rename", "step1/foreground.sh", "step2/foreground.sh"),
            FileOperation("rename", "step1/step1.md", "step2/step2.md"),
        ]
        
        # Mock os.path.isdir and os.path.isfile
        with patch("os.path.isdir", return_value=True), patch("os.path.isfile") as mock_isfile:
            # Mock os.path.isfile to return True for specific files
            def isfile_side_effect(path):
                if path in [
                    "step2/background.sh", "step2/foreground.sh", "step2/step2.md",
                    "step1/background.sh", "step1/foreground.sh", "step1/step1.md"
                ]:
                    return True
                return False
            mock_isfile.side_effect = isfile_side_effect

            operations = cli.calculate_renaming_operations(renaming_plan)
            assert operations == expected_operations, "The calculated file operations did not match the expected output."

    def test_calculate_new_step_file_operations(self):
        insert_step_num = 4
        step_title = "New Step"
        step_type = "regular"  # Assuming "regular" is a valid step type. Adjust as necessary.
        expected_operations = [
            FileOperation("makedirs", "step4"),
            FileOperation("write_file", "step4/step4.md", content="# New Step\n"),
            FileOperation(
                "write_file",
                "step4/background.sh",
                content='#!/bin/sh\necho "New Step script"\n',
            ),
            FileOperation(
                "write_file",
                "step4/foreground.sh",
                content='#!/bin/sh\necho "New Step script"\n',
            ),
            FileOperation("chmod", "step4/background.sh", mode=0o755),
            FileOperation("chmod", "step4/foreground.sh", mode=0o755),
        ]
        operations = cli.calculate_new_step_file_operations(insert_step_num, step_title, step_type)
        #  # printe the operations
        #  for op in operations:
        #  print("Printing operations to better compare results")
        #  content = f"'{op.content}'" if op.content is not None else "None"
        #  mode = f"{op.mode}" if op.mode is not None else "None"
        #  print(op.operation, op.path, content, mode)

        assert (
            operations == expected_operations
        ), "The new step file operations did not match the expected output."

    def test_calculate_index_json_updates_for_verify(self):
        insert_step_num = 2
        step_title = "New Step"
        step_type = "verify"
        current_index_data = {
            "details": {
                "steps": [
                    {
                        "title": "Step 1",
                        "text": "step1/step1.md",
                        "background": "step1/background.sh",
                    },
                    {
                        "title": "Step 2",
                        "text": "step2/step2.md",
                        "background": "step2/background.sh",
                    },
                ]
            }
        }
        expected_data = {
            "details": {
                "steps": [
                    {
                        "title": "Step 1",
                        "text": "step1/step1.md",
                        "background": "step1/background.sh",
                    },
                    {
                        "title": "New Step",
                        "text": "step2/step2.md",
                        "verify": "step2/verify.sh",
                    },
                    {
                        "title": "Step 2",
                        "text": "step3/step3.md",
                        "background": "step3/background.sh",
                    },
                ]
            }
        }
        updated_data = cli.calculate_index_json_updates(
            insert_step_num, step_title, current_index_data, step_type
        )
        assert (
            updated_data == expected_data
        ), "The updated index.json data did not match the expected output."

    def test_calculate_index_json_updates(self):
        insert_step_num = 2
        step_title = "New Step"
        step_type = "regular"
        current_index_data = {
            "details": {
                "steps": [
                    {
                        "title": "Step 1",
                        "text": "step1/step1.md",
                        "background": "step1/background.sh",
                    },
                    {
                        "title": "Step 2",
                        "text": "step2/step2.md",
                        "background": "step2/background.sh",
                    },
                ]
            }
        }
        expected_data = {
            "details": {
                "steps": [
                    {
                        "title": "Step 1",
                        "text": "step1/step1.md",
                        "background": "step1/background.sh",
                    },
                    {
                        "title": "New Step",
                        "text": "step2/step2.md",
                        "background": "step2/background.sh",
                    },
                    {
                        "title": "Step 2",
                        "text": "step3/step3.md",
                        "background": "step3/background.sh",
                    },
                ]
            }
        }
        updated_data = cli.calculate_index_json_updates(
            insert_step_num, step_title, current_index_data, step_type
        )
        assert (
            updated_data == expected_data
        ), "The updated index.json data did not match the expected output."


if __name__ == "__main__":
    unittest.main()
