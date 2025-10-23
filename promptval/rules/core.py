from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import Issue, IssueType, Severity, TextSpan
from ..llm.provider import ProviderFactory
from .pii import PATTERNS as _PII_PATTERNS
import os
import re


def _parse_issue_dict(file_path: str, item: Dict[str, Any]) -> Optional[Issue]:
	try:
		issue_type_raw = str(item.get("type") or item.get("issue_type") or "").strip().lower()
		if issue_type_raw not in {t.value for t in IssueType}:
			return None
		issue_type = IssueType(issue_type_raw)
		severity_raw = str(item.get("severity") or "warning").strip().lower()
		if severity_raw not in {s.value for s in Severity}:
			severity_raw = Severity.warning.value
		severity = Severity(severity_raw)
		message = str(item.get("message") or "").strip() or f"{issue_type.value.capitalize()} detected"
		suggestion = item.get("suggestion")
		span_val = item.get("span") or item.get("range")
		span: Optional[TextSpan] = None
		if isinstance(span_val, (list, tuple)) and len(span_val) == 2:
			try:
				span = TextSpan(start=int(span_val[0]), end=int(span_val[1]))
			except Exception:
				span = None
		return Issue(
			file_path=file_path,
			issue_type=issue_type,
			severity=severity,
			message=message,
			suggestion=str(suggestion) if suggestion is not None else None,
			span=span,
		)
	except Exception:
		return None


def _llm_analyze_and_fix(text: str) -> Dict[str, Any]:
    """Use provider abstraction to analyze and fix prompt text (LLM required)."""
    redacted_text = _local_redact(text)
    provider_name = os.getenv("PROMPTVAL_PROVIDER") or "openai"
    model = os.getenv("PROMPTVAL_MODEL") or None
    base_url = os.getenv("PROMPTVAL_BASE_URL") or None
    timeout = _parse_float(os.getenv("PROMPTVAL_TIMEOUT"))
    temperature = _parse_float(os.getenv("PROMPTVAL_TEMPERATURE"))

    _dbg(f"Provider selection: provider={provider_name}, model={model}, base_url={'set' if base_url else 'unset'}, timeout={timeout}, temperature={temperature}")
    _dbg(f"API keys present: OPENAI={'yes' if os.getenv('OPENAI_API_KEY') else 'no'}, ANTHROPIC={'yes' if os.getenv('ANTHROPIC_API_KEY') else 'no'}, GOOGLE={'yes' if os.getenv('GOOGLE_API_KEY') else 'no'}")

    provider = ProviderFactory.from_env(
        provider_name=provider_name,
        model=model,
        base_url=base_url,
        timeout=timeout,
        temperature=temperature,
    )
    data = provider.evaluate_prompt(redacted_text)
    if not isinstance(data, dict):
        data = {}
    issues = data.get("issues") if isinstance(data.get("issues"), list) else []
    # Allow providers to use alternative keys for the corrected text
    fixed_text_keys = ["fixed_text", "fixed", "corrected_prompt", "output"]
    fixed_text: Optional[str] = None
    for k in fixed_text_keys:
        v = data.get(k)
        if isinstance(v, str) and v.strip() != "":
            fixed_text = v
            break
    # Guard: treat whitespace-only fixed_text as missing and fallback to original
    if isinstance(fixed_text, str) and fixed_text.strip() == "":
        fixed_text = None
    # Optional score provided by model
    score_val = data.get("score")
    try:
        score_norm: Optional[float] = float(score_val) if score_val is not None else None
    except Exception:
        score_norm = None
    # Offline structured fallback when provider fails (no issues and no change)
    try:
        original = text
        use_fallback = (not issues) and (fixed_text is None or _stripped_equal(fixed_text, original))
        if use_fallback:
            fixed_text = _offline_structured_fix(original)
    except Exception:
        pass
    return {"issues": issues, "fixed_text": fixed_text or text, "score": score_norm}


def analyze_and_fix(text: str) -> Dict[str, Any]:
	"""Public API: return issues, fixed_text, and optional score from provider.

	If provider omits score, the caller can compute a heuristic.
	"""
	data = _llm_analyze_and_fix(text)
	return {
		"issues": data.get("issues") or [],
		"fixed_text": data.get("fixed_text") or text,
		"score": data.get("score"),
	}


def _stripped_equal(a: str, b: str) -> bool:
	try:
		return (a or "").strip().replace("\r\n", "\n").replace("\r", "\n") == (b or "").strip().replace("\r\n", "\n").replace("\r", "\n")
	except Exception:
		return False


def _offline_structured_fix(text: str) -> str:
	"""Construct a minimal structured prompt offline (no LLM)."""
	body = (text or "").strip()
	length_rules: List[str] = []
	try:
		m1 = re.findall(r"no\s+longer\s+than\s+(\d+)\s+words", body, flags=re.IGNORECASE)
		for n in m1:
			length_rules.append(f"Response must be no more than {n} words")
		m2 = re.findall(r"exactly\s+(\d+)\s+words", body, flags=re.IGNORECASE)
		for n in m2:
			length_rules.append(f"Response must be exactly {n} words")
	except Exception:
		pass

	lines: List[str] = []
	lines.append("Task:")
	lines.append(f"  {body}")
	lines.append("")
	lines.append("Success Criteria:")
	lines.append("  - Follow the instructions in Task")
	for rule in length_rules:
		lines.append(f"  - {rule}")
	lines.append("  - Do not include secrets or PII")
	lines.append("")
	lines.append("Examples:")
	lines.append("  - Normal Example: Provide a clear, concise answer")
	lines.append("  - Edge Case: Handle minimal or ambiguous input gracefully")
	lines.append("")
	lines.append("No Secrets / No PII:")
	lines.append("  Do not include personal information, credentials, or confidential data.")

	structured = "\n".join(lines)
	return _ensure_output_compliance(structured)


