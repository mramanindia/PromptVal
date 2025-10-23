from __future__ import annotations

import json
from typing import Any, Dict, Optional

try:
	import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
	genai = None  # type: ignore

from ..prompts import SYSTEM_PROMPT
import os


class GeminiProvider:
	def __init__(self, model: Optional[str] = None, *, timeout: Optional[float] = None, temperature: Optional[float] = 0.0) -> None:
		if genai is None:
			raise RuntimeError("google-generativeai package not installed. Install with extras: pip install .[gemini]")
		self.model = model or "gemini-1.5-pro"
		genai.configure()
		self.client = genai.GenerativeModel(self.model)
		self.temperature = 0.0 if temperature is None else float(temperature)
		self.timeout = timeout

	def evaluate_prompt(self, text: str) -> Dict[str, Any]:
		prompt = (
			"PROMPT TO REVIEW (PII-REDACTED):\n" + text + "\n\n" + "Respond with JSON only."
		)
		try:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] gemini.generate model={self.model} temp={self.temperature}")
			resp = self.client.generate_content([
				{"role": "user", "parts": [SYSTEM_PROMPT + "\n\n" + prompt]},
			], generation_config={"temperature": self.temperature})
			content = getattr(resp, "text", None) or "{}"
		except Exception as e:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] gemini error: {e}")
			content = "{}"
		try:
			data = _parse_json_payload(content)
		except Exception as e:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] gemini json error: {e}; content snippet={content[:200]}")
			data = {}
		return data


def _parse_json_payload(content: str) -> Dict[str, Any]:
	s = (content or "").strip()
	# Strip markdown fences if present
	if s.startswith("```") and s.endswith("```"):
		# Remove the starting fence line and ending fence
		first_newline = s.find("\n")
		if first_newline != -1:
			head = s[3:first_newline].strip().lower()
			s = s[first_newline + 1 : -3].strip()
			if head == "json":
				# already removed the language tag
				pass
	# Extract JSON object substring
	l = s.find("{")
	r = s.rfind("}")
	if l != -1 and r != -1 and r > l:
		s = s[l : r + 1]
	return json.loads(s)


