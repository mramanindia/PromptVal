

## Library API (package usage)

### Quickstart

Initialize the fixer with your provider and configuration. It will locally mask PII before any network call, invoke the LLM to fix/structure the prompt, then return a JSON payload.

```python
from promptval.services import PromptFixer

# Option A: explicit configuration (LLM required)
fixer = PromptFixer(
	provider="openai",              # "anthropic" | "gemini" | "xai" | "openai_compatible"
	model="gpt-4o-mini",            # provider-specific model name
	base_url=None,                   # for openai_compatible servers (e.g., http://localhost:11434/v1)
	timeout=30.0,
	temperature=0.0,
	max_tokens=1024,
	redaction_enabled=True,
)

result = fixer.fix_prompt("raw user prompt text")
print(result["fixed_text"])  # fixed compliant prompt

# Option B: load from environment
# PROMPTVAL_PROVIDER, PROMPTVAL_MODEL, PROMPTVAL_BASE_URL, PROMPTVAL_TIMEOUT, and provider API keys
fixer = PromptFixer.from_env()
```

### Input → Output contract

- Input: a single raw prompt `str`.
- Processing:
  1) Pre-send PII masking (local regex redaction)
  2) Call selected provider/model (LLM is required)
  3) Post-return re-redaction of `fixed_text` and `suggestions`
  4) Minimal compliance formatting (section spacing, optional CoT/TOT gating)
- Output (JSON-like `dict`):

```json
{
  "fixed_text": "...",
  "issues": [
    {
      "type": "redundancy|conflict|completeness|pii",
      "severity": "info|warning|error",
      "message": "...",
      "suggestion": "...",
      "span": [start, end]
    }
  ],
  "meta": {
    "provider": "openai|anthropic|gemini|xai|openai_compatible|null",
    "model": "...",
    "redaction": { "pre_send": true, "post_return": true },
    "fallback": { "used": false, "reason": null }
  }
}
```

### Error handling & privacy

- If the provider SDK/key is missing or an API error occurs, the fixer returns an error with `meta.fallback.used=true` and a descriptive reason; LLM is required.
- The library never logs raw prompts; only redacted snippets may appear in debug.
- Reports and returned `fixed_text` are post-redaction to avoid accidental disclosure.

## Tests

- Core: redaction and PII detections; output schema
- Provider-specific paths: skipped unless SDK+API key present per provider
- Ensure malformed/echoed LLM outputs are re-redacted

## On-the-go prompt fixing (service classes)

### Overview

- Provide a simple high-level API to accept a single prompt and return a fixed, compliant prompt immediately.
- PII masking runs before any LLM call and again after the provider returns.
- Honors privacy settings: local-only if LLM is disabled or provider is unavailable.

### Classes and responsibilities

- `PromptFixer` (orchestrator)
  - Single public surface to fix prompts (sync/async)
  - Invokes `PiiRedactor`, `ProviderClientAdapter`, and `CompliancePostprocessor`
- `PiiRedactor`
  - `redact_pre_send(text) -> redacted_text`
  - `redact_post_return(text_or_suggestion) -> redacted`
- `ProviderClientAdapter`
  - Wraps provider instances from `ProviderRegistry`
  - `evaluate_prompt(text, system_prompt) -> {issues: [...], fixed_text: str}`
- `CompliancePostprocessor`
  - Ensures section spacing, optional CoT/TOT gating, newline normalization
- `ConfigResolver`
  - Merges CLI/env/defaults into a concrete `FixOptions`

### Data flow

1) Receive `text` and `FixOptions`
2) `PiiRedactor.redact_pre_send(text)` -> `redacted_text`
3) If `options.llm_enabled`: `ProviderClientAdapter.evaluate_prompt(redacted_text, system_prompt)` else local-only fallbacks
4) Parse `issues`; pick `fixed_text` (or original on failure)
5) `PiiRedactor.redact_post_return(fixed_text)` and for each `suggestion`
6) `CompliancePostprocessor.ensure_output_compliance(text)`
7) Return `{fixed_text, issues, metadata}`

### Options (shape)

- `redaction_enabled: bool`
- `provider: str | None`
- `model: str | None`
- `base_url: str | None`
- `timeout: float | None`
- `temperature: float | None`, `max_tokens: int | None`
- `redact_suggestions: bool`
Notes:
- LLM is required; omit `llm_enabled` option. If misconfigured, return an error.

### Usage example (conceptual)

```python
from promptval.services import PromptFixer, FixOptions

fixer = PromptFixer()
result = fixer.fix_prompt(
	text=user_prompt,
	options=FixOptions(
		llm_enabled=True,
		redaction_enabled=True,
		provider="openai",
		model="gpt-4o-mini",
		base_url=None,
		timeout=30.0,
	),
)
print(result.fixed_text)
for issue in result.issues:
	print(issue.issue_type, issue.severity, issue.message)
```

Notes:
- Provide `fix_prompt_async(...)` for asyncio workflows.
- Providers are pluggable via the `ProviderRegistry`; adding a new provider requires only a small adapter.

## Tasks checklist

- [ ] Provider registry and interface
- [ ] CLI flags `--provider/--model/--base-url/...` and default `--no-llm`
- [ ] Env var resolution and safe fallbacks
- [ ] Pre/post redaction around LLM
- [ ] Expanded PII patterns + unit tests
- [ ] `--anonymize-paths` for reports
- [ ] Packaging extras and metadata updates
- [ ] README updates: provider matrix, privacy model, examples