def run_all_rules(text: str, file_path: str, use_llm: bool = True) -> List[Issue]:
	issues: List[Issue] = []
	data = _llm_analyze_and_fix(text)
	for raw in data.get("issues", []) or []:
		if not isinstance(raw, dict):
			continue
		iss = _parse_issue_dict(file_path, raw)
		if iss is not None:
			issues.append(iss)
	return issues


def check_redundancy(text: str, file_path: str, use_llm: bool = True) -> List[Issue]:
	data = _llm_analyze_and_fix(text)
	issues: List[Issue] = []
	for raw in data.get("issues", []) or []:
		if isinstance(raw, dict) and str(raw.get("type", "")).lower() == IssueType.redundancy.value:
			iss = _parse_issue_dict(file_path, raw)
			if iss is not None:
				issues.append(iss)
	return issues


def check_conflict(text: str, file_path: str, use_llm: bool = True) -> List[Issue]:
	data = _llm_analyze_and_fix(text)
	issues: List[Issue] = []
	for raw in data.get("issues", []) or []:
		if isinstance(raw, dict) and str(raw.get("type", "")).lower() == IssueType.conflict.value:
			iss = _parse_issue_dict(file_path, raw)
			if iss is not None:
				issues.append(iss)
	return issues


def check_completeness(text: str, file_path: str, use_llm: bool = True) -> List[Issue]:
	data = _llm_analyze_and_fix(text)
	issues: List[Issue] = []
	for raw in data.get("issues", []) or []:
		if isinstance(raw, dict) and str(raw.get("type", "")).lower() == IssueType.completeness.value:
			iss = _parse_issue_dict(file_path, raw)
			if iss is not None:
				issues.append(iss)
	return issues


def check_pii_llm(text: str, file_path: str, use_llm: bool = True) -> List[Issue]:
	data = _llm_analyze_and_fix(text)
	issues: List[Issue] = []
	for raw in data.get("issues", []) or []:
		if isinstance(raw, dict) and str(raw.get("type", "")).lower() == IssueType.pii.value:
			iss = _parse_issue_dict(file_path, raw)
			if iss is not None:
				issues.append(iss)
	return issues


def generate_fixed_text(text: str) -> str:
	"""Return the LLM-generated fixed text for the provided prompt.

	If the provider fails, returns the original text.
	"""
	fixed = _llm_analyze_and_fix(text).get("fixed_text") or text
	return _ensure_output_compliance(fixed)


def _ensure_output_compliance(text: str) -> str:
	"""Ensure the fixed output is minimal, redact residual PII, and add CoT only when needed."""
	clean = _local_redact((text or "").strip())
	clean = clean.replace("\r\n", "\n").replace("\r", "\n").strip()

	# Keep simple math/keyword detection just to prepend the hint; not a heuristic rule output
	regex_signals = [r"[0-9]\s*[*×/\+\-]\s*[0-9]"]
	keyword_signals = [
		"^", "sqrt", "log", "ln", "sum(", "product(",
		"step by step", "chain of thought", "tree of thought", "plan the steps", "outline steps",
	]
	needs_cot = (
		any(re.search(pat, clean, re.IGNORECASE) for pat in regex_signals)
		or any(kw in clean.lower() for kw in keyword_signals)
	)

	if needs_cot and not re.search(r"think\s+step\s+by\s+step", clean, re.IGNORECASE):
		clean = "Think step by step\n" + clean

	# Ensure blank line separation before common section headers
	clean = _ensure_section_spacing(clean)

	return clean + ("\n" if not clean.endswith("\n") else "")


def _local_redact(text: str) -> str:
	"""Apply local PII regex redaction before sending to LLM."""
	redacted = text
	for _name, pat in _PII_PATTERNS:
		redacted = pat.sub("[REDACTED]", redacted)
	return redacted


def _ensure_section_spacing(text: str) -> str:
	"""Insert a blank line before common section headers if missing.

	Headers considered (case-insensitive):
	- Task:
	- Success Criteria:
	- Examples:
	- CoT/TOT:
	- No Secrets / No PII:
	"""
	patterns = [
		r"(?mi)\n(\s*task\s*:)",
		r"(?mi)\n(\s*success\s*criteria\s*:)",
		r"(?mi)\n(\s*examples?(?:\s*with\s*edge\s*cases)?\s*:)",
		r"(?mi)\n(\s*(?:cot|chain\s*of\s*thought|tot|tree\s*of\s*thought)\s*:)",
		r"(?mi)\n(\s*no\s*secrets\s*/\s*no\s*pii\s*:)",
	]
	result = text
	for pat in patterns:
		# If there is exactly one newline before a header, make it two
		result = re.sub(pat, "\n\n\\1", result)
	return result


def _parse_float(val: Optional[str]) -> Optional[float]:
    try:
        return float(val) if val is not None and val != "" else None
    except Exception:
        return None


def _debug_enabled() -> bool:
    try:
        return str(os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}
    except Exception:
        return False


def _dbg(msg: str) -> None:
    if _debug_enabled():
        try:
            print(f"[promptval][debug] {msg}")
        except Exception:
            pass

