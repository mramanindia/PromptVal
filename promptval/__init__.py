"""PromptVal package initialization."""

from .api import analyze_prompt, PromptValConfig

__all__ = [
	"__version__",
	"analyze_prompt",
	"PromptValConfig",
]

__version__ = "0.1.0"