from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from promptval.cli import app


runner = CliRunner()


@patch('promptval.api.analyze_prompt')
def test_cli_prompt_text_success(mock_analyze):
    """Test CLI prompt command with text input."""
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


@patch('promptval.api.analyze_prompt')
def test_cli_prompt_file_success(mock_analyze):
    """Test CLI prompt command with file input."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test prompt from file")
        temp_file = f.name
    
    try:
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


@patch('promptval.api.analyze_prompt')
def test_cli_prompt_with_all_options(mock_analyze):
    """Test CLI prompt command with all available options."""
    mock_analyze.return_value = {
        "fixed_prompt": "Test",
        "issues": [],
        "score": 100,
        "provider": {"name": "openai", "model": "gpt-4o-mini"}
    }
    
    result = runner.invoke(app, [
        "prompt",
        "--text", "Test prompt",
        "--provider", "openai",
        "--model", "gpt-4o-mini",
        "--base-url", "https://api.openai.com/v1",
        "--timeout", "120.0",
        "--temperature", "0.7"
    ])
    
    assert result.exit_code == 0
    # Verify the analyze_prompt was called with correct config
    mock_analyze.assert_called_once()
    call_args = mock_analyze.call_args
    assert call_args[0][0] == "Test prompt"  # text
    config = call_args[0][1]  # config
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.base_url == "https://api.openai.com/v1"
    assert config.timeout == 120.0
    assert config.temperature == 0.7


@patch('promptval.api.analyze_prompt')
def test_cli_prompt_json_output_format(mock_analyze):
    """Test CLI prompt command outputs valid JSON."""
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
