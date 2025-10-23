# PromptVal Usage Guide

This guide provides detailed examples of how to use PromptVal as both a CLI tool and Python package.

## 📦 Installation

### Option 1: Install from PyPI (when published)
```bash
pip install promptval
```

### Option 2: Install from source
```bash
git clone https://github.com/mramanindia/PromptVal.git
cd PromptVal
pip install -e .
```

### Option 3: Install with specific LLM providers
```bash
# Install with OpenAI support
pip install promptval[openai]

# Install with all providers
pip install promptval[all]

# Install for development
pip install promptval[dev]
```

## 🔧 Configuration

### Environment Variables

Set up your API keys and configuration:

```bash
# Required: Set at least one API key
export OPENAI_API_KEY="your_openai_key_here"
# OR
export ANTHROPIC_API_KEY="your_anthropic_key_here"
# OR  
export GOOGLE_API_KEY="your_google_key_here"

# Optional: Override default settings
export PROMPTVAL_PROVIDER="openai"
export PROMPTVAL_MODEL="gpt-4o-mini"
export PROMPTVAL_TEMPERATURE="0.1"
export PROMPTVAL_TIMEOUT="30.0"
```

## 🖥️ CLI Usage

### Basic Commands

**Scan a directory of prompts:**
```bash
promptval scan ./my_prompts
```

**Scan with JSON report:**
```bash
promptval scan ./my_prompts --report-json report.json
```

**Apply fixes automatically:**
```bash
promptval scan ./my_prompts --fix --out-dir ./corrected
```

**Analyze a single prompt:**
```bash
promptval prompt --text "Write a story about a cat"
promptval prompt --file my_prompt.txt
```

### Advanced CLI Options

**Use specific provider:**
```bash
promptval scan ./prompts --provider anthropic --model claude-3-sonnet-20240229
```

**Use OpenAI-compatible API:**
```bash
promptval scan ./prompts --provider openai_compatible --base-url http://localhost:11434/v1
```

**Offline mode (PII detection only):**
```bash
promptval scan ./prompts --no-llm
```

**In-place editing with backup:**
```bash
promptval scan ./prompts --fix --in-place
```

## 🐍 Python Package Usage

### Basic Analysis

```python
from promptval import analyze_prompt

# Analyze a single prompt
result = analyze_prompt("Your prompt text here")
print(f"Score: {result['score']}/100")
print(f"Issues: {len(result['issues'])}")
```

### Directory Validation

```python
from promptval.api import validate_directory, apply_fixes

# Validate all .txt files in a directory
results = validate_directory("./prompts", use_llm=True)

# Print summary
for result in results:
    print(f"{result.file_path}: {result.score}/100")

# Apply fixes
apply_fixes(results, out_dir="./corrected")
```

### Custom Configuration

```python
from promptval import analyze_prompt, PromptValConfig

# Create custom configuration
config = PromptValConfig(
    provider="openai",
    model="gpt-4o-mini",
    temperature=0.1,
    timeout=30.0
)

# Use with analysis
result = analyze_prompt("Your prompt", config)
```

### Working with Results

```python
from promptval.api import validate_file

# Validate a single file
result = validate_file("prompt.txt")

# Check if there are errors
if result.has_errors:
    print("Critical issues found!")

# Access individual issues
for issue in result.issues:
    print(f"Type: {issue.type}")
    print(f"Severity: {issue.severity}")
    print(f"Message: {issue.message}")
    print(f"Suggestion: {issue.suggestion}")
    print(f"Location: {issue.span}")
```

## 🔍 Understanding Results

### Score Calculation
- **100**: Perfect prompt with no issues
- **70-99**: Good prompt with minor issues
- **50-69**: Moderate issues that should be addressed
- **0-49**: Significant issues requiring attention

### Issue Types
- **`redundancy`**: Repetitive or unnecessary content
- **`conflict`**: Contradictory instructions
- **`completeness`**: Missing required sections
- **`pii`**: Personal information or secrets detected

### Severity Levels
- **`error`**: Critical issues (-30 points)
- **`warning`**: Important issues (-10 points)  
- **`info`**: Suggestions for improvement (-5 points)

## 🛡️ PII Detection

PromptVal automatically detects and redacts:

- **Email addresses**: `user@example.com`
- **Phone numbers**: `(555) 123-4567`
- **Credit cards**: `4111-1111-1111-1111`
- **API keys**: `sk-1234567890abcdef`
- **SSNs**: `123-45-6789`
- **IP addresses**: `192.168.1.1`
- **Private keys**: `-----BEGIN PRIVATE KEY-----`

## 🚀 Advanced Usage

### Custom Provider

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

### Error Handling

```python
from promptval.api import validate_file
from promptval.models import ValidationResult

try:
    result = validate_file("prompt.txt")
    if result.has_errors:
        print("Errors found:", [i.message for i in result.issues if i.severity == "error"])
except Exception as e:
    print(f"Validation failed: {e}")
```

## 🧪 Testing

Run the example script to test your installation:

```bash
python examples/basic_usage.py
```

Run the test suite:

```bash
pytest tests/
```

## ❓ Troubleshooting

### Common Issues

**"No API key found"**
- Set `OPENAI_API_KEY` or another provider's API key
- Use `--no-llm` flag for offline mode

**"Provider not supported"**
- Install the required provider: `pip install promptval[openai]`
- Check provider name spelling

**"Model not found"**
- Verify the model name is correct for your provider
- Check if the model is available in your region

**"Timeout error"**
- Increase timeout: `--timeout 60`
- Check your internet connection
- Verify API key permissions

### Getting Help

- Check the [README.md](README.md) for overview
- Look at [examples/basic_usage.py](examples/basic_usage.py) for code examples
- Run `promptval --help` for CLI options
- Open an issue on GitHub for bugs or feature requests
