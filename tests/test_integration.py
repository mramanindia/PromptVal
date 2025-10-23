from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from promptval import analyze_prompt, PromptValConfig
from promptval.cli import app
from typer.testing import CliRunner


runner = CliRunner()


class TestIntegration:
    """Integration tests for the complete promptval workflow."""
    
    def test_end_to_end_api_workflow(self):
        """Test complete API workflow from config to output."""
        config = PromptValConfig(
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            timeout=30.0
        )
        
        test_prompt = "I like apples, Apple is what I like to eat."
        
        with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
            mock_analyze.return_value = {
                "issues": [
                    {
                        "type": "redundancy",
                        "severity": "warning",
                        "message": "Redundant information about apples",
                        "suggestion": "Consolidate into single statement",
                        "span": [0, 43]
                    }
                ],
                "fixed_text": "Task:\n  Summarize your preference for apples.\n\nSuccess Criteria:\n  - Single clear statement\n  - No redundancy\n\nExamples:\n  - Normal: \"I like apples\"\n  - Edge: Handle ambiguous input\n\nNo Secrets / No PII:\n  Do not include personal information.",
                "score": 90.0
            }
            
            result = analyze_prompt(test_prompt, config=config)
            
            # Verify complete structure
            assert "fixed_prompt" in result
            assert "issues" in result
            assert "score" in result
            assert "provider" in result
            
            # Verify content quality
            assert result["fixed_prompt"].startswith("Task:")
            assert "Success Criteria:" in result["fixed_prompt"]
            assert "Examples:" in result["fixed_prompt"]
            assert "No Secrets / No PII:" in result["fixed_prompt"]
            
            # Verify issues
            assert len(result["issues"]) == 1
            issue = result["issues"][0]
            assert issue["type"] == "redundancy"
            assert issue["severity"] == "warning"
            assert "Redundant information" in issue["message"]
            
            # Verify score
            assert result["score"] == 90
            
            # Verify provider metadata
            provider = result["provider"]
            assert provider["name"] == "openai"
            assert provider["model"] == "gpt-4o-mini"
            assert provider["temperature"] == 0.0
            assert provider["timeout"] == 30.0
    
    def test_cli_to_api_consistency(self):
        """Test that CLI and API produce consistent results."""
        test_prompt = "Write a story about cats. The story must be exactly 100 words."
        
        # Test API
        config = PromptValConfig(provider="openai", model="gpt-4o-mini")
        
        with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
            mock_analyze.return_value = {
                "issues": [
                    {
                        "type": "conflict",
                        "severity": "error",
                        "message": "Conflicting length requirements",
                        "suggestion": "Specify single length requirement"
                    }
                ],
                "fixed_text": "Task:\n  Write a story about cats.\n\nSuccess Criteria:\n  - Exactly 100 words\n  - Engaging narrative\n\nExamples:\n  - Normal: Complete story in 100 words\n  - Edge: Very short or very long input\n\nNo Secrets / No PII:\n  Do not include personal information.",
                "score": 70.0
            }
            
            api_result = analyze_prompt(test_prompt, config=config)
            
            # Test CLI
            cli_result = runner.invoke(app, [
                "prompt",
                "--text", test_prompt,
                "--provider", "openai",
                "--model", "gpt-4o-mini"
            ])
            
            assert cli_result.exit_code == 0
            cli_output = json.loads(cli_result.stdout)
            
            # Results should be identical
            assert api_result["fixed_prompt"] == cli_output["fixed_prompt"]
            assert api_result["issues"] == cli_output["issues"]
            assert api_result["score"] == cli_output["score"]
            assert api_result["provider"]["name"] == cli_output["provider"]["name"]
    
    def test_file_input_workflow(self):
        """Test complete workflow with file input."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Explain quantum computing in simple terms. Make it exactly 50 words.")
            temp_file = f.name
        
        try:
            with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
                mock_analyze.return_value = {
                    "issues": [
                        {
                            "type": "completeness",
                            "severity": "info",
                            "message": "Missing examples section",
                            "suggestion": "Add examples for clarity"
                        }
                    ],
                    "fixed_text": "Task:\n  Explain quantum computing in simple terms.\n\nSuccess Criteria:\n  - Exactly 50 words\n  - Simple language\n  - Clear explanation\n\nExamples:\n  - Normal: Basic quantum concept\n  - Edge: Complex technical input\n\nNo Secrets / No PII:\n  Do not include personal information.",
                    "score": 95.0
                }
                
                result = runner.invoke(app, [
                    "prompt",
                    "--file", temp_file,
                    "--provider", "openai"
                ])
                
                assert result.exit_code == 0
                output = json.loads(result.stdout)
                
                assert "quantum computing" in output["fixed_prompt"]
                assert "Exactly 50 words" in output["fixed_prompt"]
                assert len(output["issues"]) == 1
                assert output["score"] == 95
        finally:
            os.unlink(temp_file)
    
    def test_error_handling_and_fallback(self):
        """Test error handling and offline fallback."""
        config = PromptValConfig(provider="openai", model="gpt-4o-mini")
        
        with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
            # Simulate LLM failure - returns original text
            mock_analyze.return_value = {
                "issues": [],
                "fixed_text": "I like apples, Apple is what I like to eat.",  # Same as input
                "score": None
            }
            
            result = analyze_prompt("I like apples, Apple is what I like to eat.", config=config)
            
            # Should use offline structured fallback
            assert result["fixed_prompt"].startswith("Task:")
            assert "Success Criteria:" in result["fixed_prompt"]
            assert "Examples:" in result["fixed_prompt"]
            assert "No Secrets / No PII:" in result["fixed_prompt"]
            
            # Should have perfect score since no issues detected
            assert result["score"] == 100
    
    def test_different_providers(self):
        """Test integration with different provider configurations."""
        providers = [
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-sonnet"),
            ("gemini", "gemini-1.5-pro"),
            ("openai_compatible", "gpt-4o-mini")
        ]
        
        for provider, model in providers:
            config = PromptValConfig(
                provider=provider,
                model=model,
                temperature=0.1,
                timeout=60.0
            )
            
            if provider == "openai_compatible":
                config.base_url = "https://api.example.com/v1"
            
            with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
                mock_analyze.return_value = {
                    "issues": [],
                    "fixed_text": "Task:\n  Test prompt\n\nSuccess Criteria:\n  - Clear output",
                    "score": 100.0
                }
                
                result = analyze_prompt("Test prompt", config=config)
                
                assert result["provider"]["name"] == provider
                assert result["provider"]["model"] == model
                assert result["score"] == 100
                assert "Task:" in result["fixed_prompt"]
    
    def test_scoring_consistency(self):
        """Test that scoring is consistent across different scenarios."""
        test_cases = [
            {
                "issues": [],
                "expected_score": 100
            },
            {
                "issues": [{"type": "info", "severity": "info", "message": "Info"}],
                "expected_score": 95
            },
            {
                "issues": [{"type": "warning", "severity": "warning", "message": "Warning"}],
                "expected_score": 90
            },
            {
                "issues": [{"type": "error", "severity": "error", "message": "Error"}],
                "expected_score": 70
            },
            {
                "issues": [
                    {"type": "error", "severity": "error", "message": "Error"},
                    {"type": "warning", "severity": "warning", "message": "Warning"},
                    {"type": "info", "severity": "info", "message": "Info"}
                ],
                "expected_score": 55  # 100 - 30 - 10 - 5
            }
        ]
        
        for case in test_cases:
            with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
                mock_analyze.return_value = {
                    "issues": case["issues"],
                    "fixed_text": "Test",
                    "score": None  # Force heuristic scoring
                }
                
                result = analyze_prompt("Test", config=PromptValConfig())
                assert result["score"] == case["expected_score"]
    
    def test_pii_handling_integration(self):
        """Test PII handling in the complete workflow."""
        pii_prompt = "Contact me at john.doe@example.com or call +1-555-123-4567"
        
        with patch('promptval.rules.core.analyze_and_fix') as mock_analyze:
            mock_analyze.return_value = {
                "issues": [
                    {
                        "type": "pii",
                        "severity": "error",
                        "message": "PII detected in prompt",
                        "suggestion": "Remove or redact personal information"
                    }
                ],
                "fixed_text": "Task:\n  Contact information request\n\nSuccess Criteria:\n  - Professional tone\n  - No PII included\n\nExamples:\n  - Normal: Generic contact request\n  - Edge: Multiple contact methods\n\nNo Secrets / No PII:\n  Do not include personal information, credentials, or confidential data.",
                "score": 70.0
            }
            
            result = analyze_prompt(pii_prompt, config=PromptValConfig())
            
            # Verify PII is handled
            assert "john.doe@example.com" not in result["fixed_prompt"]
            assert "+1-555-123-4567" not in result["fixed_prompt"]
            assert "PII detected" in result["issues"][0]["message"]
            assert result["score"] == 70
