from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
	import anthropic  # type: ignore
except Exception:  # pragma: no cover - optional dependency
	anthropic = None  # type: ignore

from ..prompts import SYSTEM_PROMPT
import os


class AnthropicProvider:
	def __init__(self, model: Optional[str] = None, *, timeout: Optional[float] = None, temperature: Optional[float] = 0.0) -> None:
		if anthropic is None:
			raise RuntimeError("anthropic package not installed. Install with extras: pip install .[anthropic]")
		self.model = model or "claude-3-5-sonnet-latest"
		self.client = anthropic.Anthropic()
		self.temperature = 0.0 if temperature is None else float(temperature)
		self.timeout = timeout

	def evaluate_prompt(self, text: str) -> Dict[str, Any]:
		prompt = (
			"PROMPT TO REVIEW (PII-REDACTED):\n" + text + "\n\n" + "Respond with JSON only."
		)
		try:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] anthropic.create model={self.model} temp={self.temperature}")
			resp = self.client.messages.create(
				model=self.model,
				max_tokens=2048,
				temperature=self.temperature,
				messages=[
					{"role": "system", "content": SYSTEM_PROMPT},
					{"role": "user", "content": prompt},
				],
			)
			# Anthropci SDK returns content segments; join to text
			content = "".join([seg.text for seg in (resp.content or []) if getattr(seg, "text", None)]) or "{}"
		except Exception as e:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] anthropic error: {e}")
			content = "{}"
		try:
			data = _parse_json_payload(content)
		except Exception as e:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] anthropic json error: {e}; content snippet={content[:200]}")
			data = {}
		return data


def _parse_json_payload(content: str) -> Dict[str, Any]:
	s = (content or "").strip()
	if s.startswith("```") and s.endswith("```"):
		first_newline = s.find("\n")
		if first_newline != -1:
			head = s[3:first_newline].strip().lower()
			s = s[first_newline + 1 : -3].strip()
			if head == "json":
				pass
	l = s.find("{")
	r = s.rfind("}")
	if l != -1 and r != -1 and r > l:
		s = s[l : r + 1]
	return json.loads(s)


