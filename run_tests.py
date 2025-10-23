#!/usr/bin/env python3
"""
Test runner script for promptval package.

This script provides an easy way to run all tests or specific test modules.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_pattern=None, verbose=False, coverage=False, llm_tests=False):
    """Run tests with the specified options."""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=promptval", "--cov-report=html", "--cov-report=term"])
    
    if not llm_tests:
        # Skip LLM tests by default (they require API keys)
        cmd.extend(["-m", "not llm"])
    
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("tests/")
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install it with: pip install pytest")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run promptval tests")
    parser.add_argument(
        "pattern", 
        nargs="?", 
        help="Test pattern to run (e.g., 'test_pii.py', 'test_api.py::TestPromptValAPI::test_analyze_prompt_basic')"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--llm", 
        action="store_true", 
        help="Include LLM tests (requires API keys)"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all tests including LLM tests"
    )
    
    args = parser.parse_args()
    
    if args.all:
        args.llm = True
    
    print("🧪 PromptVal Test Runner")
    print("=" * 60)
    
    if args.llm:
        print("⚠️  Running LLM tests - ensure API keys are configured!")
        print("   Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or XAI_API_KEY")
        print()
    else:
        print("ℹ️  Skipping LLM tests (use --llm to include them)")
        print()
    
    return run_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        llm_tests=args.llm
    )


if __name__ == "__main__":
    sys.exit(main())
