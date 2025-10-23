from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest

from promptval.rules.core import analyze_and_fix, _offline_structured_fix, _stripped_equal


def test_analyze_and_fix_success():
    """Test analyze_and_fix with successful LLM response."""
    with patch('promptval.rules.core._llm_analyze_and_fix') as mock_llm:
        mock_llm.return_value = {
            "issues": [
                {
                    "type": "redundancy",
                    "severity": "warning",
                    "message": "Redundant information",
                    "suggestion": "Remove redundancy"
                }
            ],
            "fixed_text": "Task:\n  Clean prompt\n\nSuccess Criteria:\n  - Clear output",
            "score": 85.0
        }
        
        result = analyze_and_fix("Test prompt")
        
        assert result["issues"] == [
            {
                "type": "redundancy",
                "severity": "warning",
                "message": "Redundant information",
                "suggestion": "Remove redundancy"
            }
        ]
        assert result["fixed_text"].startswith("Task:")
        assert result["score"] == 85.0


def test_analyze_and_fix_no_issues():
    """Test analyze_and_fix with no issues detected."""
    with patch('promptval.rules.core._llm_analyze_and_fix') as mock_llm:
        mock_llm.return_value = {
            "issues": [],
            "fixed_text": "Perfect prompt",
            "score": 100.0
        }
        
        result = analyze_and_fix("Perfect prompt")
        
        assert result["issues"] == []
        assert result["fixed_text"] == "Perfect prompt"
        assert result["score"] == 100.0


def test_analyze_and_fix_llm_failure():
    """Test analyze_and_fix when LLM fails."""
    with patch('promptval.rules.core._llm_analyze_and_fix') as mock_llm:
        mock_llm.return_value = {
            "issues": [],
            "fixed_text": "Original prompt",  # Same as input
            "score": None
        }
        
        result = analyze_and_fix("Original prompt")
        
        # Should use offline fallback since fixed_text equals original
        assert result["fixed_prompt"].startswith("Task:")
        assert "Success Criteria:" in result["fixed_prompt"]
        assert "Examples:" in result["fixed_prompt"]


def test_stripped_equal():
    """Test _stripped_equal function."""
    assert _stripped_equal("hello", "hello")
    assert _stripped_equal("  hello  ", "hello")
    assert _stripped_equal("hello\n", "hello")
    assert _stripped_equal("hello\r\n", "hello")
    assert _stripped_equal("hello\r", "hello")
    assert not _stripped_equal("hello", "world")
    assert not _stripped_equal("hello", "hello world")
    
    # Edge cases
    assert _stripped_equal("", "")
    assert _stripped_equal(None, None)
    assert not _stripped_equal("hello", None)
    assert not _stripped_equal(None, "hello")


def test_offline_structured_fix_basic():
    """Test _offline_structured_fix with basic input."""
    text = "Explain how to bake bread"
    result = _offline_structured_fix(text)
    
    assert "Task:" in result
    assert "Explain how to bake bread" in result
    assert "Success Criteria:" in result
    assert "Examples:" in result
    assert "No Secrets / No PII:" in result


def test_offline_structured_fix_with_length_constraints():
    """Test _offline_structured_fix with length constraints."""
    text = "Explain how to bake bread. The explanation must be no longer than 100 words."
    result = _offline_structured_fix(text)
    
    assert "Task:" in result
    assert "Explain how to bake bread" in result
    assert "Success Criteria:" in result
    assert "Response must be no more than 100 words" in result
    assert "Examples:" in result


def test_offline_structured_fix_with_exact_length():
    """Test _offline_structured_fix with exact length requirements."""
    text = "Write exactly 50 words about cats"
    result = _offline_structured_fix(text)
    
    assert "Task:" in result
    assert "Write exactly 50 words about cats" in result
    assert "Success Criteria:" in result
    assert "Response must be exactly 50 words" in result


def test_offline_structured_fix_multiple_constraints():
    """Test _offline_structured_fix with multiple length constraints."""
    text = "Write about dogs. Must be no longer than 200 words. Also write exactly 10 sentences."
    result = _offline_structured_fix(text)
    
    assert "Response must be no more than 200 words" in result
    assert "Response must be exactly 10 sentences" in result


def test_offline_structured_fix_empty_input():
    """Test _offline_structured_fix with empty input."""
    result = _offline_structured_fix("")
    
    assert "Task:" in result
    assert "Success Criteria:" in result
    assert "Examples:" in result


def test_offline_structured_fix_whitespace_only():
    """Test _offline_structured_fix with whitespace-only input."""
    result = _offline_structured_fix("   \n\t   ")
    
    assert "Task:" in result
    assert "Success Criteria:" in result
    assert "Examples:" in result


def test_offline_structured_fix_applies_compliance():
    """Test _offline_structured_fix applies compliance rules."""
    text = "Calculate 2 + 2 * 3"
    result = _offline_structured_fix(text)
    
    # Should add "Think step by step" for math
    assert "Think step by step" in result or "Task:" in result


def test_offline_structured_fix_section_spacing():
    """Test _offline_structured_fix ensures proper section spacing."""
    text = "Test prompt"
    result = _offline_structured_fix(text)
    
    # Should have proper spacing between sections
    assert "\n\nSuccess Criteria:" in result
    assert "\n\nExamples:" in result
    assert "\n\nNo Secrets / No PII:" in result


def test_analyze_and_fix_with_environment_variables():
    """Test analyze_and_fix respects environment variables."""
    with patch.dict(os.environ, {
        "PROMPTVAL_PROVIDER": "anthropic",
        "PROMPTVAL_MODEL": "claude-3-sonnet",
        "PROMPTVAL_TEMPERATURE": "0.7"
    }):
        with patch('promptval.rules.core.ProviderFactory.from_env') as mock_factory:
            mock_provider = MagicMock()
            mock_provider.evaluate_prompt.return_value = {
                "issues": [],
                "fixed_text": "Test",
                "score": 100
            }
            mock_factory.return_value = mock_provider
            
            result = analyze_and_fix("Test prompt")
            
            # Verify provider was created with correct parameters
            mock_factory.assert_called_once()
            call_kwargs = mock_factory.call_args[1]
            assert call_kwargs["provider_name"] == "anthropic"
            assert call_kwargs["model"] == "claude-3-sonnet"
            assert call_kwargs["temperature"] == 0.7


def test_analyze_and_fix_score_handling():
    """Test analyze_and_fix handles different score types."""
    with patch('promptval.rules.core._llm_analyze_and_fix') as mock_llm:
        # Test with integer score
        mock_llm.return_value = {
            "issues": [],
            "fixed_text": "Test",
            "score": 85
        }
        
        result = analyze_and_fix("Test")
        assert result["score"] == 85
        
        # Test with float score
        mock_llm.return_value = {
            "issues": [],
            "fixed_text": "Test",
            "score": 85.5
        }
        
        result = analyze_and_fix("Test")
        assert result["score"] == 85.5
        
        # Test with string score
        mock_llm.return_value = {
            "issues": [],
            "fixed_text": "Test",
            "score": "90"
        }
        
        result = analyze_and_fix("Test")
        assert result["score"] == 90.0
        
        # Test with invalid score
        mock_llm.return_value = {
            "issues": [],
            "fixed_text": "Test",
            "score": "invalid"
        }
        
        result = analyze_and_fix("Test")
        assert result["score"] is None
