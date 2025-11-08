# Testing Improvements for killercoda-cli

**Current Status:**
- ✅ 58 tests passing
- ✅ 85% code coverage
- ⚠️ Gap Analysis: Coverage (85%) > Quality (needs assessment)

## FIRST Principles Assessment

### Current Compliance

✅ **Fast** - Tests run in <1 second
✅ **Isolated** - Good use of temp directories and mocks
✅ **Repeatable** - No flaky tests observed
✅ **Self-Checking** - All tests use proper assertions
⚠️ **Timely** - Some tests could benefit from data-driven patterns

## Critical Improvements Needed

### 1. Behavior Testing vs Existence Testing

**Problem Found:** Some tests check that output exists, not what it contains.

**Example - Weak Test Pattern:**
```python
# ❌ WEAK: Only checks that error message exists
self.assertIn("Missing step file", message)
```

**Recommended - Strong Test Pattern:**
```python
# ✅ STRONG: Verify exact error details
self.assertFalse(is_valid)
self.assertIn("Missing step file: step1/step1.md", message)
self.assertEqual(result.missing_files, ["step1/step1.md"])
```

### 2. Property-Based Testing Opportunities

**Add property-based tests for step renaming logic:**

```python
# Suggested addition to test_step_management.py
from hypothesis import given, strategies as st

class TestStepManagementProperties(unittest.TestCase):
    @given(st.integers(min_value=1, max_value=100))
    def test_property_step_numbers_sequential(self, insert_position):
        """PROPERTY: After insertion, all steps are sequential with no gaps"""
        steps_dict = {i: f"step{i}" for i in range(1, 10)}

        renamed = plan_renaming(steps_dict, insert_position)
        # Apply renames
        new_dict = apply_renames(steps_dict, renamed)

        # Verify sequential: 1, 2, 3, ..., N with no gaps
        step_numbers = sorted(new_dict.keys())
        for i, num in enumerate(step_numbers, 1):
            self.assertEqual(num, i, f"Gap detected at position {i}")
```

### 3. Security Testing Gaps

**Current:** No security tests found
**Recommended:** Add path traversal and injection protection tests

```python
# Suggested addition to test_file_operations.py
class TestFileOperationsSecurity(unittest.TestCase):
    def test_security_rejects_path_traversal_dotdot(self):
        """SECURITY: Reject path traversal with .."""
        with self.assertRaises(ValueError) as cm:
            FileOperation("write_file", "../etc/passwd", content="hack")
        self.assertIn("path traversal", str(cm.exception).lower())

    def test_security_rejects_absolute_paths(self):
        """SECURITY: Reject absolute paths"""
        with self.assertRaises(ValueError) as cm:
            FileOperation("write_file", "/etc/passwd", content="hack")
        self.assertIn("absolute path", str(cm.exception).lower())

    def test_security_handles_null_bytes(self):
        """SECURITY: Handle null bytes in file names"""
        with self.assertRaises(ValueError) as cm:
            FileOperation("write_file", "test\x00.md", content="data")
        self.assertIn("invalid character", str(cm.exception).lower())
```

### 4. Mutation Testing Setup

**Recommended:** Add mutation testing to identify weak tests

**Installation:**
```bash
pip install mutmut
```

**Configuration (.mutmut-config.py):**
```python
def pre_mutation(context):
    # Skip test files
    if 'test_' in context.filename:
        context.skip = True
```

**Run mutation tests:**
```bash
# Run mutation testing
mutmut run --paths-to-mutate=killercoda_cli/

# Show results
mutmut results

# View survivors (mutations that didn't fail tests)
mutmut show
```

**Expected survivors to investigate:**
- Magic numbers in scoring logic
- String formatting details
- Error message exact text
- Log output formatting

### 5. Test Coverage Improvements

**Low Coverage Areas (from tester agent):**

