# PromptVal

PromptVal is a Python module and CLI to validate and optionally fix a directory of prompt `.txt` files. It detects:

- Redundant instructions
- Conflicting instructions
- Missing strategy sections (Task, Success Criteria, Examples with an edge case, CoT/TOT guidance)
- PII/Secrets

## Install

Requirments:
- Openai_api_key required

```bash
pip3 install -e .
# For dev/test extras on zsh use quotes:
pip3 install -e '.[dev]'
```

## CLI Usage

Interactive validation and optional application of fixes:

```bash
export OPENAI_API_KEY=...  # required for LLM mode
promptval validate ./samples --report-json report.json
# You will be prompted to confirm applying corrections to ./corrected
```

Non-interactive apply (auto-approve):

```bash
promptval validate ./samples --report-json report.json --yes
```

Notes:

- `--llm/--no-llm` toggles LLM usage (on by default). When LLM is disabled or unavailable, only PII redaction and minimal formatting are applied; redundancy/conflict/completeness checks require LLM.
- Corrected files are written to `./corrected` and contain only the LLM-corrected prompt.
- The corrected prompt is multi-line and sectioned: Task, Success Criteria, Examples (Normal/Edge), CoT/TOT, No Secrets/No PII.

## Python API

```python
from promptval.api import validate_directory, apply_fixes

results = validate_directory("./samples")
apply_fixes(results, out_dir="./corrected")
```

## Development

- Python 3.10+
- Install dev deps: `pip install -e '.[dev]'`
- LLM extras: `pip install -e '.[openai]'` and set `OPENAI_API_KEY`.
- Run tests and coverage: `pytest -q --cov=promptval --cov-report=term-missing`.

## Architecture

- LLM provider abstraction in `promptval/llm/provider.py` with `ProviderFactory`.
- OpenAI implementation in `promptval/llm/providers/openai_provider.py` using `promptval/llm/prompts.py`.
- Rule entrypoints in `promptval/rules/core.py` and re-exported from `promptval/rules/__init__.py`.

## License

MIT