from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from promptval.cli import app


runner = CliRunner()


def test_cli_prompt_text_success():
    """Test CLI prompt command with text input."""
    with patch('promptval.rules.core.ProviderFactory.from_env') as mock_factory:
        mock_provider = MagicMock()
        mock_provider.evaluate_prompt.return_value = {
            "issues": [{"type": "redundancy", "severity": "info", "message": "Test issue"}],
            "fixed_text": "Task:\n  Test prompt\n\nSuccess Criteria:\n  - Clear output",
            "score": 95.0
        }
        mock_factory.return_value = mock_provider
        mock_analyze.return_value = {
            "fixed_prompt": "Task:\n  Test prompt\n\nSuccess Criteria:\n  - Clear output",
            "issues": [{"type": "redundancy", "severity": "info", "message": "Test issue"}],
            "score": 95,
            "provider": {"name": "openai", "model": "gpt-4o-mini"}
        }
        
        result = runner.invoke(app, [
            "prompt", 
            "--text", "Test prompt",
            "--provider", "openai",
            "--model", "gpt-4o-mini"
        ])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["fixed_prompt"].startswith("Task:")
        assert output["score"] == 95
        assert len(output["issues"]) == 1


def test_cli_prompt_file_success():
    """Test CLI prompt command with file input."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test prompt from file")
        temp_file = f.name
    
    try:
        with patch('promptval.api.analyze_prompt') as mock_analyze:
            mock_analyze.return_value = {
                "fixed_prompt": "Task:\n  Test prompt from file\n\nSuccess Criteria:\n  - Clear output",
                "issues": [],
                "score": 100,
                "provider": {"name": "openai", "model": "gpt-4o-mini"}
            }
            
            result = runner.invoke(app, [
                "prompt",
                "--file", temp_file,
                "--provider", "openai"
            ])
            
            assert result.exit_code == 0
            output = json.loads(result.stdout)
            assert "Test prompt from file" in output["fixed_prompt"]
            assert output["score"] == 100
    finally:
        os.unlink(temp_file)


def test_cli_prompt_missing_input():
    """Test CLI prompt command with no input specified."""
    result = runner.invoke(app, ["prompt", "--provider", "openai"])
    
    assert result.exit_code == 2
    assert "Provide --text or --file" in result.stdout


def test_cli_prompt_nonexistent_file():
    """Test CLI prompt command with non-existent file."""
    result = runner.invoke(app, [
        "prompt",
        "--file", "/nonexistent/file.txt",
        "--provider", "openai"
    ])
    
    assert result.exit_code == 2
    assert "File not found" in result.stdout


def test_cli_prompt_with_all_options():
    """Test CLI prompt command with all available options."""
    with patch('promptval.api.analyze_prompt') as mock_analyze:
        mock_analyze.return_value = {
            "fixed_prompt": "Test",
            "issues": [],
            "score": 100,
            "provider": {"name": "openai", "model": "gpt-4o-mini"}
        }
        
        result = runner.invoke(app, [
            "prompt",
            "--text", "Test prompt",
            "--provider", "anthropic",
            "--model", "claude-3-sonnet",
            "--base-url", "https://api.anthropic.com",
            "--timeout", "120.0",
            "--temperature", "0.7"
        ])
        
        assert result.exit_code == 0
        # Verify the analyze_prompt was called with correct config
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        assert call_args[0][0] == "Test prompt"  # text
        config = call_args[0][1]  # config
        assert config.provider == "anthropic"
        assert config.model == "claude-3-sonnet"
        assert config.base_url == "https://api.anthropic.com"
        assert config.timeout == 120.0
        assert config.temperature == 0.7


def test_cli_prompt_environment_override():
    """Test CLI prompt command respects environment variables."""
    with patch.dict(os.environ, {
        "PROMPTVAL_PROVIDER": "gemini",
        "PROMPTVAL_MODEL": "gemini-1.5-pro",
        "PROMPTVAL_TEMPERATURE": "0.5"
    }):
        with patch('promptval.api.analyze_prompt') as mock_analyze:
            mock_analyze.return_value = {
                "fixed_prompt": "Test",
                "issues": [],
                "score": 100,
                "provider": {"name": "gemini", "model": "gemini-1.5-pro"}
            }
            
            result = runner.invoke(app, ["prompt", "--text", "Test prompt"])
            
            assert result.exit_code == 0
            # Verify environment variables were used
            mock_analyze.assert_called_once()
            config = mock_analyze.call_args[0][1]
            assert config.provider == "gemini"
            assert config.model == "gemini-1.5-pro"
            assert config.temperature == 0.5


def test_cli_prompt_json_output_format():
    """Test CLI prompt command outputs valid JSON."""
    with patch('promptval.api.analyze_prompt') as mock_analyze:
        mock_analyze.return_value = {
            "fixed_prompt": "Task:\n  Test\n\nSuccess Criteria:\n  - Clear",
            "issues": [
                {
                    "type": "redundancy",
                    "severity": "warning",
                    "message": "Redundant text",
                    "suggestion": "Remove redundancy",
                    "span": [0, 10]
                }
            ],
            "score": 90,
            "provider": {
                "name": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "timeout": 30.0,
                "base_url_set": False
            }
        }
        
        result = runner.invoke(app, ["prompt", "--text", "Test prompt"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        
        # Verify JSON structure
        assert "fixed_prompt" in output
        assert "issues" in output
        assert "score" in output
        assert "provider" in output
        
        # Verify issue structure
        issue = output["issues"][0]
        assert "type" in issue
        assert "severity" in issue
        assert "message" in issue
        assert "suggestion" in issue
        assert "span" in issue
        
        # Verify provider structure
        provider = output["provider"]
        assert "name" in provider
        assert "model" in provider
        assert "temperature" in provider
        assert "timeout" in provider
        assert "base_url_set" in provider


def test_cli_prompt_error_handling():
    """Test CLI prompt command handles errors gracefully."""
    with patch('promptval.api.analyze_prompt') as mock_analyze:
        mock_analyze.side_effect = Exception("API Error")
        
        result = runner.invoke(app, ["prompt", "--text", "Test prompt"])
        
        # Should still exit with 0 but show error in output
        assert result.exit_code == 0
        # The error should be handled by the offline fallback
        output = json.loads(result.stdout)
        assert "fixed_prompt" in output
        assert "score" in output


def test_cli_scan_command_still_works():
    """Test that existing scan command still works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test prompt content")
        
        with patch('promptval.api.validate_directory') as mock_validate:
            from promptval.models import ValidationResult, Issue, IssueType, Severity
            mock_validate.return_value = [
                ValidationResult(
                    file_path=str(test_file),
                    issues=[
                        Issue(
                            file_path=str(test_file),
                            issue_type=IssueType.redundancy,
                            severity=Severity.warning,
                            message="Test issue"
                        )
                    ]
                )
            ]
            
            result = runner.invoke(app, ["scan", temp_dir])
            
            assert result.exit_code == 1  # Has issues
            assert "Test issue" in result.stdout


def test_cli_validate_command_still_works():
    """Test that existing validate command still works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test prompt content")
        
        with patch('promptval.api.validate_directory') as mock_validate:
            from promptval.models import ValidationResult
            mock_validate.return_value = [
                ValidationResult(file_path=str(test_file), issues=[])
            ]
            
            result = runner.invoke(app, ["validate", temp_dir])
            
            assert result.exit_code == 0
            assert "PromptVal Report" in result.stdout
