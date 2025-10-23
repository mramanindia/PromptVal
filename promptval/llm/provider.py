from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable


class LLMProvider(ABC):
	@abstractmethod
	def evaluate_prompt(self, text: str) -> Dict[str, Any]:
		"""Return structured analysis using LLM.

		Expected schema:
		{
		  "issues": [
		    {"type": "redundancy|conflict|completeness|pii", "severity": "info|warning|error", "message": str, "suggestion": str|None, "span": [start, end]|None}
		  ],
		  "fixed_text": str
		}
		"""
		raise NotImplementedError


class ProviderRegistry:
	_registry: Dict[str, Callable[..., LLMProvider]] = {}

	@classmethod
	def register(cls, name: str, factory: Callable[..., LLMProvider]) -> None:
		cls._registry[name.lower()] = factory

	@classmethod
	def create(
		cls,
		name: str,
		*,
		model: Optional[str] = None,
		base_url: Optional[str] = None,
		timeout: Optional[float] = None,
		temperature: Optional[float] = None,
		**extra: Any,
	) -> LLMProvider:
		key = (name or "").lower()
		if key not in cls._registry:
			raise ValueError(f"Unknown provider: {name}")
		return cls._registry[key](model=model, base_url=base_url, timeout=timeout, temperature=temperature, **extra)


class ProviderFactory:
	@staticmethod
	def from_env(
		provider_name: Optional[str] = None,
		model: Optional[str] = None,
		base_url: Optional[str] = None,
		timeout: Optional[float] = None,
		temperature: Optional[float] = None,
	) -> LLMProvider:
		name = (provider_name or os.getenv("PROMPTVAL_PROVIDER") or "openai").lower()
		mdl = model or os.getenv("PROMPTVAL_MODEL") or None
		base = base_url or os.getenv("PROMPTVAL_BASE_URL") or None
		to_val: Optional[float] = timeout if timeout is not None else _parse_float(os.getenv("PROMPTVAL_TIMEOUT"))
		temp_val: Optional[float] = temperature if temperature is not None else _parse_float(os.getenv("PROMPTVAL_TEMPERATURE"))

		# Ensure provider-specific API keys exist before creating
		if name == "openai":
			if not os.getenv("OPENAI_API_KEY"):
				raise RuntimeError("OPENAI_API_KEY not set in environment")
			from .providers.openai_provider import OpenAIProvider
			return OpenAIProvider(model=mdl)

		if name == "openai_compatible":
			from .providers.openai_compatible import OpenAICompatibleProvider
			return OpenAICompatibleProvider(model=mdl, base_url=base, timeout=to_val, temperature=temp_val)

		if name == "anthropic":
			from .providers.anthropic_provider import AnthropicProvider
			return AnthropicProvider(model=mdl, timeout=to_val, temperature=temp_val)

		if name == "gemini":
			from .providers.gemini_provider import GeminiProvider
			return GeminiProvider(model=mdl, timeout=to_val, temperature=temp_val)

		if name == "xai":
			# Prefer native provider if available; otherwise route through openai_compatible with base_url
			try:
				from .providers.xai_provider import XAIProvider  # type: ignore
				return XAIProvider(model=mdl, timeout=to_val, temperature=temp_val)
			except Exception:
				from .providers.openai_compatible import OpenAICompatibleProvider
				return OpenAICompatibleProvider(model=mdl, base_url=base or os.getenv("XAI_BASE_URL"), timeout=to_val, temperature=temp_val)

		raise ValueError(f"Unknown provider: {name}")


def _parse_float(val: Optional[str]) -> Optional[float]:
	try:
		return float(val) if val is not None and val != "" else None
	except Exception:
		return None


