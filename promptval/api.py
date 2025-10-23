from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import ValidationResult
from .rules import run_all_rules, generate_fixed_text, analyze_and_fix


class PromptValConfig:
	"""Runtime configuration for provider/model and generation params.

	Values map to environment variables consumed by provider selection.
	"""
	def __init__(
		self,
		*,
		provider: Optional[str] = None,
		model: Optional[str] = None,
		base_url: Optional[str] = None,
		timeout: Optional[float] = None,
		temperature: Optional[float] = None,
	) -> None:
		self.provider = provider
		self.model = model
		self.base_url = base_url
		self.timeout = timeout
		self.temperature = temperature


def validate_file(file_path: str, use_llm: bool = True) -> ValidationResult:
	"""Validate a single prompt file.

	Args:
		file_path: Path to a text prompt file (typically `.txt`). The extension is not enforced.
		use_llm: Controls whether LLM-assisted checks are allowed. Current built-in rules are heuristic-only and ignore this flag.

	Returns:
		ValidationResult containing all detected issues for the file.
	"""
	path = Path(file_path)
	text = path.read_text(encoding="utf-8")
	issues = run_all_rules(text=text, file_path=str(path), use_llm=use_llm)
	return ValidationResult(file_path=str(path), issues=issues)


def validate_directory(directory_path: str, use_llm: bool = True) -> List[ValidationResult]:
	"""Validate all `.txt` prompt files under a directory (recursive).

	Args:
		directory_path: Root directory to search for `.txt` files.
		use_llm: Controls whether LLM-assisted checks are allowed. Current built-in rules are heuristic-only and ignore this flag.

	Returns:
		List of ValidationResult, one per file.
	"""
	dir_path = Path(directory_path)
	files = sorted(p for p in dir_path.rglob("*.txt") if p.is_file())
	results: List[ValidationResult] = []
	for file in files:
		results.append(validate_file(str(file), use_llm=use_llm))
	return results


def apply_fixes(results: List[ValidationResult], out_dir: Optional[str] = "corrected") -> None:
	"""Apply suggested fixes to files and write outputs.

	Args:
		results: Validation results produced by the validators.
		out_dir: Output directory. If None, files are overwritten in place (expect backups to be handled by caller).
	"""
	# Generate LLM-fixed prompt text and write to output files via provider-based rules
	for res in results:
		path = Path(res.file_path)
		original_text = path.read_text(encoding="utf-8")
		fixed_text = generate_fixed_text(original_text)
		# Write only the corrected text as requested
		if out_dir is None:
			path.write_text(fixed_text, encoding="utf-8")
		else:
			out = Path(out_dir)
			out.mkdir(parents=True, exist_ok=True)
			target_path = out / path.name
			target_path.write_text(fixed_text, encoding="utf-8")


def _compute_score(issues: List[Dict[str, Any]]) -> int:
	"""Heuristic score 0..100 based on issue severities.

	- start 100; error -30, warning -10, info -5; clamp to [0,100]
	"""
	if issues is None:
		return 100
	
	penalty = 0
	for it in issues:
		sev = str(it.get("severity") or "").lower()
		if sev == "error":
			penalty += 30
		elif sev == "warning":
			penalty += 10
		elif sev == "info":
			penalty += 5
	return max(0, min(100, 100 - penalty))


def analyze_prompt(text: str, config: Optional[PromptValConfig] = None) -> Dict[str, Any]:
	"""Analyze a single prompt and return JSON-friendly dict.

	Output keys:
	- fixed_prompt: str
	- issues: list of dicts
	- score: int (0..100)
	- provider: metadata dict
	"""
	# Apply config to env for provider selection (lazy dependency on CLI helper avoided here)
	import os
	if config is not None:
		if config.provider:
			os.environ["PROMPTVAL_PROVIDER"] = config.provider
		if config.model:
			os.environ["PROMPTVAL_MODEL"] = config.model
		if config.base_url:
			os.environ["PROMPTVAL_BASE_URL"] = config.base_url
		if config.timeout is not None:
			os.environ["PROMPTVAL_TIMEOUT"] = str(config.timeout)
		if config.temperature is not None:
			os.environ["PROMPTVAL_TEMPERATURE"] = str(config.temperature)

	data = analyze_and_fix(text)
	issues = data.get("issues") or []
	fixed = data.get("fixed_text") or text
	# Prefer provider score if present; otherwise heuristic
	try:
		provider_score = data.get("score")
		score = int(round(float(provider_score))) if provider_score is not None else _compute_score(issues)
	except Exception:
		score = _compute_score(issues)

	provider_meta = {
		"name": os.getenv("PROMPTVAL_PROVIDER") or "openai",
		"model": os.getenv("PROMPTVAL_MODEL"),
		"temperature": _safe_float(os.getenv("PROMPTVAL_TEMPERATURE")),
		"timeout": _safe_float(os.getenv("PROMPTVAL_TIMEOUT")),
		"base_url_set": bool(os.getenv("PROMPTVAL_BASE_URL")),
	}

	return {
		"fixed_prompt": fixed,
		"issues": issues,
		"score": score,
		"provider": provider_meta,
	}


def _safe_float(val: Optional[str]) -> Optional[float]:
	try:
		return float(val) if val not in (None, "") else None
	except Exception:
		return None