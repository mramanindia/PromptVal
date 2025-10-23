# PromptVal

**AI-Powered Prompt Validation and Enhancement Tool**

PromptVal is a comprehensive Python package and CLI tool that validates, analyzes, and enhances prompt files. It detects issues like redundancy, conflicts, missing strategy sections, and PII/secrets, then uses AI to generate improved, compliant prompts.

## ✨ Features

- **🔍 Smart Validation**: Detects redundant instructions, conflicting requirements, and missing strategy sections
- **🛡️ PII Protection**: Automatically identifies and redacts personal information, API keys, and secrets
- **🤖 AI Enhancement**: Uses multiple LLM providers (OpenAI, Anthropic, Google Gemini, X.ai Grok) to fix and improve prompts
- **📊 Comprehensive Scoring**: Provides detailed scoring and issue categorization
- **🔧 Multiple Interfaces**: CLI tool, Python API, and programmatic usage
- **⚡ Offline Fallback**: Works without LLM when needed, focusing on PII redaction and basic formatting

## 🚀 Installation

### Basic Installation

```bash
pip install promptval
```

### With LLM Provider Support

```bash
# Install with specific provider
pip install promptval[openai]        # OpenAI support
pip install promptval[anthropic]     # Anthropic support  
pip install promptval[gemini]        # Google Gemini support
pip install promptval[all]           # All providers

# For development
pip install promptval[dev]
```

## 🎯 Quick Start

### CLI Usage

**Scan and validate prompts in a directory:**

```bash
# Basic validation (requires API key)
export OPENAI_API_KEY=your_key_here
promptval scan ./prompts --report-json report.json

# Apply fixes automatically
promptval scan ./prompts --fix --out-dir ./corrected

# Use different provider
promptval scan ./prompts --provider anthropic --model claude-3-sonnet-20240229

# Offline mode (PII redaction only)
promptval scan ./prompts --no-llm
```

**Analyze a single prompt:**

```bash
# From text
promptval prompt --text "Your prompt here"

# From file
promptval prompt --file prompt.txt
```

### Python API Usage

**Basic validation:**

```python
from promptval import analyze_prompt, PromptValConfig

# Analyze a single prompt
result = analyze_prompt("Your prompt text here")
print(f"Score: {result['score']}")
print(f"Issues: {len(result['issues'])}")

# With custom configuration
config = PromptValConfig(
    provider="openai",
    model="gpt-4o-mini",
    temperature=0.1
)
result = analyze_prompt("Your prompt", config)
```

**Directory validation:**

```python
from promptval.api import validate_directory, apply_fixes

# Validate all .txt files in directory
results = validate_directory("./prompts", use_llm=True)

# Apply fixes to corrected files
apply_fixes(results, out_dir="./corrected")
```

**Advanced usage with provider selection:**

```python
from promptval.api import validate_file
from promptval.llm.provider import ProviderFactory

# Configure provider
provider = ProviderFactory.create_provider(
    provider_type="openai",
    model="gpt-4o-mini",
    api_key="your_key_here"
)

# Validate with specific provider
result = validate_file("prompt.txt", use_llm=True)
```

## 🔧 Configuration

### Environment Variables

Set these environment variables for automatic configuration:

```bash
# Provider selection
export PROMPTVAL_PROVIDER=openai
export PROMPTVAL_MODEL=gpt-4o-mini
export PROMPTVAL_BASE_URL=https://api.openai.com/v1  # For OpenAI-compatible
export PROMPTVAL_TIMEOUT=30.0
export PROMPTVAL_TEMPERATURE=0.0

# Provider API keys
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export GOOGLE_API_KEY=your_key_here
export XAI_API_KEY=your_key_here
```

### Supported Providers

| Provider | Models | Installation |
|----------|--------|--------------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | `pip install promptval[openai]` |
| **Anthropic** | claude-3-opus, claude-3-sonnet, claude-3-haiku | `pip install promptval[anthropic]` |
| **Google Gemini** | gemini-pro, gemini-pro-vision | `pip install promptval[gemini]` |
| **X.ai Grok** | grok-beta | `pip install promptval[all]` |
| **OpenAI-Compatible** | Any OpenAI-compatible API | `pip install promptval[openai]` |

## 📋 Validation Rules

PromptVal checks for:

### 1. **Redundancy Detection**
- Identifies repetitive or unnecessary instructions
- Suggests consolidation of similar requirements

### 2. **Conflict Resolution**
- Detects contradictory instructions
- Flags impossible or conflicting requirements

### 3. **Completeness Analysis**
- Ensures presence of essential sections:
  - Clear task description
  - Success criteria
  - Examples (normal and edge cases)
  - Chain of Thought (CoT) or Tree of Thought (ToT) guidance when needed

### 4. **PII & Security**
- Automatically detects and redacts:
  - Email addresses, phone numbers, SSNs
  - API keys and tokens
  - Credit card numbers
  - Private keys and credentials
  - IP addresses and other sensitive data

## 📊 Output Format

### Validation Results

```python
{
    "file_path": "prompt.txt",
    "score": 85,
    "issues": [
        {
            "type": "redundancy",
            "severity": "warning", 
            "message": "Instruction repeated multiple times",
            "suggestion": "Consolidate into single clear instruction",
            "span": [10, 50]
        }
    ],
    "fixed_text": "Enhanced prompt with all issues resolved..."
}
```

### Issue Types
- `redundancy`: Repetitive or unnecessary content
- `conflict`: Contradictory instructions  
- `completeness`: Missing required sections
- `pii`: Personal information or secrets detected

### Severity Levels
- `error`: Critical issues that must be fixed
- `warning`: Important issues that should be addressed
- `info`: Suggestions for improvement

## 🛠️ Development

### Setup Development Environment

```bash
git clone https://github.com/mramanindia/PromptVal.git
cd PromptVal
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=promptval --cov-report=html

# Run specific test categories
pytest tests/test_pii.py          # PII detection tests
pytest tests/test_llm_fix.py      # LLM integration tests (requires API keys)
pytest tests/test_offline_fallback.py  # Offline functionality tests
```

### Project Structure

```
promptval/
├── __init__.py              # Package initialization
├── api.py                   # Main API functions
├── cli.py                   # Command-line interface
├── models.py                # Data models and schemas
├── llm/                     # LLM provider abstraction
│   ├── provider.py          # Provider factory and base classes
│   ├── prompts.py           # System prompts for LLM
│   └── providers/           # Specific provider implementations
│       ├── openai_provider.py
│       ├── anthropic_provider.py
│       ├── gemini_provider.py
│       └── openai_compatible.py
└── rules/                   # Validation rules
    ├── core.py              # Main validation logic
    └── pii.py               # PII detection patterns
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m "Add feature"`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for CLI
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Powered by [Pydantic](https://pydantic.dev/) for data validation
- Supports multiple LLM providers for maximum flexibility

---

**Need help?** Check out the [test files](tests/) for usage examples or open an issue on GitHub.