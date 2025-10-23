# PromptVal Test Suite

This directory contains comprehensive test cases for the PromptVal package, organized by functionality area.

## Test Files

### Core Functionality Tests

- **`test_pii.py`** - Tests PII detection using regex patterns
  - Email addresses, phone numbers, credit cards, SSNs
  - API keys (OpenAI, AWS, Google, GitHub, etc.)
  - Private keys, JWT tokens, bearer tokens
  - IPv4/IPv6 addresses, IBAN numbers
  - No LLM required - uses regex patterns only

- **`test_score.py`** - Tests scoring functionality and validation results
  - Score calculation based on issue severity
  - Error (-30), warning (-10), info (-5) penalties
  - Score clamping (0-100 range)
  - ValidationResult.has_errors property

- **`test_offline_fallback.py`** - Tests offline fallback when LLM is not available
  - Structured prompt generation
  - PII redaction before LLM calls
  - Chain of thought detection and addition
  - Section spacing and formatting

- **`test_llm_fix.py`** - Tests LLM-based fixing functionality
  - **⚠️ REQUIRES API KEYS** - See configuration section below
  - OpenAI, Anthropic, Google Gemini, X.ai Grok providers
  - OpenAI-compatible providers
  - Provider factory and configuration
  - Fallback behavior when LLM fails

- **`test_api.py`** - Tests main API functions
  - `analyze_prompt()` function
  - `validate_file()` and `validate_directory()` functions
  - `apply_fixes()` function
  - `PromptValConfig` class
  - Environment variable handling

- **`test_models.py`** - Tests data models and validation result structures
  - Pydantic models (Severity, IssueType, TextSpan, Issue, etc.)
  - ValidationResult and FixOperation models
  - Model serialization and deserialization
  - Property validation and edge cases

### Configuration

- **`conftest.py`** - Pytest configuration and fixtures
  - Common test fixtures for files, directories, and mock data
  - Environment variable management
  - Test markers and configuration

## Running Tests

### Quick Start

```bash
# Run all tests (excluding LLM tests)
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run with coverage reporting
python run_tests.py --coverage

# Run specific test file
python run_tests.py test_pii.py

# Run specific test class or method
python run_tests.py test_api.py::TestPromptValAPI::test_analyze_prompt_basic
```

### LLM Tests (Requires API Keys)

To run LLM tests, you need to configure API keys for at least one provider:

```bash
# Set environment variables
export OPENAI_API_KEY="sk-your-key-here"
# OR
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
# OR
export GOOGLE_API_KEY="your-google-key-here"
# OR
export XAI_API_KEY="your-xai-key-here"

# Run all tests including LLM tests
python run_tests.py --llm

# Run only LLM tests
python run_tests.py test_llm_fix.py
```

### Using pytest directly

```bash
# Install pytest if not already installed
pip install pytest pytest-cov

# Run all tests except LLM tests
pytest tests/ -m "not llm"

# Run with coverage
pytest tests/ --cov=promptval --cov-report=html

# Run specific test file
pytest tests/test_pii.py

# Run with verbose output
pytest tests/ -v
```

## Test Categories

### By Functionality

1. **PII Detection** (`test_pii.py`)
   - Regex pattern matching
   - Various PII types (emails, phones, keys, etc.)
   - Text span calculation
   - No external dependencies

2. **Scoring System** (`test_score.py`)
   - Heuristic score calculation
   - Severity-based penalties
   - Score clamping and edge cases
   - ValidationResult properties

3. **Offline Fallback** (`test_offline_fallback.py`)
   - Structured prompt generation
   - PII redaction
   - Chain of thought detection
   - Output compliance

4. **LLM Integration** (`test_llm_fix.py`)
   - Multiple provider support
   - API key validation
   - Provider factory
   - Fallback behavior

5. **API Functions** (`test_api.py`)
   - Core API functions
   - File and directory validation
   - Configuration handling
   - Environment variable management

6. **Data Models** (`test_models.py`)
   - Pydantic model validation
   - Serialization/deserialization
   - Property testing
   - Edge case handling

### By Test Type

- **Unit Tests** - Test individual functions and classes
- **Integration Tests** - Test component interactions
- **Mock Tests** - Test with mocked external dependencies
- **LLM Tests** - Test with actual LLM API calls (requires API keys)

## Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.llm` - Requires LLM API access
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.integration` - Integration tests

## Fixtures

Common fixtures available in `conftest.py`:

- `temp_file` - Temporary file for testing
- `temp_directory` - Temporary directory for testing
- `sample_prompt_text` - Sample prompt text
- `sample_prompt_with_pii` - Prompt with PII
- `mock_llm_response` - Mock LLM response
- `openai_environment` - Environment with OpenAI API key
- `anthropic_environment` - Environment with Anthropic API key
- And many more...

## Coverage

To generate coverage reports:

```bash
# HTML coverage report
python run_tests.py --coverage

# View coverage report
open htmlcov/index.html
```

## Continuous Integration

The test suite is designed to work in CI environments:

- LLM tests are skipped by default (require API keys)
- Tests use temporary files and directories
- No external dependencies beyond the package itself
- Comprehensive error handling and cleanup

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the project root
   - Install the package in development mode: `pip install -e .`

2. **LLM Test Failures**
   - Check that API keys are properly set
   - Verify network connectivity
   - Check API key permissions and quotas

3. **File Permission Errors**
   - Ensure write permissions in the test directory
   - Check that temporary files can be created

4. **Missing Dependencies**
   - Install test dependencies: `pip install pytest pytest-cov`
   - Install package dependencies: `pip install -r requirements.txt`

### Debug Mode

Enable debug mode for more verbose output:

```bash
export PROMPTVAL_DEBUG=true
python run_tests.py -v
```

## Contributing

When adding new tests:

1. Follow the existing naming conventions
2. Use appropriate fixtures from `conftest.py`
3. Add proper docstrings and comments
4. Mark tests with appropriate pytest markers
5. Ensure tests are deterministic and don't depend on external state
6. Add both positive and negative test cases
7. Test edge cases and error conditions

## Test Data

Test data is generated programmatically to avoid maintaining large test files. Use fixtures for common test data patterns.

For LLM tests, use realistic but safe prompts that won't trigger content filters or consume excessive API quota.
