#!/usr/bin/env python3
"""
Property-based tests for step management using Hypothesis.

These tests verify invariants and properties that should hold true
for all valid inputs, not just specific examples.
"""

import unittest
from hypothesis import given, strategies as st, assume

from killercoda_cli.step_management import (
    get_current_steps_dict,
    plan_renaming,
)


class TestStepManagementProperties(unittest.TestCase):
    """Property-based tests for step management functions."""

    @given(st.integers(min_value=1, max_value=11))
    def test_property_step_numbers_sequential_after_insertion(self, insert_position):
        """
        PROPERTY: After planning renaming for insertion, all step numbers remain sequential.

        When we insert a step at any position, the renaming plan should ensure
        that all existing steps are renumbered sequentially with no gaps.
        """
        # Create a valid steps dict with sequential numbers 1-10
        steps_dict = {i: f"step{i}" for i in range(1, 11)}

        # Generate renaming plan
        renaming_plan = plan_renaming(steps_dict, insert_position)

        # Apply renames to verify final state
        result_dict = steps_dict.copy()
        for old_name, new_name in renaming_plan:
            # Extract step numbers from names
            old_num = int(old_name.replace("step", ""))
            new_num = int(new_name.replace("step", ""))
            # Remove old entry and add new one
            del result_dict[old_num]
            result_dict[new_num] = new_name

        # Add the new step that would be inserted
        result_dict[insert_position] = f"step{insert_position}"

        # Verify all step numbers are sequential with no gaps
        step_numbers = sorted(result_dict.keys())
        for i, num in enumerate(step_numbers, 1):
            self.assertEqual(
                num,
                i,
                f"Gap detected at position {i}: expected {i}, got {num}. "
                f"Insert position: {insert_position}, Numbers: {step_numbers}"
            )

    @given(st.integers(min_value=1, max_value=50))
    def test_property_renaming_plan_preserves_order(self, insert_position):
        """
        PROPERTY: Renaming plan preserves relative order of existing steps.

        When inserting at position N, steps N and onwards are shifted by 1,
        but their relative order remains the same.
        """
        steps_dict = {i: f"step{i}" for i in range(1, 21)}
        assume(1 <= insert_position <= 21)

        renaming_plan = plan_renaming(steps_dict, insert_position)

        # Extract all renamed step numbers
        renamed_old = []
        renamed_new = []
        for old_name, new_name in renaming_plan:
            old_num = int(old_name.replace("step", ""))
            new_num = int(new_name.replace("step", ""))
            renamed_old.append(old_num)
            renamed_new.append(new_num)

        # Verify renaming plan is sorted in reverse order (to avoid conflicts)
        self.assertEqual(renamed_old, sorted(renamed_old, reverse=True))

        # Verify each old number maps to new number = old + 1
        for old_num, new_num in zip(renamed_old, renamed_new):
            self.assertEqual(
                new_num,
                old_num + 1,
                f"Step {old_num} should be renamed to {old_num + 1}, got {new_num}"
            )

    @given(st.integers(min_value=1, max_value=20))
    def test_property_only_steps_at_or_after_insertion_are_renamed(self, insert_position):
        """
        PROPERTY: Only steps at or after insertion position are renamed.

        Steps before the insertion position should not appear in the renaming plan.
        """
        steps_dict = {i: f"step{i}" for i in range(1, 16)}
        assume(1 <= insert_position <= 16)

        renaming_plan = plan_renaming(steps_dict, insert_position)

        # Extract all step numbers that are being renamed
        renamed_step_nums = []
        for old_name, _ in renaming_plan:
            step_num = int(old_name.replace("step", ""))
            renamed_step_nums.append(step_num)

        # Verify all renamed steps are >= insert_position
        for step_num in renamed_step_nums:
            self.assertGreaterEqual(
                step_num,
                insert_position,
                f"Step {step_num} should not be renamed when inserting at {insert_position}"
            )

        # Verify all steps >= insert_position are in the plan
        expected_renames = [i for i in range(insert_position, 16)]
        self.assertEqual(
            sorted(renamed_step_nums),
            sorted(expected_renames),
            f"Missing or extra renames for insertion at {insert_position}"
        )

    @given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=50, unique=True))
    def test_property_handles_non_sequential_step_numbers(self, step_numbers):
        """
        PROPERTY: Renaming works correctly even with non-sequential initial step numbers.

        Users might have steps numbered 1, 3, 5, 7 (gaps). The renaming logic
        should still work correctly.
        """
        # Create steps dict with potentially non-sequential numbers
        steps_dict = {num: f"step{num}" for num in step_numbers}

        # Insert at the beginning
        insert_position = 1

        renaming_plan = plan_renaming(steps_dict, insert_position)

        # All existing steps should be renamed
        self.assertEqual(
            len(renaming_plan),
            len(step_numbers),
            f"All {len(step_numbers)} steps should be renamed when inserting at position 1"
        )

    @given(st.integers(min_value=1, max_value=10))
    def test_property_empty_or_single_step_dict(self, insert_position):
        """
        PROPERTY: Edge case handling for empty or single-step dictionaries.
        """
        # Empty dict - should always produce empty renaming plan
        renaming_plan = plan_renaming({}, insert_position)
        self.assertEqual(renaming_plan, [], "Empty dict should produce empty renaming plan")

        # Single step dict
        steps_dict = {1: "step1"}
        renaming_plan = plan_renaming(steps_dict, insert_position)

        if insert_position == 1:
            # Inserting at position 1 - step 1 needs to move to step 2
            self.assertEqual(len(renaming_plan), 1)
            self.assertEqual(renaming_plan[0], ("step1", "step2"))
        else:
            # Inserting at position 2 or higher - step 1 stays at 1
            self.assertEqual(len(renaming_plan), 0)

    def test_property_renaming_plan_is_conflict_free(self):
        """
        PROPERTY: Renaming plan should be conflict-free when executed in reverse order.

        The renaming plan is returned in reverse order specifically to avoid
        conflicts (e.g., renaming step5 to step6 before step6 to step7).
        This test verifies that the plan can be executed without intermediate conflicts.
        """
        steps_dict = {i: f"step{i}" for i in range(1, 11)}
        insert_position = 5

        renaming_plan = plan_renaming(steps_dict, insert_position)

        # Track which step numbers are "in use" as we apply renames
        active_numbers = set(steps_dict.keys())

        # Apply renames in the order given (reverse order)
        for old_name, new_name in renaming_plan:
            old_num = int(old_name.replace("step", ""))
            new_num = int(new_name.replace("step", ""))

            # Verify old number exists
            self.assertIn(
                old_num,
                active_numbers,
                f"Cannot rename {old_name}: step {old_num} doesn't exist"
            )

            # Verify new number is free (no conflict)
            self.assertNotIn(
                new_num,
                active_numbers,
                f"Conflict: Cannot rename {old_name} to {new_name}, "
                f"step {new_num} already exists"
            )

            # Apply the rename
            active_numbers.remove(old_num)
            active_numbers.add(new_num)

        # After all renames, we should have steps at positions insert_position+1 onwards
        # (leaving insert_position free for the new step)
        expected_numbers = set(range(1, insert_position)) | set(range(insert_position + 1, 12))
        self.assertEqual(active_numbers, expected_numbers)

    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=20, unique=True))
    def test_property_get_current_steps_dict_filters_correctly(self, random_items):
        """
        PROPERTY: get_current_steps_dict correctly filters and extracts step numbers.

        Given a list of random directory items, the function should only
        extract items that match the step pattern (stepN or stepN.md).
        """
        # Add some valid step items
        valid_items = ["step1", "step2.md", "step10"]
        all_items = random_items + valid_items

        # Mock os.path.isdir to return True for non-.md items
        import os
        from unittest.mock import patch

        def mock_isdir(path):
            return not path.endswith('.md') and path.startswith('step')

        with patch('os.path.isdir', side_effect=mock_isdir):
            result = get_current_steps_dict(all_items)

            # All returned keys should be positive integers
            for key in result.keys():
                self.assertIsInstance(key, int)
                self.assertGreater(key, 0)

            # All returned values should start with "step"
            for value in result.values():
                self.assertTrue(
                    value.startswith("step"),
                    f"Value {value} should start with 'step'"
                )

            # Should include our known valid items (if they match the pattern)
            self.assertIn(1, result)
            self.assertIn(2, result)
            self.assertIn(10, result)


if __name__ == '__main__':
    unittest.main()
