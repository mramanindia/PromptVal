from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
	"""Severity levels for issues detected in a prompt file."""
	info = "info"
	warning = "warning"
	error = "error"


class IssueType(str, Enum):
	"""Types of validation issues."""
	redundancy = "redundancy"
	conflict = "conflict"
	completeness = "completeness"
	pii = "pii"


class TextSpan(BaseModel):
	"""Character span within a file text [start, end)."""
	start: int = Field(..., description="Start index in the file text (inclusive)")
	end: int = Field(..., description="End index in the file text (exclusive)")


class Issue(BaseModel):
	"""A single validation issue with optional fix suggestion and text span."""
	file_path: str
	issue_type: IssueType
	severity: Severity
	message: str
	suggestion: Optional[str] = None
	span: Optional[TextSpan] = None


class ValidationResult(BaseModel):
	"""Issues collected for a specific file."""
	file_path: str
	issues: List[Issue] = Field(default_factory=list)

	@property
	def has_errors(self) -> bool:
		"""Return True if any issue has severity error."""
		return any(i.severity == Severity.error for i in self.issues)


class FixOperationType(str, Enum):
	"""Supported fix operation types for applying automated edits."""
	replace = "replace"
	delete = "delete"
	insert_after = "insert_after"
	append = "append"


class FixOperation(BaseModel):
	"""A single text transformation operation."""
	op: FixOperationType
	span: Optional[TextSpan] = None
	content: Optional[str] = None


class FixProposal(BaseModel):
	"""Set of operations to apply to a file, with a human-readable description."""
	file_path: str
	operations: List[FixOperation]
	description: str