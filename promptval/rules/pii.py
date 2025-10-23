from __future__ import annotations

import re
from typing import List

from ..models import Issue, IssueType, Severity, TextSpan


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:(?:\+\d{1,3}[ -]?)?(?:\(\d{1,4}\)[ -]?)?\d{3,4}[ -]?\d{3,4}[ -]?\d{3,4})")
CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
OPENAI_KEY = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
AWS_ACCESS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
AWS_SECRET_KEY = re.compile(r"\b[0-9A-Za-z/+]{40}\b")
PASSWORD_HINT = re.compile(r"password\s*[:=]", re.IGNORECASE)
TOKEN_HINT = re.compile(r"(api|access|secret|bearer)\s*token", re.IGNORECASE)

# Additional secrets/tokens
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP) PRIVATE KEY-----[\s\S]*?-----END .*? PRIVATE KEY-----", re.IGNORECASE)
JWT = re.compile(r"\b[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b")
GITHUB_PAT = re.compile(r"\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})\b")
SLACK_TOKEN = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]+\b")
STRIPE_KEY = re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{24,}\b")
GOOGLE_API_KEY = re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")
GENERIC_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9\-\._~\+\/]+=*\b", re.IGNORECASE)
IBAN = re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b")
IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")
IPV6 = re.compile(r"\b([0-9a-f]{1,4}:){7}[0-9a-f]{1,4}\b", re.IGNORECASE)


PATTERNS = [
	("email", EMAIL),
	("phone", PHONE),
	("credit_card", CREDIT_CARD),
	("ssn", SSN),
	("openai_key", OPENAI_KEY),
	("aws_access_key", AWS_ACCESS_KEY),
	("aws_secret_key", AWS_SECRET_KEY),
	("password_hint", PASSWORD_HINT),
	("token_hint", TOKEN_HINT),
	("private_key", PRIVATE_KEY),
	("jwt", JWT),
	("github_pat", GITHUB_PAT),
	("slack_token", SLACK_TOKEN),
	("stripe_key", STRIPE_KEY),
	("google_api_key", GOOGLE_API_KEY),
	("bearer_token", GENERIC_BEARER),
	("iban", IBAN),
	("ipv4", IPV4),
	("ipv6", IPV6),
]


def _find_spans(pattern: re.Pattern, text: str) -> List[TextSpan]:
	spans: List[TextSpan] = []
	for m in pattern.finditer(text):
		spans.append(TextSpan(start=m.start(), end=m.end()))
	return spans


def check_pii(text: str, file_path: str, use_llm: bool = False) -> List[Issue]:
	"""Detect likely PII and secrets using regex patterns.

	Matches emails, phone numbers, credit cards, SSNs, API keys/tokens, and related hints.
	Every match is reported as an error with a suggested redaction.

	`use_llm` is accepted for API consistency but is currently unused.
	"""
	issues: List[Issue] = []
	for name, pat in PATTERNS:
		spans = _find_spans(pat, text)
		for span in spans:
			issues.append(
				Issue(
					file_path=file_path,
					issue_type=IssueType.pii,
					severity=Severity.error,
					message=f"Prohibited content detected: {name}",
					suggestion="Remove or redact the sensitive content.",
					span=span,
				)
			)
	return issues