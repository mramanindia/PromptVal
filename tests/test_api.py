"""
Test cases for main API functions.

This module tests the core API functions like analyze_prompt, validate_file, and validate_directory.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from promptval.api import (
    analyze_prompt, 
    validate_file, 
    validate_directory, 
    apply_fixes,
    PromptValConfig,
    _compute_score
)
from promptval.models import ValidationResult, Issue, IssueType, Severity


class TestPromptValAPI:
    """Test main API functions."""

    def test_analyze_prompt_basic(self):
        """Test basic analyze_prompt functionality."""
        text = "Write a function to calculate the area of a circle"
        
        # This will use offline fallback if no API keys are available
        result = analyze_prompt(text)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check types
        assert isinstance(result["fixed_prompt"], str)
        assert isinstance(result["issues"], list)
        assert isinstance(result["score"], int)
        assert isinstance(result["provider"], dict)
        
        # Check score range
        assert 0 <= result["score"] <= 100

    def test_analyze_prompt_with_config(self):
        """Test analyze_prompt with configuration."""
        text = "Create a user authentication system"
        config = PromptValConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
            timeout=30.0
        )
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check provider metadata
        provider_meta = result["provider"]
        assert "name" in provider_meta
        assert "model" in provider_meta
        assert "temperature" in provider_meta
        assert "timeout" in provider_meta
        assert "base_url_set" in provider_meta

    def test_analyze_prompt_without_config(self):
        """Test analyze_prompt without configuration (uses defaults)."""
        text = "Write a sorting algorithm"
        
        result = analyze_prompt(text)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result

    def test_validate_file_basic(self):
        """Test validate_file with a simple text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Write a function to calculate the area of a circle")
            temp_path = f.name
        
        try:
            result = validate_file(temp_path)
            
            assert isinstance(result, ValidationResult)
            assert result.file_path == temp_path
            assert isinstance(result.issues, list)
        finally:
            os.unlink(temp_path)

    def test_validate_file_nonexistent(self):
        """Test validate_file with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            validate_file("nonexistent_file.txt")

    def test_validate_file_with_llm_disabled(self):
        """Test validate_file with LLM disabled."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Write a function to calculate the area of a circle")
            temp_path = f.name
        
        try:
            result = validate_file(temp_path, use_llm=False)
            
            assert isinstance(result, ValidationResult)
            assert result.file_path == temp_path
            assert isinstance(result.issues, list)
        finally:
            os.unlink(temp_path)

    def test_validate_directory_basic(self):
        """Test validate_directory with a directory containing text files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = Path(temp_dir) / "test1.txt"
            file2 = Path(temp_dir) / "test2.txt"
            file3 = Path(temp_dir) / "not_txt.py"  # Should be ignored
            
            file1.write_text("Write a function to calculate area")
            file2.write_text("Create a user authentication system")
            file3.write_text("print('hello')")
            
            results = validate_directory(temp_dir)
            
            assert isinstance(results, list)
            assert len(results) == 2  # Only .txt files
            
            for result in results:
                assert isinstance(result, ValidationResult)
                assert result.file_path.endswith('.txt')
                assert isinstance(result.issues, list)

    def test_validate_directory_nonexistent(self):
        """Test validate_directory with nonexistent directory."""
        with pytest.raises(FileNotFoundError):
            validate_directory("nonexistent_directory")

    def test_validate_directory_empty(self):
        """Test validate_directory with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            results = validate_directory(temp_dir)
            
            assert isinstance(results, list)
            assert len(results) == 0

    def test_validate_directory_recursive(self):
        """Test that validate_directory searches recursively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            subdir = Path(temp_dir) / "subdir"
            subdir.mkdir()
            
            # Create files in root and subdirectory
            file1 = Path(temp_dir) / "root.txt"
            file2 = subdir / "sub.txt"
            
            file1.write_text("Root file content")
            file2.write_text("Subdirectory file content")
            
            results = validate_directory(temp_dir)
            
            assert len(results) == 2
            file_paths = [result.file_path for result in results]
            assert any("root.txt" in path for path in file_paths)
            assert any("sub.txt" in path for path in file_paths)

    def test_apply_fixes_basic(self):
        """Test apply_fixes with basic validation results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Write a function to calculate area")
            
            # Create validation result
            result = ValidationResult(
                file_path=str(test_file),
                issues=[]
            )
            
            # Apply fixes
            apply_fixes([result], out_dir="corrected")
            
            # Check that corrected file was created
            corrected_file = Path("corrected") / "test.txt"
            assert corrected_file.exists()
            assert corrected_file.read_text() != test_file.read_text()  # Should be different (fixed)

    def test_apply_fixes_in_place(self):
        """Test apply_fixes with in-place modification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            original_content = "Write a function to calculate area"
            test_file.write_text(original_content)
            
            # Create validation result
            result = ValidationResult(
                file_path=str(test_file),
                issues=[]
            )
            
            # Apply fixes in place
            apply_fixes([result], out_dir=None)
            
            # Check that file was modified
            modified_content = test_file.read_text()
            assert modified_content != original_content  # Should be different (fixed)

    def test_apply_fixes_with_custom_out_dir(self):
        """Test apply_fixes with custom output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Write a function to calculate area")
            
            # Create validation result
            result = ValidationResult(
                file_path=str(test_file),
                issues=[]
            )
            
            # Apply fixes to custom directory
            custom_dir = Path(temp_dir) / "custom_output"
            apply_fixes([result], out_dir=str(custom_dir))
            
            # Check that corrected file was created in custom directory
            corrected_file = custom_dir / "test.txt"
            assert corrected_file.exists()

    def test_prompt_val_config_creation(self):
        """Test PromptValConfig creation and properties."""
        config = PromptValConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            base_url="https://api.openai.com/v1",
            timeout=30.0,
            temperature=0.7
        )
        
        assert config.provider == "openai"
        assert config.model == "gpt-3.5-turbo"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.timeout == 30.0
        assert config.temperature == 0.7

    def test_prompt_val_config_defaults(self):
        """Test PromptValConfig with default values."""
        config = PromptValConfig()
        
        assert config.provider is None
        assert config.model is None
        assert config.base_url is None
        assert config.timeout is None
        assert config.temperature is None

    def test_prompt_val_config_partial(self):
        """Test PromptValConfig with partial values."""
        config = PromptValConfig(provider="anthropic", model="claude-3-haiku")
        
        assert config.provider == "anthropic"
        assert config.model == "claude-3-haiku"
        assert config.base_url is None
        assert config.timeout is None
        assert config.temperature is None

    def test_analyze_prompt_environment_override(self):
        """Test that environment variables override config parameters."""
        text = "Write a test function"
        
        with patch.dict(os.environ, {
            "PROMPTVAL_PROVIDER": "openai",
            "PROMPTVAL_MODEL": "gpt-4",
            "PROMPTVAL_TEMPERATURE": "0.5"
        }):
            config = PromptValConfig(provider="anthropic")  # Should be overridden
            
            result = analyze_prompt(text, config)
            
            # Should use environment values
            assert result["provider"]["name"] == "openai"
            assert result["provider"]["model"] == "gpt-4"
            assert result["provider"]["temperature"] == 0.5

    def test_analyze_prompt_config_override_environment(self):
        """Test that config parameters override environment variables."""
        text = "Write a test function"
        
        with patch.dict(os.environ, {
            "PROMPTVAL_PROVIDER": "openai",
            "PROMPTVAL_MODEL": "gpt-3.5-turbo"
        }):
            config = PromptValConfig(provider="anthropic", model="claude-3-haiku")
            
            result = analyze_prompt(text, config)
            
            # Should use config values, not environment
            assert result["provider"]["name"] == "anthropic"
            assert result["provider"]["model"] == "claude-3-haiku"

    def test_analyze_prompt_fallback_behavior(self):
        """Test analyze_prompt fallback behavior when LLM fails."""
        text = "Write a simple function"
        
        # This should work even without API keys (uses offline fallback)
        result = analyze_prompt(text)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Should have structured output from offline fallback
        assert "Task:" in result["fixed_prompt"] or "Success Criteria:" in result["fixed_prompt"]

    def test_validate_file_encoding_handling(self):
        """Test validate_file with different text encodings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Write a function to calculate the area of a circle")
            temp_path = f.name
        
        try:
            result = validate_file(temp_path)
            
            assert isinstance(result, ValidationResult)
            assert result.file_path == temp_path
        finally:
            os.unlink(temp_path)

    def test_validate_directory_file_filtering(self):
        """Test that validate_directory only processes .txt files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various file types
            files = [
                "test.txt",
                "test.py",
                "test.md",
                "test.json",
                "test.yaml",
                "test.TXT",  # Should be included (case insensitive)
            ]
            
            for filename in files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(f"Content for {filename}")
            
            results = validate_directory(temp_dir)
            
            # Should only process .txt files
            assert len(results) == 2  # test.txt and test.TXT
            file_paths = [result.file_path for result in results]
            assert any("test.txt" in path for path in file_paths)
            assert any("test.TXT" in path for path in file_paths)

    def test_apply_fixes_multiple_files(self):
        """Test apply_fixes with multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            files = ["test1.txt", "test2.txt", "test3.txt"]
            results = []
            
            for filename in files:
                file_path = Path(temp_dir) / filename
                file_path.write_text(f"Content for {filename}")
                
                result = ValidationResult(file_path=str(file_path), issues=[])
                results.append(result)
            
            # Apply fixes
            apply_fixes(results, out_dir="corrected")
            
            # Check that all corrected files were created
            for filename in files:
                corrected_file = Path("corrected") / filename
                assert corrected_file.exists()

    def test_apply_fixes_empty_results(self):
        """Test apply_fixes with empty results list."""
        # Should not raise an exception
        apply_fixes([], out_dir="corrected")
        
        # Directory should not be created if no files
        assert not Path("corrected").exists()

    def test_analyze_prompt_provider_metadata(self):
        """Test that provider metadata is correctly populated."""
        text = "Write a test"
        
        result = analyze_prompt(text)
        
        provider_meta = result["provider"]
        required_keys = ["name", "model", "temperature", "timeout", "base_url_set"]
        
        for key in required_keys:
            assert key in provider_meta
        
        # Check that values are appropriate types
        assert isinstance(provider_meta["name"], str)
        assert provider_meta["model"] is None or isinstance(provider_meta["model"], str)
        assert provider_meta["temperature"] is None or isinstance(provider_meta["temperature"], float)
        assert provider_meta["timeout"] is None or isinstance(provider_meta["timeout"], float)
        assert isinstance(provider_meta["base_url_set"], bool)

    def test_analyze_prompt_score_fallback(self):
        """Test that score calculation falls back to heuristic when provider fails."""
        text = "Write a function"
        
        result = analyze_prompt(text)
        
        # Should always have a valid score
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_analyze_prompt_issues_structure(self):
        """Test that issues are properly structured."""
        text = "Write a function to calculate area"
        
        result = analyze_prompt(text)
        
        assert isinstance(result["issues"], list)
        
        # If there are issues, they should have proper structure
        for issue in result["issues"]:
            assert isinstance(issue, dict)
            # Issues should have type, severity, message, etc.
            if "type" in issue or "issue_type" in issue:
                assert "severity" in issue
                assert "message" in issue

    def test_analyze_prompt_fixed_prompt_structure(self):
        """Test that fixed_prompt is properly structured."""
        text = "Write a function to calculate area"
        
        result = analyze_prompt(text)
        
        fixed_prompt = result["fixed_prompt"]
        assert isinstance(fixed_prompt, str)
        assert len(fixed_prompt) > 0
        
        # Should be structured (either from LLM or offline fallback)
        structured_indicators = [
            "Task:", "Success Criteria:", "Examples:", 
            "Think step by step", "No Secrets / No PII:"
        ]
        
        has_structure = any(indicator in fixed_prompt for indicator in structured_indicators)
        assert has_structure, f"Fixed prompt should be structured: {fixed_prompt[:200]}..."