**cli.py (60% coverage)** - Interactive mode untested
```python
# Suggested addition to test_cli.py
class TestCLIInteractiveMode(unittest.TestCase):
    @patch('builtins.input', side_effect=['New Step', '2', 'r'])
    @patch('killercoda_cli.cli.get_tree_structure')
    def test_interactive_mode_creates_regular_step(self, mock_tree, mock_input):
        """Test full interactive workflow for regular step"""
        # Setup
        os.chdir(self.test_dir)

        # Execute
        cli.main()

        # Verify step was created
        self.assertTrue(os.path.exists('step2'))
        self.assertTrue(os.path.exists('step2/step2.md'))
        self.assertTrue(os.path.exists('step2/background.sh'))
        self.assertTrue(os.path.exists('step2/foreground.sh'))
```

**assets.py (77% coverage)** - Error handling untested
```python
# Suggested addition to test_assets.py
class TestAssetsErrorHandling(unittest.TestCase):
    @patch('killercoda_cli.assets.cookiecutter')
    def test_handles_cookiecutter_failure(self, mock_cookiecutter):
        """Test graceful handling when cookiecutter fails"""
        mock_cookiecutter.side_effect = Exception('Network error')

        with self.assertRaises(RuntimeError) as cm:
            generate_assets()

        self.assertIn('Failed to generate assets', str(cm.exception))
        self.assertIn('Network error', str(cm.exception))
```

**validation.py (79% coverage)** - Edge cases untested
```python
# Suggested addition to test_validation.py
class TestValidationEdgeCases(unittest.TestCase):
    def test_validates_very_large_index_json(self):
        """Test validation with 100+ steps"""
        steps = [
            {"title": f"Step {i}", "text": f"step{i}/step{i}.md"}
            for i in range(1, 101)
        ]
        index_data = {"details": {"steps": steps}}

        # Create all step files
        for i in range(1, 101):
            os.makedirs(f"step{i}", exist_ok=True)
            with open(f"step{i}/step{i}.md", 'w') as f:
                f.write(f"# Step {i}\n")

        is_valid, message = validate_course(self.course_dir)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Valid")

    def test_validates_unicode_in_step_titles(self):
        """QUIRK: Unicode characters in step titles"""
        index_data = {
            "details": {
                "steps": [{"title": "测试 🔥", "text": "step1/step1.md"}]
            }
        }
        # ... test unicode handling
```

### 6. Data-Driven Test Patterns

**Current:** Individual tests for each case
**Recommended:** Parameterized tests for similar scenarios

```python
# Suggested refactor of test_validation.py
import pytest

class TestValidationDataDriven:
    @pytest.mark.parametrize("missing_file,expected_error", [
        ("step1/step1.md", "Missing step file: step1/step1.md"),
        ("step1/background.sh", "Missing background script: step1/background.sh"),
        ("step1/foreground.sh", "Missing foreground script: step1/foreground.sh"),
        ("intro.md", "Missing intro.md"),
        ("finish.md", "Missing finish.md"),
    ])
    def test_validates_missing_files(self, missing_file, expected_error):
        """Data-driven test for missing file validation"""
        # Setup valid course
        self.create_valid_course()

        # Remove specific file
        os.remove(os.path.join(self.course_dir, missing_file))

        # Validate
        is_valid, message = validate_course(self.course_dir)

        # Assert
        self.assertFalse(is_valid)
        self.assertIn(expected_error, message)
```

### 7. TDD Workflow for New Features

**Recommended process for future features:**

1. **RED** - Write failing test first
```python
def test_new_feature_validates_templates(self):
    """New feature: Validate step templates"""
    # This test will fail - feature doesn't exist yet
    is_valid = validate_templates(self.course_dir)
    self.assertTrue(is_valid)
```

2. **GREEN** - Minimal implementation
```python
def validate_templates(course_dir):
    # Simplest possible implementation
    return True
```

3. **REFACTOR** - Improve while keeping tests green
```python
def validate_templates(course_dir):
    templates = find_templates(course_dir)
    return all(is_valid_template(t) for t in templates)
```

4. **REPEAT** - Next test

## Test Quality Metrics

**Recommended Targets:**

- **Code Coverage:** 85-90% (currently 85% ✅)
- **Mutation Score:** 70%+ (needs setup)
- **Test Speed:** <2s for full suite (currently ~0.8s ✅)
- **Test Count:** ~70 tests (currently 58)

