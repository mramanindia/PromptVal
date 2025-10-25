# PromptVal

**AI-Powered Prompt Validation and Enhancement Tool**

Transform your raw prompts into professional, compliant, and effective AI instructions with intelligent validation, conflict detection, and automated enhancement.

## 🚀 Quick Start

### Example: From Problematic to Perfect

**Input Prompt:**
```
Write a story about a cat. The story should be exactly 100 words long. 
Also include a comprehensive 5000-word analysis of feline behavior. 
Make sure to include my email: john.doe@example.com
```

**PromptVal Analysis:**
```bash
promptval prompt --text "Write a story about a cat. The story should be exactly 100 words long. Also include a comprehensive 5000-word analysis of feline behavior. Make sure to include my email: john.doe@example.com"
```

**Output:**
```json
{
  "score": 40,
  "issues": [
    {
      "type": "conflict",
      "severity": "error", 
      "message": "Conflicting length requirements: 100 words vs 5000 words",
      "suggestion": "Separate the task into two distinct parts: a short story and a detailed analysis"
    },
    {
      "type": "pii",
      "severity": "error",
      "message": "Personal information (email) included in the prompt",
      "suggestion": "Remove any personal information from the prompt"
    }
  ],
  "fixed_prompt": "Task:\n  Write a story about a cat and provide an analysis of feline behavior.\n\nSuccess Criteria:\n  - The story must be exactly 100 words long\n  - The analysis should be a separate section, with a minimum of 500 words\n\nExamples:\n  - Normal case: A 100-word story about a cat's adventure followed by a brief analysis\n  - Edge case: If the story is about a specific cat breed, ensure the analysis includes behaviors specific to that breed"
}
```

## 📦 Installation

### From PyPI (Recommended)

```bash
# Basic installation
pip install promptval

# Install with specific LLM providers
pip install promptval[openai]        # OpenAI support
pip install promptval[anthropic]     # Anthropic support  
pip install promptval[gemini]        # Google Gemini support
pip install promptval[all]           # All providers

# For development
pip install promptval[dev]
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/mramanindia/PromptVal.git
cd PromptVal

# Install in development mode
pip install -e .

# Install with specific LLM providers
pip install -e ".[openai]"        # OpenAI support
pip install -e ".[anthropic]"     # Anthropic support  
pip install -e ".[gemini]"        # Google Gemini support
pip install -e ".[all]"           # All providers

# For development
pip install -e ".[dev]"
```

## 🎯 Core Capabilities

### 1. **Intelligent Issue Detection**
- **🔍 Redundancy Detection**: Identifies repetitive or unnecessary instructions
- **⚔️ Conflict Resolution**: Detects contradictory requirements and impossible constraints
- **📋 Completeness Analysis**: Ensures essential sections are present (Task, Success Criteria, Examples, CoT/ToT guidance)
- **🛡️ PII & Security**: Automatically detects and redacts sensitive information

### 2. **Multi-Provider AI Enhancement**
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Anthropic**: Claude-3.5-Sonnet, Claude-3-Haiku, Claude-3-Opus
- **Google Gemini**: Gemini-1.5-Pro, Gemini-1.5-Flash
- **OpenAI-Compatible**: Any OpenAI-compatible API (local models, custom endpoints)

### 3. **Comprehensive Scoring System**
- **100 points**: Perfect prompt with no issues
- **70-99 points**: Good prompt with minor suggestions
- **50-69 points**: Moderate issues requiring attention
- **0-49 points**: Significant issues that must be addressed

### 4. **Multiple Interfaces**
- **CLI Tool**: Command-line interface for batch processing
- **Python API**: Programmatic integration for applications
- **Interactive Mode**: Step-by-step validation with user confirmation

## 🔧 Usage

### Command Line Interface

**Analyze a single prompt:**
```bash
# Set your API key
export OPENAI_API_KEY=your_key_here

# Analyze text directly
promptval prompt --text "Your prompt here"

# Analyze from file
promptval prompt --file prompt.txt

# Use specific model
promptval prompt --text "Your prompt" --model "gpt-4o"
```

**Process multiple files:**
```bash
# Scan directory with report
promptval scan ./prompts --report-json report.json

# Apply fixes automatically
promptval scan ./prompts --fix --out-dir ./corrected

# Interactive validation
promptval validate ./prompts --report-json report.json

# Auto-apply without confirmation
promptval validate ./prompts --yes
```

**Use different providers:**
```bash
# Anthropic Claude
promptval scan ./prompts --provider anthropic --model claude-3-5-sonnet-latest

# Google Gemini
promptval scan ./prompts --provider gemini --model gemini-1.5-pro

# OpenAI-compatible (local model)
promptval scan ./prompts --provider openai_compatible --base-url http://localhost:11434/v1
```

### Python API

**Basic analysis:**
```python
from promptval import analyze_prompt

# Analyze a single prompt
result = analyze_prompt("Your prompt text here")
print(f"Score: {result['score']}/100")
print(f"Issues: {len(result['issues'])}")

# Access detailed results
for issue in result['issues']:
    print(f"- {issue['type'].upper()}: {issue['message']}")
    print(f"  Suggestion: {issue['suggestion']}")
```

