import os
import json
import pytest
from killercoda_cli.cli import validate_course, validate_all

@pytest.fixture
def temp_course(tmp_path):
    """Create a temporary valid course structure"""
    course_dir = tmp_path / "course-1"
    course_dir.mkdir()
    
    # Create valid index.json
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
    
    # Write index.json
    with open(course_dir / "index.json", "w") as f:
        json.dump(index_data, f)
    
    # Create step directory and files
    step_dir = course_dir / "step1"
    step_dir.mkdir()
    
    (step_dir / "step1.md").write_text("# Step 1")
    (step_dir / "background.sh").write_text("#!/bin/sh\necho 'test'")
    
    return course_dir

def test_validate_course_empty_json(tmp_path):
    course_dir = tmp_path / "empty-json-course"
    course_dir.mkdir()
    (course_dir / "index.json").write_text("")
    
    is_valid, message = validate_course(str(course_dir))
    assert not is_valid
    assert "Empty index.json file" in message

def test_validate_course_valid(temp_course):
    """Test validation of a valid course"""
    is_valid, message = validate_course(str(temp_course))
    assert is_valid
    assert message == "Valid"

def test_validate_course_missing_index(tmp_path):
    """Test validation when index.json is missing"""
    course_dir = tmp_path / "invalid-course"
    course_dir.mkdir()
    
    is_valid, message = validate_course(str(course_dir))
    assert not is_valid
    assert "Missing index.json file" in message

def test_validate_course_invalid_json(tmp_path):
    """Test validation with invalid JSON in index.json"""
    course_dir = tmp_path / "invalid-json-course"
    course_dir.mkdir()
    
    # Create invalid JSON file
    (course_dir / "index.json").write_text("{invalid json")
    
    is_valid, message = validate_course(str(course_dir))
    assert not is_valid
    assert "Invalid JSON in index.json" in message

def test_validate_course_empty_file(tmp_path):
    course_dir = tmp_path / "empty-file-course" 
    course_dir.mkdir()
    
    # Create empty index.json
    (course_dir / "index.json").write_text("")
    
    is_valid, message = validate_course(str(course_dir))
    assert not is_valid
    assert "Empty index.json file" in message

def test_validate_invalid_current_directory(tmp_path):
    """Test validation fails when current directory has invalid index.json"""
    # Create invalid index.json in current directory
    (tmp_path / "index.json").write_text("invalid json")
    
    assert not validate_all(str(tmp_path))

def test_validate_course_missing_required_fields(tmp_path):
    course_dir = tmp_path / "missing-fields-course"
    course_dir.mkdir()
    index_data = {
        "title": "Test Course"
    }
    with open(course_dir / "index.json", "w") as f:
        json.dump(index_data, f)
    
    is_valid, message = validate_course(str(course_dir))
    assert not is_valid
    assert "Missing required fields" in message

def test_validate_course_missing_step_files(temp_course):
    """Test validation when step files are missing"""
    # Remove a required file
    (temp_course / "step1" / "step1.md").unlink()
    
    is_valid, message = validate_course(str(temp_course))
    assert not is_valid
    assert "Missing step file" in message

def test_validate_all(tmp_path):
    """Test validation of multiple courses"""
    # Create two courses - one valid, one invalid
    valid_course = tmp_path / "course-1"
    invalid_course = tmp_path / "course-2"
    
    # Set up valid course
    valid_course.mkdir()
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
    with open(valid_course / "index.json", "w") as f:
        json.dump(index_data, f)
    
    step_dir = valid_course / "step1"
    step_dir.mkdir()
    (step_dir / "step1.md").write_text("# Step 1")
    (step_dir / "background.sh").write_text("#!/bin/sh\necho 'test'")
    
    # Set up invalid course (missing index.json)
    invalid_course.mkdir()
    
    # Run validation
    result = validate_all(str(tmp_path))
    assert not result  # Should be False because one course is invalid

def test_validate_all_empty_directory(tmp_path):
    """Test validation of an empty directory"""
    result = validate_all(str(tmp_path))
    assert result  # Should be True as there are no courses to validate
