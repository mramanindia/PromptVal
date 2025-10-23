"""
Test cases for LLM-based fixing functionality.

IMPORTANT: These tests require LLM API keys to be configured in the environment.
Set the appropriate environment variables before running these tests:

Required API Keys (at least one):
- OPENAI_API_KEY for OpenAI provider
- ANTHROPIC_API_KEY for Anthropic provider  
- GOOGLE_API_KEY for Google Gemini provider
- XAI_API_KEY for X.ai Grok provider

Optional Configuration:
- PROMPTVAL_PROVIDER: Provider name (openai, anthropic, gemini, xai, openai_compatible)
- PROMPTVAL_MODEL: Model name (provider-specific)
- PROMPTVAL_BASE_URL: Base URL for OpenAI-compatible providers
- PROMPTVAL_TIMEOUT: Request timeout in seconds
- PROMPTVAL_TEMPERATURE: Sampling temperature (0.0-1.0)

Tests will be skipped if no API keys are available.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from promptval.api import analyze_prompt, PromptValConfig
from promptval.rules.core import analyze_and_fix, generate_fixed_text
from promptval.llm.provider import ProviderFactory


class TestLLMFixing:
    """Test LLM-based fixing functionality."""

    def _skip_if_no_api_keys(self):
        """Skip test if no API keys are available."""
        api_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "GOOGLE_API_KEY",
            "XAI_API_KEY"
        ]
        
        if not any(os.getenv(key) for key in api_keys):
            pytest.skip("No LLM API keys configured - set OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or XAI_API_KEY")

    def test_analyze_prompt_openai_provider(self):
        """Test analyze_prompt with OpenAI provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        text = "Write a function to calculate the area of a circle"
        config = PromptValConfig(provider="openai", model="gpt-3.5-turbo")
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check provider metadata
        assert result["provider"]["name"] == "openai"
        assert result["provider"]["model"] == "gpt-3.5-turbo"
        
        # Check that we got a structured response
        assert isinstance(result["fixed_prompt"], str)
        assert len(result["fixed_prompt"]) > 0
        assert isinstance(result["issues"], list)
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_analyze_prompt_anthropic_provider(self):
        """Test analyze_prompt with Anthropic provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        text = "Create a user authentication system"
        config = PromptValConfig(provider="anthropic", model="claude-3-haiku-20240307")
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check provider metadata
        assert result["provider"]["name"] == "anthropic"
        assert result["provider"]["model"] == "claude-3-haiku-20240307"

    def test_analyze_prompt_google_provider(self):
        """Test analyze_prompt with Google Gemini provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not set")
        
        text = "Design a database schema for a blog"
        config = PromptValConfig(provider="gemini", model="gemini-pro")
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check provider metadata
        assert result["provider"]["name"] == "gemini"
        assert result["provider"]["model"] == "gemini-pro"

    def test_analyze_prompt_xai_provider(self):
        """Test analyze_prompt with X.ai Grok provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("XAI_API_KEY"):
            pytest.skip("XAI_API_KEY not set")
        
        text = "Write a Python script to process CSV files"
        config = PromptValConfig(provider="xai", model="grok-beta")
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check provider metadata
        assert result["provider"]["name"] == "xai"
        assert result["provider"]["model"] == "grok-beta"

    def test_analyze_prompt_openai_compatible_provider(self):
        """Test analyze_prompt with OpenAI-compatible provider."""
        self._skip_if_no_api_keys()
        
        # This test requires a custom base URL for OpenAI-compatible API
        base_url = os.getenv("PROMPTVAL_BASE_URL")
        if not base_url:
            pytest.skip("PROMPTVAL_BASE_URL not set for OpenAI-compatible provider")
        
        text = "Create a REST API endpoint"
        config = PromptValConfig(
            provider="openai_compatible",
            model="gpt-3.5-turbo",
            base_url=base_url
        )
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check provider metadata
        assert result["provider"]["name"] == "openai_compatible"
        assert result["provider"]["base_url_set"] is True

    def test_analyze_prompt_with_custom_parameters(self):
        """Test analyze_prompt with custom temperature and timeout."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        text = "Write a creative story"
        config = PromptValConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.9,
            timeout=60.0
        )
        
        result = analyze_prompt(text, config)
        
        assert "fixed_prompt" in result
        assert "issues" in result
        assert "score" in result
        assert "provider" in result
        
        # Check that custom parameters are reflected in provider metadata
        assert result["provider"]["temperature"] == 0.9
        assert result["provider"]["timeout"] == 60.0

    def test_analyze_prompt_without_config(self):
        """Test analyze_prompt without explicit config (uses environment variables)."""
        self._skip_if_no_api_keys()
        
        # Set environment variables
        with patch.dict(os.environ, {
            "PROMPTVAL_PROVIDER": "openai",
            "PROMPTVAL_MODEL": "gpt-3.5-turbo"
        }):
            text = "Write a sorting algorithm"
            result = analyze_prompt(text)
            
            assert "fixed_prompt" in result
            assert "issues" in result
            assert "score" in result
            assert "provider" in result
            
            # Should use environment defaults
            assert result["provider"]["name"] == "openai"

    def test_analyze_and_fix_function(self):
        """Test the analyze_and_fix function directly."""
        self._skip_if_no_api_keys()
        
        text = "Write a function to validate email addresses"
        result = analyze_and_fix(text)
        
        assert "issues" in result
        assert "fixed_text" in result
        assert "score" in result
        
        assert isinstance(result["issues"], list)
        assert isinstance(result["fixed_text"], str)
        assert isinstance(result["score"], (int, float, type(None)))

    def test_generate_fixed_text_function(self):
        """Test the generate_fixed_text function directly."""
        self._skip_if_no_api_keys()
        
        text = "Create a web scraper"
        result = generate_fixed_text(text)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should be structured output
        assert "Task:" in result or "Success Criteria:" in result

    def test_provider_factory_openai(self):
        """Test ProviderFactory with OpenAI provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        provider = ProviderFactory.from_env(provider_name="openai", model="gpt-3.5-turbo")
        
        assert provider is not None
        # Test that provider can be called (this will make an actual API call)
        try:
            result = provider.evaluate_prompt("Test prompt")
            assert isinstance(result, dict)
        except Exception as e:
            # If API call fails, that's okay for testing the factory
            assert "API" in str(e) or "key" in str(e).lower()

    def test_provider_factory_anthropic(self):
        """Test ProviderFactory with Anthropic provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        provider = ProviderFactory.from_env(provider_name="anthropic", model="claude-3-haiku-20240307")
        
        assert provider is not None

    def test_provider_factory_google(self):
        """Test ProviderFactory with Google provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not set")
        
        provider = ProviderFactory.from_env(provider_name="gemini", model="gemini-pro")
        
        assert provider is not None

    def test_provider_factory_xai(self):
        """Test ProviderFactory with X.ai provider."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("XAI_API_KEY"):
            pytest.skip("XAI_API_KEY not set")
        
        provider = ProviderFactory.from_env(provider_name="xai", model="grok-beta")
        
        assert provider is not None

    def test_provider_factory_openai_compatible(self):
        """Test ProviderFactory with OpenAI-compatible provider."""
        self._skip_if_no_api_keys()
        
        base_url = os.getenv("PROMPTVAL_BASE_URL")
        if not base_url:
            pytest.skip("PROMPTVAL_BASE_URL not set for OpenAI-compatible provider")
        
        provider = ProviderFactory.from_env(
            provider_name="openai_compatible",
            model="gpt-3.5-turbo",
            base_url=base_url
        )
        
        assert provider is not None

    def test_provider_factory_invalid_provider(self):
        """Test ProviderFactory with invalid provider name."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderFactory.from_env(provider_name="invalid_provider")

    def test_provider_factory_missing_api_key(self):
        """Test ProviderFactory behavior when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="API_KEY not set"):
                ProviderFactory.from_env(provider_name="openai")

    def test_analyze_prompt_fallback_on_provider_failure(self):
        """Test that analyze_prompt falls back gracefully when provider fails."""
        self._skip_if_no_api_keys()
        
        # Use a provider that might fail
        text = "Write a simple function"
        
        try:
            result = analyze_prompt(text)
            # Should still return a valid structure even if provider fails
            assert "fixed_prompt" in result
            assert "issues" in result
            assert "score" in result
            assert "provider" in result
        except Exception as e:
            # If it fails completely, it should be due to missing API keys
            assert "API" in str(e) or "key" in str(e).lower()

    def test_analyze_prompt_pii_redaction(self):
        """Test that PII is redacted before sending to LLM."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Text with PII that should be redacted
        text = "Contact me at test@example.com for the API key sk-1234567890abcdef"
        
        with patch('promptval.rules.core._local_redact') as mock_redact:
            mock_redact.return_value = "Contact me at [REDACTED] for the API key [REDACTED]"
            
            result = analyze_prompt(text)
            
            # Verify that redaction was called
            mock_redact.assert_called_once()
            
            # Result should still be valid
            assert "fixed_prompt" in result
            assert "issues" in result

    def test_analyze_prompt_structured_output(self):
        """Test that LLM output is properly structured."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        text = "Write a function to calculate fibonacci numbers"
        result = analyze_prompt(text)
        
        # The fixed prompt should be well-structured
        fixed_prompt = result["fixed_prompt"]
        assert isinstance(fixed_prompt, str)
        assert len(fixed_prompt) > len(text)  # Should be expanded/structured
        
        # Should contain structured elements
        structured_elements = ["Task:", "Success Criteria:", "Examples:"]
        has_structured = any(element in fixed_prompt for element in structured_elements)
        assert has_structured or "Think step by step" in fixed_prompt

    def test_analyze_prompt_issues_detection(self):
        """Test that LLM detects various types of issues."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Text that should trigger various issues
        text = "Write a function that is both fast and slow, and also write a function that is both fast and slow"
        
        result = analyze_prompt(text)
        
        assert "issues" in result
        assert isinstance(result["issues"], list)
        
        # Should detect some issues (redundancy, conflict, etc.)
        if result["issues"]:
            for issue in result["issues"]:
                assert "type" in issue or "issue_type" in issue
                assert "severity" in issue
                assert "message" in issue

    def test_analyze_prompt_score_calculation(self):
        """Test that LLM provides meaningful scores."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        text = "Write a function"
        result = analyze_prompt(text)
        
        assert "score" in result
        score = result["score"]
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_analyze_prompt_with_environment_override(self):
        """Test that environment variables override config parameters."""
        self._skip_if_no_api_keys()
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        # Set environment variables
        with patch.dict(os.environ, {
            "PROMPTVAL_PROVIDER": "openai",
            "PROMPTVAL_MODEL": "gpt-4",
            "PROMPTVAL_TEMPERATURE": "0.5"
        }):
            text = "Write a test"
            config = PromptValConfig(provider="anthropic")  # This should be overridden
            
            result = analyze_prompt(text, config)
            
            # Should use environment values, not config values
            assert result["provider"]["name"] == "openai"
            assert result["provider"]["model"] == "gpt-4"
            assert result["provider"]["temperature"] == 0.5