**Directory processing:**
```python
from promptval.api import validate_directory, apply_fixes

# Validate all .txt files in directory
results = validate_directory("./prompts", use_llm=True)

# Print summary
for result in results:
    print(f"{result.file_path}: {result.score}/100")

# Apply fixes
apply_fixes(results, out_dir="./corrected")
```

**Custom configuration:**
```python
from promptval import analyze_prompt, PromptValConfig

# Configure specific provider and settings
config = PromptValConfig(
    provider="openai",
    model="gpt-4o-mini",
    temperature=0.1,
    timeout=30.0
)

result = analyze_prompt("Your prompt", config)
```

## 🔍 Validation Rules

### Issue Types

| Type | Description | Example |
|------|-------------|---------|
| **`redundancy`** | Repetitive or unnecessary content | "Write a story. Create a narrative. Tell a tale." |
| **`conflict`** | Contradictory instructions | "Write exactly 100 words" + "Write at least 500 words" |
| **`completeness`** | Missing required sections | No success criteria or examples provided |
| **`pii`** | Personal information detected | Email addresses, phone numbers, API keys |

### Severity Levels

| Level | Points Deducted | Description |
|-------|----------------|-------------|
| **`error`** | -30 | Critical issues that must be fixed |
| **`warning`** | -10 | Important issues that should be addressed |
| **`info`** | -5 | Suggestions for improvement |

### PII Detection Patterns

PromptVal automatically detects and redacts:

- **Personal Information**: Email addresses, phone numbers, SSNs
- **API Keys**: OpenAI, AWS, Google, GitHub, Slack, Stripe tokens
- **Credentials**: Private keys, JWT tokens, bearer tokens
- **Financial Data**: Credit card numbers, IBAN numbers
- **Network Data**: IPv4/IPv6 addresses
- **Generic Patterns**: Passwords, tokens, sensitive identifiers

## ⚙️ Configuration

### Environment Variables

```bash
# Provider selection
export PROMPTVAL_PROVIDER=openai
export PROMPTVAL_MODEL=gpt-4o-mini
export PROMPTVAL_BASE_URL=https://api.openai.com/v1
export PROMPTVAL_TIMEOUT=30.0
export PROMPTVAL_TEMPERATURE=0.0

# Provider API keys
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export GOOGLE_API_KEY=your_key_here
```

### Supported Providers

| Provider | Models | Installation | API Key |
|----------|--------|--------------|---------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | `pip install promptval[openai]` | `OPENAI_API_KEY` |
| **Anthropic** | claude-3-5-sonnet-latest, claude-3-haiku, claude-3-opus | `pip install promptval[anthropic]` | `ANTHROPIC_API_KEY` |
| **Google Gemini** | gemini-1.5-pro, gemini-1.5-flash | `pip install promptval[gemini]` | `GOOGLE_API_KEY` |
| **OpenAI-Compatible** | Any OpenAI-compatible API | `pip install promptval[openai]` | Provider-specific |

## 📊 Output Format

### Validation Result Structure

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
    "fixed_prompt": "Enhanced prompt with all issues resolved...",
    "provider": {
        "name": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "timeout": 30.0
    }
}
```

### CLI Output

```
                  PromptVal Report: ./prompts                  
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
┃ File                           ┃ Issues ┃ Errors ┃ Warnings ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
│ prompt1.txt                    │ 2      │ 1      │ 1        │
│ prompt2.txt                    │ 0      │ 0      │ 0        │
│ prompt3.txt                    │ 3      │ 2      │ 1        │
└────────────────────────────────┴────────┴────────┴──────────┘
```

## 🛠️ Development

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

### Setup Development Environment

```bash
git clone https://github.com/mramanindia/PromptVal.git
cd PromptVal
pip install -e ".[dev]"
```

## 🚀 Advanced Features

### Offline Mode

When LLM is not available, PromptVal falls back to:
- PII detection and redaction using regex patterns
- Basic prompt structuring and formatting
- Chain of Thought detection and addition
- Compliance framework enforcement

```python
# Force offline mode
from promptval.api import validate_file
result = validate_file("prompt.txt", use_llm=False)
```

### Custom Provider Integration

```python
from promptval.llm.provider import ProviderFactory

# Create custom provider
provider = ProviderFactory.create_provider(
    provider_type="openai_compatible",
    model="custom-model",
    api_key="your_key",
    base_url="https://your-api.com/v1"
)
```

### Batch Processing

```python
import os
from pathlib import Path
from promptval.api import validate_file

# Process multiple files
prompt_files = Path("./prompts").glob("*.txt")
results = []

for file_path in prompt_files:
    result = validate_file(str(file_path))
    results.append(result)
    print(f"Processed {file_path.name}: {result.score}/100")
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

**Need help?** Check out the [examples](examples/) directory for usage examples or open an issue on GitHub.