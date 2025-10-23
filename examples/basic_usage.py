#!/usr/bin/env python3
"""
Basic usage examples for PromptVal package.

This script demonstrates how to use PromptVal as a Python package
for prompt validation and enhancement.
"""

import os
from pathlib import Path
from promptval import analyze_prompt, PromptValConfig
from promptval.api import validate_directory, validate_file, apply_fixes


def example_single_prompt():
    """Example: Analyze a single prompt string."""
    print("=== Single Prompt Analysis ===")
    
    prompt_text = """
    Write a story about a cat. The story should be exactly 100 words long.
    Also include a comprehensive 5000-word analysis of feline behavior.
    Make sure to include my email: john.doe@example.com
    """
    
    # Analyze the prompt
    result = analyze_prompt(prompt_text)
    
    print(f"Score: {result['score']}/100")
    print(f"Number of issues: {len(result['issues'])}")
    
    for issue in result['issues']:
        print(f"- {issue['type'].upper()}: {issue['message']}")
        print(f"  Suggestion: {issue['suggestion']}")
    
    print(f"\nFixed prompt:\n{result['fixed_text']}")


def example_with_config():
    """Example: Using custom configuration."""
    print("\n=== Custom Configuration ===")
    
    # Create custom configuration
    config = PromptValConfig(
        provider="openai",
        model="gpt-4o-mini",
        temperature=0.1,
        timeout=30.0
    )
    
    prompt_text = "Create a marketing email for our product launch."
    result = analyze_prompt(prompt_text, config)
    
    print(f"Score: {result['score']}/100")
    print(f"Issues found: {len(result['issues'])}")


def example_directory_validation():
    """Example: Validate a directory of prompt files."""
    print("\n=== Directory Validation ===")
    
    # Create sample directory if it doesn't exist
    sample_dir = Path("sample_prompts")
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample prompt files
    (sample_dir / "prompt1.txt").write_text("Write a short story about a robot.")
    (sample_dir / "prompt2.txt").write_text("Create a marketing email for our new product. Include my phone number: 555-123-4567")
    
    # Validate directory
    results = validate_directory(str(sample_dir), use_llm=False)  # Offline mode
    
    print(f"Validated {len(results)} files:")
    for result in results:
        print(f"- {Path(result.file_path).name}: Score {result.score}/100")
        if result.issues:
            print(f"  Issues: {len(result.issues)}")
    
    # Apply fixes
    apply_fixes(results, out_dir="corrected_prompts")
    print("Fixed prompts saved to 'corrected_prompts/' directory")


def example_offline_mode():
    """Example: Using offline mode for PII detection only."""
    print("\n=== Offline Mode (PII Detection) ===")
    
    prompt_with_pii = """
    Please send an email to john.doe@company.com about the project.
    Use the API key: sk-1234567890abcdef for authentication.
    The server is at 192.168.1.100:8080
    """
    
    # This will work without any API keys
    result = analyze_prompt(prompt_with_pii)
    
    print(f"PII issues detected: {len([i for i in result['issues'] if i['type'] == 'pii'])}")
    for issue in result['issues']:
        if issue['type'] == 'pii':
            print(f"- PII: {issue['message']}")


def main():
    """Run all examples."""
    print("PromptVal Package Usage Examples")
    print("=" * 40)
    
    # Check if API key is available
    has_api_key = bool(os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    
    if has_api_key:
        print("✅ API key detected - running full examples")
        example_single_prompt()
        example_with_config()
    else:
        print("⚠️  No API key detected - running offline examples only")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY for full functionality")
    
    example_directory_validation()
    example_offline_mode()
    
    print("\n" + "=" * 40)
    print("Examples completed!")


if __name__ == "__main__":
    main()
