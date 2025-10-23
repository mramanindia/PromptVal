from __future__ import annotations

import json
from typing import Any, Dict, Optional
import time

try:
	from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
	OpenAI = None  # type: ignore

from ..prompts import SYSTEM_PROMPT
import os


class OpenAIProvider:
	def __init__(self, model: Optional[str] = None, *, timeout: Optional[float] = None, temperature: Optional[float] = 0.0) -> None:
		if OpenAI is None:
			raise RuntimeError("openai package not installed. Install with extras: pip install .[openai]")
		self.model = model or "gpt-4o-mini"
		# Pass timeout to client if provided
		if timeout is not None:
			try:
				self.client = OpenAI(timeout=timeout)
			except Exception:
				self.client = OpenAI()
		else:
			self.client = OpenAI()
		self.temperature = 0.0 if temperature is None else float(temperature)
		self.timeout = timeout

	def evaluate_prompt(self, text: str) -> Dict[str, Any]:
		prompt = (
			"PROMPT TO REVIEW (PII-REDACTED):\n" + text + "\n\n" + "Respond with JSON only."
		)
		content = "{}"
		retries = 3
		backoff_s = 1.0
		for attempt in range(1, retries + 1):
			try:
				if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
					print(f"[promptval][debug] openai.create attempt={attempt} model={self.model} temp={self.temperature}")
				resp = self.client.chat.completions.create(
					model=self.model,
					messages=[
						{"role": "system", "content": SYSTEM_PROMPT},
						{"role": "user", "content": prompt},
					],
					temperature=self.temperature,
					timeout=self.timeout,
				)
				content = resp.choices[0].message.content or "{}"
				break
			except Exception as e:
				if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
					print(f"[promptval][debug] openai error attempt={attempt}: {type(e).__name__}: {e}")
					import traceback
					print(f"[promptval][debug] traceback: {traceback.format_exc()}")
				if attempt < retries:
					time.sleep(backoff_s)
					backoff_s *= 2
		try:
			data = _parse_json_payload(content)
		except Exception as e:
			if (os.getenv("PROMPTVAL_DEBUG") or "").strip() not in {"", "0", "false", "False"}:
				print(f"[promptval][debug] openai json error: {e}; content snippet={content[:200]}")
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

