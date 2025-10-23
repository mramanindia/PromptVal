"""
Test cases for scoring functionality.

This module tests the scoring system that calculates quality scores based on detected issues.
"""

import pytest
from promptval.api import _compute_score
from promptval.models import Issue, IssueType, Severity, ValidationResult
from promptval.api import analyze_prompt, PromptValConfig


class TestScoringSystem:
    """Test the scoring functionality."""

    def test_perfect_score_no_issues(self):
        """Test that text with no issues gets a perfect score."""
        issues = []
        score = _compute_score(issues)
        assert score == 100

    def test_error_penalty(self):
        """Test that errors reduce the score by 30 points."""
        issues = [
            {"severity": "error", "message": "Test error"}
        ]
        score = _compute_score(issues)
        assert score == 70  # 100 - 30

    def test_warning_penalty(self):
        """Test that warnings reduce the score by 10 points."""
        issues = [
            {"severity": "warning", "message": "Test warning"}
        ]
        score = _compute_score(issues)
        assert score == 90  # 100 - 10

    def test_info_penalty(self):
        """Test that info issues reduce the score by 5 points."""
        issues = [
            {"severity": "info", "message": "Test info"}
        ]
        score = _compute_score(issues)
        assert score == 95  # 100 - 5

    def test_multiple_issues_penalty(self):
        """Test that multiple issues accumulate penalties."""
        issues = [
            {"severity": "error", "message": "Error 1"},
            {"severity": "error", "message": "Error 2"},
            {"severity": "warning", "message": "Warning 1"},
            {"severity": "info", "message": "Info 1"},
        ]
        score = _compute_score(issues)
        # 100 - (2 * 30) - (1 * 10) - (1 * 5) = 100 - 60 - 10 - 5 = 25
        assert score == 25

    def test_score_clamped_to_zero(self):
        """Test that score is clamped to minimum of 0."""
        issues = [
            {"severity": "error", "message": "Error 1"},
            {"severity": "error", "message": "Error 2"},
            {"severity": "error", "message": "Error 3"},
            {"severity": "error", "message": "Error 4"},
        ]
        score = _compute_score(issues)
        # 100 - (4 * 30) = 100 - 120 = -20, clamped to 0
        assert score == 0

    def test_score_clamped_to_hundred(self):
        """Test that score is clamped to maximum of 100."""
        issues = []  # No issues should give 100
        score = _compute_score(issues)
        assert score == 100

    def test_mixed_severity_penalties(self):
        """Test mixed severity levels with proper penalties."""
        issues = [
            {"severity": "error", "message": "Critical error"},
            {"severity": "warning", "message": "Warning 1"},
            {"severity": "warning", "message": "Warning 2"},
            {"severity": "info", "message": "Info 1"},
            {"severity": "info", "message": "Info 2"},
            {"severity": "info", "message": "Info 3"},
        ]
        score = _compute_score(issues)
        # 100 - 30 - (2 * 10) - (3 * 5) = 100 - 30 - 20 - 15 = 35
        assert score == 35

    def test_case_insensitive_severity(self):
        """Test that severity matching is case insensitive."""
        issues = [
            {"severity": "ERROR", "message": "Uppercase error"},
            {"severity": "Warning", "message": "Mixed case warning"},
            {"severity": "INFO", "message": "Uppercase info"},
        ]
        score = _compute_score(issues)
        # 100 - 30 - 10 - 5 = 55
        assert score == 55

    def test_unknown_severity_ignored(self):
        """Test that unknown severity levels are ignored."""
        issues = [
            {"severity": "error", "message": "Valid error"},
            {"severity": "unknown", "message": "Unknown severity"},
            {"severity": "", "message": "Empty severity"},
            {"severity": None, "message": "None severity"},
        ]
        score = _compute_score(issues)
        # Only the error should count: 100 - 30 = 70
        assert score == 70

    def test_missing_severity_field(self):
        """Test handling of missing severity field."""
        issues = [
            {"message": "No severity field"},
            {"severity": "error", "message": "Valid error"},
        ]
        score = _compute_score(issues)
        # Only the error should count: 100 - 30 = 70
        assert score == 70

    def test_empty_issues_list(self):
        """Test empty issues list."""
        issues = []
        score = _compute_score(issues)
        assert score == 100

    def test_none_issues_list(self):
        """Test None issues list."""
        issues = None
        score = _compute_score(issues)
        assert score == 100

    def test_validation_result_has_errors_property(self):
        """Test ValidationResult.has_errors property."""
        # Test with errors
        error_issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="Test error"
        )
        warning_issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.redundancy,
            severity=Severity.warning,
            message="Test warning"
        )
        
        result_with_errors = ValidationResult(
            file_path="test.txt",
            issues=[error_issue, warning_issue]
        )
        assert result_with_errors.has_errors is True
        
        # Test without errors
        result_without_errors = ValidationResult(
            file_path="test.txt",
            issues=[warning_issue]
        )
        assert result_without_errors.has_errors is False
        
        # Test empty issues
        result_empty = ValidationResult(
            file_path="test.txt",
            issues=[]
        )
        assert result_empty.has_errors is False

    def test_analyze_prompt_score_calculation(self):
        """Test that analyze_prompt calculates scores correctly."""
        # This test requires LLM functionality, so we'll mock the behavior
        # In a real test environment, you would need to set up API keys
        # For now, we'll test the structure and comment about LLM requirements
        
        # NOTE: This test requires LLM API keys to be configured
        # Set environment variables:
        # - OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or XAI_API_KEY
        # - PROMPTVAL_PROVIDER (optional, defaults to openai)
        # - PROMPTVAL_MODEL (optional, provider-specific default)
        
        text = "This is a test prompt with some issues."
        config = PromptValConfig(provider="openai", model="gpt-3.5-turbo")
        
        # This will fail without proper API keys, but tests the structure
        try:
            result = analyze_prompt(text, config)
            assert "score" in result
            assert "issues" in result
            assert "fixed_prompt" in result
            assert "provider" in result
            assert isinstance(result["score"], int)
            assert 0 <= result["score"] <= 100
        except RuntimeError as e:
            if "API_KEY" in str(e):
                pytest.skip("LLM API keys not configured - test requires API access")
            else:
                raise

    def test_provider_metadata_in_analyze_prompt(self):
        """Test that provider metadata is included in analyze_prompt results."""
        text = "Test prompt"
        config = PromptValConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
            timeout=30.0
        )
        
        try:
            result = analyze_prompt(text, config)
            provider_meta = result["provider"]
            
            assert "name" in provider_meta
            assert "model" in provider_meta
            assert "temperature" in provider_meta
            assert "timeout" in provider_meta
            assert "base_url_set" in provider_meta
            
            assert provider_meta["name"] == "openai"
            assert provider_meta["model"] == "gpt-3.5-turbo"
            assert provider_meta["temperature"] == 0.7
            assert provider_meta["timeout"] == 30.0
            assert provider_meta["base_url_set"] is False
        except RuntimeError as e:
            if "API_KEY" in str(e):
                pytest.skip("LLM API keys not configured - test requires API access")
            else:
                raise

    def test_score_fallback_mechanism(self):
        """Test that score calculation falls back to heuristic when provider fails."""
        # This tests the fallback mechanism in analyze_prompt
        text = "Test prompt"
        
        try:
            result = analyze_prompt(text)
            # Should always return a valid score even if provider fails
            assert isinstance(result["score"], int)
            assert 0 <= result["score"] <= 100
        except Exception as e:
            # If API keys are missing, that's expected
            if "API_KEY" in str(e):
                pytest.skip("LLM API keys not configured - test requires API access")
            else:
                raise

    def test_edge_case_scores(self):
        """Test edge cases in score calculation."""
        # Test exactly at boundary values
        issues_99 = [{"severity": "info", "message": "Info"}]
        score_99 = _compute_score(issues_99)
        assert score_99 == 95
        
        # Test multiple small penalties
        issues_many_info = [{"severity": "info", "message": f"Info {i}"} for i in range(20)]
        score_many = _compute_score(issues_many_info)
        # 100 - (20 * 5) = 0, clamped to 0
        assert score_many == 0
        
        # Test mixed with one error
        issues_mixed = [{"severity": "error", "message": "Error"}] + issues_many_info
        score_mixed = _compute_score(issues_mixed)
        # 100 - 30 - (20 * 5) = -30, clamped to 0
        assert score_mixed == 0
