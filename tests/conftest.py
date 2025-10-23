"""
Pytest configuration and fixtures for promptval tests.

This module provides common fixtures and configuration for all test modules.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for prompt validation")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_prompt_text():
    """Sample prompt text for testing."""
    return "Write a function to calculate the area of a circle given its radius."


@pytest.fixture
def sample_prompt_with_pii():
    """Sample prompt text containing PII for testing."""
    return "Contact me at test@example.com or call 555-123-4567 for more information."


@pytest.fixture
def sample_prompt_with_redundancy():
    """Sample prompt text with redundant content for testing."""
    return "Write a function to calculate area. Write a function to calculate area."


@pytest.fixture
def sample_prompt_with_conflict():
    """Sample prompt text with conflicting instructions for testing."""
    return "Write a function that is both fast and slow, and also write a function that is both fast and slow."


@pytest.fixture
def sample_prompt_incomplete():
    """Sample prompt text that is incomplete for testing."""
    return "Write a function to"


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "issues": [
            {
                "type": "redundancy",
                "severity": "warning",
                "message": "Redundant content detected",
                "suggestion": "Remove duplicate text"
            }
        ],
        "fixed_text": "Write a function to calculate the area of a circle given its radius.",
        "score": 85
    }


@pytest.fixture
def mock_llm_response_with_pii():
    """Mock LLM response with PII issues for testing."""
    return {
        "issues": [
            {
                "type": "pii",
                "severity": "error",
                "message": "PII detected: email address",
                "suggestion": "Remove or redact the email address"
            }
        ],
        "fixed_text": "Contact me at [REDACTED] for more information.",
        "score": 60
    }


@pytest.fixture
def mock_llm_response_multiple_issues():
    """Mock LLM response with multiple issues for testing."""
    return {
        "issues": [
            {
                "type": "redundancy",
                "severity": "warning",
                "message": "Redundant content detected",
                "suggestion": "Remove duplicate text"
            },
            {
                "type": "conflict",
                "severity": "error",
                "message": "Conflicting instructions detected",
                "suggestion": "Clarify the requirements"
            },
            {
                "type": "completeness",
                "severity": "info",
                "message": "Missing edge cases",
                "suggestion": "Add examples for edge cases"
            }
        ],
        "fixed_text": "Write a clear, non-redundant function to calculate the area of a circle given its radius. Include edge cases for invalid inputs.",
        "score": 70
    }


@pytest.fixture
def mock_llm_response_no_issues():
    """Mock LLM response with no issues for testing."""
    return {
        "issues": [],
        "fixed_text": "Write a function to calculate the area of a circle given its radius.",
        "score": 100
    }


@pytest.fixture
def mock_llm_response_failure():
    """Mock LLM response that simulates a failure for testing."""
    return {
        "issues": [],
        "fixed_text": None,
        "score": None
    }


@pytest.fixture
def clean_environment():
    """Clean environment variables for testing."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def openai_environment():
    """Environment with OpenAI API key for testing."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-key-1234567890abcdef",
        "PROMPTVAL_PROVIDER": "openai",
        "PROMPTVAL_MODEL": "gpt-3.5-turbo"
    }):
        yield


@pytest.fixture
def anthropic_environment():
    """Environment with Anthropic API key for testing."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "sk-ant-test-key-1234567890abcdef",
        "PROMPTVAL_PROVIDER": "anthropic",
        "PROMPTVAL_MODEL": "claude-3-haiku-20240307"
    }):
        yield


@pytest.fixture
def google_environment():
    """Environment with Google API key for testing."""
    with patch.dict(os.environ, {
        "GOOGLE_API_KEY": "AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI",
        "PROMPTVAL_PROVIDER": "gemini",
        "PROMPTVAL_MODEL": "gemini-pro"
    }):
        yield


@pytest.fixture
def xai_environment():
    """Environment with X.ai API key for testing."""
    with patch.dict(os.environ, {
        "XAI_API_KEY": "xai-test-key-1234567890abcdef",
        "PROMPTVAL_PROVIDER": "xai",
        "PROMPTVAL_MODEL": "grok-beta"
    }):
        yield


@pytest.fixture
def openai_compatible_environment():
    """Environment with OpenAI-compatible provider for testing."""
    with patch.dict(os.environ, {
        "PROMPTVAL_PROVIDER": "openai_compatible",
        "PROMPTVAL_MODEL": "gpt-3.5-turbo",
        "PROMPTVAL_BASE_URL": "https://api.example.com/v1"
    }):
        yield


@pytest.fixture
def debug_environment():
    """Environment with debug mode enabled for testing."""
    with patch.dict(os.environ, {
        "PROMPTVAL_DEBUG": "true"
    }):
        yield


@pytest.fixture
def test_files_directory(temp_directory):
    """Create a directory with test files for testing."""
    test_files = [
        "valid_prompt.txt",
        "prompt_with_pii.txt",
        "redundant_prompt.txt",
        "conflicting_prompt.txt",
        "incomplete_prompt.txt"
    ]
    
    test_contents = [
        "Write a function to calculate the area of a circle.",
        "Contact me at test@example.com for more information.",
        "Write a function to calculate area. Write a function to calculate area.",
        "Write a function that is both fast and slow.",
        "Write a function to"
    ]
    
    for filename, content in zip(test_files, test_contents):
        file_path = Path(temp_directory) / filename
        file_path.write_text(content)
    
    return temp_directory


@pytest.fixture
def sample_validation_result():
    """Sample ValidationResult for testing."""
    from promptval.models import ValidationResult, Issue, IssueType, Severity, TextSpan
    
    issue = Issue(
        file_path="test.txt",
        issue_type=IssueType.pii,
        severity=Severity.error,
        message="PII detected: email address",
        suggestion="Remove or redact the email address",
        span=TextSpan(start=10, end=25)
    )
    
    return ValidationResult(
        file_path="test.txt",
        issues=[issue]
    )


@pytest.fixture
def sample_fix_operation():
    """Sample FixOperation for testing."""
    from promptval.models import FixOperation, FixOperationType, TextSpan
    
    return FixOperation(
        op=FixOperationType.replace,
        span=TextSpan(start=10, end=25),
        content="[REDACTED]"
    )


@pytest.fixture
def sample_fix_proposal():
    """Sample FixProposal for testing."""
    from promptval.models import FixProposal, FixOperation, FixOperationType, TextSpan
    
    operation = FixOperation(
        op=FixOperationType.replace,
        span=TextSpan(start=10, end=25),
        content="[REDACTED]"
    )
    
    return FixProposal(
        file_path="test.txt",
        operations=[operation],
        description="Replace PII with redacted text"
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM API access"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add llm marker to tests that require LLM access
        if "llm" in item.name.lower() or "llm_fix" in item.nodeid:
            item.add_marker(pytest.mark.llm)
        
        # Add slow marker to tests that might be slow
        if "integration" in item.name.lower() or "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # Add integration marker to integration tests
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