## Implementation Priority

### High Priority (This Week)
1. ✅ Add security tests (path traversal, injections)
2. ✅ Setup mutation testing (mutmut)
3. ✅ Add property-based tests for step renaming

### Medium Priority (This Month)
4. Improve CLI interactive mode coverage (60% → 80%)
5. Add assets.py error handling tests (77% → 90%)
6. Refactor to data-driven test patterns

### Low Priority (Nice to Have)
7. Add performance tests for large scenarios (100+ steps)
8. Add integration tests with real cookiecutter templates
9. Document test quirks with QUIRK: prefix pattern

## Mutation Testing Deep Dive

### Expected Mutation Survivors

Based on the codebase analysis, expect these survivors:

**1. String Formatting Details**
```python
# Original
f"Step {i}"
# Mutant (survived)
f"Step {i + 1}"
# Why: Tests don't verify exact step titles
```

**2. Default Values**
```python
# Original
priority = priority or "M"
# Mutant (survived)
priority = priority or "H"
# Why: Tests don't check default priority
```

**3. Error Messages**
```python
# Original
raise ValueError("Invalid step number")
# Mutant (survived)
raise ValueError("Invalid input")
# Why: Tests use assertRaises without checking message
```

### Mutation Testing Workflow

```bash
# 1. Run mutation tests
mutmut run

# 2. Analyze survivors
mutmut show

# 3. For each survivor, decide:
#    a) Weak test → Add assertion
#    b) Code smell → Refactor code
#    c) Cosmetic → Document and accept

# 4. Re-run to verify
mutmut run
```

## Architecture Improvements for Testability

### Pure Functions = Easy Testing

**Current Code:**
```python
# Impure: Hard to test (uses global state)
def process_step():
    directory = os.getcwd()  # Global state
    files = os.listdir(directory)  # I/O
    return parse_steps(files)
```

**Recommended:**
```python
# Pure: Easy to test
def parse_steps(file_list):
    """Pure function - no I/O, no global state"""
    return [f for f in file_list if is_step_file(f)]

# Impure wrapper (thin layer)
def process_step():
    directory = os.getcwd()
    files = os.listdir(directory)
    return parse_steps(files)  # Call pure function
```

**Testing becomes trivial:**
```python
def test_parse_steps_filters_correctly():
    # No mocking needed!
    files = ['step1.md', 'README.md', 'step2', 'config.json']
    result = parse_steps(files)
    self.assertEqual(result, ['step1.md', 'step2'])
```

## Documentation Standards

### QUIRK Pattern for Unexpected Behaviors

```python
def test_quirk_parked_status_uses_backlog_tag(self):
    """QUIRK: Parked status adds +backlog tag, not +hold (line 154)

    DISCOVERED: Original implementation treated "Parked" as low-priority
    backlog item, not "on hold". This differs from other pause states
    like "Blocked" which use +hold tag.
    """
    result = process_status("Parked")
    self.assertIn("backlog", result.tags)
    self.assertNotIn("hold", result.tags)
```

### Mutation Fix Pattern

```python
def test_mutation_fix_verify_exact_step_order(self):
    """MUTATION FIX: Verify step order, not just count

    Catches mutant where step numbers are randomized but count is correct.
    Original test only checked len(steps) == 5.
    """
    steps = plan_renaming(steps_dict, insert_at=3)
    step_numbers = [s[1] for s in steps]

    # Verify exact sequence
    self.assertEqual(step_numbers, [2, 3, 4, 5, 6])
```

## Summary

**Current Strengths:**
- Good coverage (85%)
- Well-organized tests
- Fast test suite

**Key Improvements:**
1. Add security tests (HIGH PRIORITY)
2. Setup mutation testing (HIGH PRIORITY)
3. Add property-based tests (MEDIUM PRIORITY)
4. Improve behavior testing vs existence testing
5. Refactor to data-driven patterns

**Expected Outcomes:**
- Mutation score: 70%+
- Fewer bugs in production
- More confidence in refactoring
- Better documentation through tests
