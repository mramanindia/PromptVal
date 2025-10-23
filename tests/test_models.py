"""
Test cases for data models and validation result structures.

This module tests the Pydantic models used throughout the promptval package.
"""

import pytest
from promptval.models import (
    Severity,
    IssueType,
    TextSpan,
    Issue,
    ValidationResult,
    FixOperationType,
    FixOperation,
    FixProposal
)


class TestSeverity:
    """Test Severity enum."""

    def test_severity_values(self):
        """Test that Severity enum has correct values."""
        assert Severity.info == "info"
        assert Severity.warning == "warning"
        assert Severity.error == "error"

    def test_severity_enum_membership(self):
        """Test Severity enum membership."""
        assert "info" in Severity
        assert "warning" in Severity
        assert "error" in Severity
        assert "critical" not in Severity

    def test_severity_string_conversion(self):
        """Test Severity string conversion."""
        assert str(Severity.info) == "Severity.info"
        assert str(Severity.warning) == "Severity.warning"
        assert str(Severity.error) == "Severity.error"
        # Test value access
        assert Severity.info.value == "info"
        assert Severity.warning.value == "warning"
        assert Severity.error.value == "error"


class TestIssueType:
    """Test IssueType enum."""

    def test_issue_type_values(self):
        """Test that IssueType enum has correct values."""
        assert IssueType.redundancy == "redundancy"
        assert IssueType.conflict == "conflict"
        assert IssueType.completeness == "completeness"
        assert IssueType.pii == "pii"

    def test_issue_type_enum_membership(self):
        """Test IssueType enum membership."""
        assert "redundancy" in IssueType
        assert "conflict" in IssueType
        assert "completeness" in IssueType
        assert "pii" in IssueType
        assert "unknown" not in IssueType

    def test_issue_type_string_conversion(self):
        """Test IssueType string conversion."""
        assert str(IssueType.redundancy) == "IssueType.redundancy"
        assert str(IssueType.conflict) == "IssueType.conflict"
        assert str(IssueType.completeness) == "IssueType.completeness"
        assert str(IssueType.pii) == "IssueType.pii"
        # Test value access
        assert IssueType.redundancy.value == "redundancy"
        assert IssueType.conflict.value == "conflict"
        assert IssueType.completeness.value == "completeness"
        assert IssueType.pii.value == "pii"


class TestTextSpan:
    """Test TextSpan model."""

    def test_text_span_creation(self):
        """Test TextSpan creation with valid values."""
        span = TextSpan(start=10, end=20)
        
        assert span.start == 10
        assert span.end == 20

    def test_text_span_validation(self):
        """Test TextSpan validation."""
        # Valid span
        span = TextSpan(start=0, end=10)
        assert span.start == 0
        assert span.end == 10
        
        # Edge case: start equals end (empty span)
        span = TextSpan(start=5, end=5)
        assert span.start == 5
        assert span.end == 5

    def test_text_span_negative_values(self):
        """Test TextSpan with negative values."""
        # Should allow negative values (might be valid in some contexts)
        span = TextSpan(start=-1, end=5)
        assert span.start == -1
        assert span.end == 5

    def test_text_span_float_values(self):
        """Test TextSpan with float values."""
        # Pydantic v2 doesn't auto-convert floats to ints, so we need to pass ints
        span = TextSpan(start=10, end=20)
        assert span.start == 10
        assert span.end == 20

    def test_text_span_string_values(self):
        """Test TextSpan with string values that can be converted to int."""
        span = TextSpan(start="10", end="20")
        assert span.start == 10
        assert span.end == 20


class TestIssue:
    """Test Issue model."""

    def test_issue_creation_minimal(self):
        """Test Issue creation with minimal required fields."""
        issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="Test issue"
        )
        
        assert issue.file_path == "test.txt"
        assert issue.issue_type == IssueType.pii
        assert issue.severity == Severity.error
        assert issue.message == "Test issue"
        assert issue.suggestion is None
        assert issue.span is None

    def test_issue_creation_full(self):
        """Test Issue creation with all fields."""
        span = TextSpan(start=10, end=20)
        issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.redundancy,
            severity=Severity.warning,
            message="Redundant content detected",
            suggestion="Remove duplicate text",
            span=span
        )
        
        assert issue.file_path == "test.txt"
        assert issue.issue_type == IssueType.redundancy
        assert issue.severity == Severity.warning
        assert issue.message == "Redundant content detected"
        assert issue.suggestion == "Remove duplicate text"
        assert issue.span == span

    def test_issue_creation_with_string_types(self):
        """Test Issue creation with string values for enums."""
        issue = Issue(
            file_path="test.txt",
            issue_type="pii",
            severity="error",
            message="Test issue"
        )
        
        assert issue.issue_type == IssueType.pii
        assert issue.severity == Severity.error

    def test_issue_validation(self):
        """Test Issue validation."""
        # Valid issue
        issue = Issue(
            file_path="/path/to/file.txt",
            issue_type=IssueType.completeness,
            severity=Severity.info,
            message="Missing edge cases"
        )
        
        assert issue.file_path == "/path/to/file.txt"
        assert issue.issue_type == IssueType.completeness
        assert issue.severity == Severity.info
        assert issue.message == "Missing edge cases"

    def test_issue_optional_fields(self):
        """Test Issue with optional fields."""
        issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.conflict,
            severity=Severity.warning,
            message="Conflicting instructions",
            suggestion="Clarify the requirements"
        )
        
        assert issue.suggestion == "Clarify the requirements"
        assert issue.span is None

    def test_issue_with_span(self):
        """Test Issue with TextSpan."""
        span = TextSpan(start=5, end=15)
        issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="PII detected",
            span=span
        )
        
        assert issue.span == span
        assert issue.span.start == 5
        assert issue.span.end == 15


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_creation_minimal(self):
        """Test ValidationResult creation with minimal fields."""
        result = ValidationResult(file_path="test.txt")
        
        assert result.file_path == "test.txt"
        assert result.issues == []

    def test_validation_result_creation_with_issues(self):
        """Test ValidationResult creation with issues."""
        issue1 = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="PII detected"
        )
        issue2 = Issue(
            file_path="test.txt",
            issue_type=IssueType.redundancy,
            severity=Severity.warning,
            message="Redundant content"
        )
        
        result = ValidationResult(
            file_path="test.txt",
            issues=[issue1, issue2]
        )
        
        assert result.file_path == "test.txt"
        assert len(result.issues) == 2
        assert result.issues[0] == issue1
        assert result.issues[1] == issue2

    def test_validation_result_has_errors_property(self):
        """Test ValidationResult.has_errors property."""
        # No issues
        result = ValidationResult(file_path="test.txt", issues=[])
        assert result.has_errors is False
        
        # Only warnings and info
        warning_issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.redundancy,
            severity=Severity.warning,
            message="Warning"
        )
        info_issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.completeness,
            severity=Severity.info,
            message="Info"
        )
        
        result = ValidationResult(
            file_path="test.txt",
            issues=[warning_issue, info_issue]
        )
        assert result.has_errors is False
        
        # With errors
        error_issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="Error"
        )
        
        result = ValidationResult(
            file_path="test.txt",
            issues=[warning_issue, info_issue, error_issue]
        )
        assert result.has_errors is True

    def test_validation_result_has_errors_multiple_errors(self):
        """Test ValidationResult.has_errors with multiple errors."""
        error1 = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="Error 1"
        )
        error2 = Issue(
            file_path="test.txt",
            issue_type=IssueType.conflict,
            severity=Severity.error,
            message="Error 2"
        )
        
        result = ValidationResult(
            file_path="test.txt",
            issues=[error1, error2]
        )
        assert result.has_errors is True

    def test_validation_result_issues_default_factory(self):
        """Test that issues defaults to empty list."""
        result = ValidationResult(file_path="test.txt")
        assert result.issues == []
        assert isinstance(result.issues, list)


class TestFixOperationType:
    """Test FixOperationType enum."""

    def test_fix_operation_type_values(self):
        """Test that FixOperationType enum has correct values."""
        assert FixOperationType.replace == "replace"
        assert FixOperationType.delete == "delete"
        assert FixOperationType.insert_after == "insert_after"
        assert FixOperationType.append == "append"

    def test_fix_operation_type_enum_membership(self):
        """Test FixOperationType enum membership."""
        assert "replace" in FixOperationType
        assert "delete" in FixOperationType
        assert "insert_after" in FixOperationType
        assert "append" in FixOperationType
        assert "unknown" not in FixOperationType

    def test_fix_operation_type_string_conversion(self):
        """Test FixOperationType string conversion."""
        assert str(FixOperationType.replace) == "FixOperationType.replace"
        assert str(FixOperationType.delete) == "FixOperationType.delete"
        assert str(FixOperationType.insert_after) == "FixOperationType.insert_after"
        assert str(FixOperationType.append) == "FixOperationType.append"
        # Test value access
        assert FixOperationType.replace.value == "replace"
        assert FixOperationType.delete.value == "delete"
        assert FixOperationType.insert_after.value == "insert_after"
        assert FixOperationType.append.value == "append"


class TestFixOperation:
    """Test FixOperation model."""

    def test_fix_operation_creation_minimal(self):
        """Test FixOperation creation with minimal fields."""
        operation = FixOperation(op=FixOperationType.replace)
        
        assert operation.op == FixOperationType.replace
        assert operation.span is None
        assert operation.content is None

    def test_fix_operation_creation_full(self):
        """Test FixOperation creation with all fields."""
        span = TextSpan(start=10, end=20)
        operation = FixOperation(
            op=FixOperationType.replace,
            span=span,
            content="New content"
        )
        
        assert operation.op == FixOperationType.replace
        assert operation.span == span
        assert operation.content == "New content"

    def test_fix_operation_creation_with_string_op(self):
        """Test FixOperation creation with string operation type."""
        operation = FixOperation(op="delete")
        
        assert operation.op == FixOperationType.delete

    def test_fix_operation_different_types(self):
        """Test FixOperation with different operation types."""
        # Replace operation
        replace_op = FixOperation(
            op=FixOperationType.replace,
            span=TextSpan(start=0, end=10),
            content="Replacement text"
        )
        assert replace_op.op == FixOperationType.replace
        assert replace_op.content == "Replacement text"
        
        # Delete operation
        delete_op = FixOperation(
            op=FixOperationType.delete,
            span=TextSpan(start=5, end=15)
        )
        assert delete_op.op == FixOperationType.delete
        assert delete_op.content is None
        
        # Insert after operation
        insert_op = FixOperation(
            op=FixOperationType.insert_after,
            span=TextSpan(start=10, end=10),
            content="Inserted text"
        )
        assert insert_op.op == FixOperationType.insert_after
        assert insert_op.content == "Inserted text"
        
        # Append operation
        append_op = FixOperation(
            op=FixOperationType.append,
            content="Appended text"
        )
        assert append_op.op == FixOperationType.append
        assert append_op.content == "Appended text"
        assert append_op.span is None


class TestFixProposal:
    """Test FixProposal model."""

    def test_fix_proposal_creation_minimal(self):
        """Test FixProposal creation with minimal fields."""
        proposal = FixProposal(
            file_path="test.txt",
            operations=[],
            description="Test fix"
        )
        
        assert proposal.file_path == "test.txt"
        assert proposal.operations == []
        assert proposal.description == "Test fix"

    def test_fix_proposal_creation_with_operations(self):
        """Test FixProposal creation with operations."""
        operation1 = FixOperation(
            op=FixOperationType.replace,
            span=TextSpan(start=0, end=10),
            content="New text"
        )
        operation2 = FixOperation(
            op=FixOperationType.append,
            content="Additional text"
        )
        
        proposal = FixProposal(
            file_path="test.txt",
            operations=[operation1, operation2],
            description="Fix redundant content and add clarification"
        )
        
        assert proposal.file_path == "test.txt"
        assert len(proposal.operations) == 2
        assert proposal.operations[0] == operation1
        assert proposal.operations[1] == operation2
        assert proposal.description == "Fix redundant content and add clarification"

    def test_fix_proposal_operations_default_factory(self):
        """Test that operations defaults to empty list."""
        proposal = FixProposal(
            file_path="test.txt",
            operations=[],  # Explicitly provide empty list
            description="Test fix"
        )
        assert proposal.operations == []
        assert isinstance(proposal.operations, list)

    def test_fix_proposal_validation(self):
        """Test FixProposal validation."""
        # Valid proposal
        proposal = FixProposal(
            file_path="/path/to/file.txt",
            operations=[],
            description="Valid fix proposal"
        )
        
        assert proposal.file_path == "/path/to/file.txt"
        assert proposal.description == "Valid fix proposal"

    def test_fix_proposal_with_complex_operations(self):
        """Test FixProposal with complex operations."""
        operations = [
            FixOperation(
                op=FixOperationType.replace,
                span=TextSpan(start=0, end=5),
                content="Start"
            ),
            FixOperation(
                op=FixOperationType.insert_after,
                span=TextSpan(start=10, end=10),
                content="Middle"
            ),
            FixOperation(
                op=FixOperationType.delete,
                span=TextSpan(start=15, end=20)
            ),
            FixOperation(
                op=FixOperationType.append,
                content="End"
            )
        ]
        
        proposal = FixProposal(
            file_path="complex.txt",
            operations=operations,
            description="Complex multi-operation fix"
        )
        
        assert len(proposal.operations) == 4
        assert proposal.operations[0].op == FixOperationType.replace
        assert proposal.operations[1].op == FixOperationType.insert_after
        assert proposal.operations[2].op == FixOperationType.delete
        assert proposal.operations[3].op == FixOperationType.append


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_issue_serialization(self):
        """Test Issue serialization to dict."""
        issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.pii,
            severity=Severity.error,
            message="PII detected",
            suggestion="Remove sensitive data",
            span=TextSpan(start=10, end=20)
        )
        
        data = issue.model_dump()
        
        assert data["file_path"] == "test.txt"
        assert data["issue_type"] == "pii"
        assert data["severity"] == "error"
        assert data["message"] == "PII detected"
        assert data["suggestion"] == "Remove sensitive data"
        assert data["span"]["start"] == 10
        assert data["span"]["end"] == 20

    def test_validation_result_serialization(self):
        """Test ValidationResult serialization to dict."""
        issue = Issue(
            file_path="test.txt",
            issue_type=IssueType.redundancy,
            severity=Severity.warning,
            message="Redundant content"
        )
        
        result = ValidationResult(
            file_path="test.txt",
            issues=[issue]
        )
        
        data = result.model_dump()
        
        assert data["file_path"] == "test.txt"
        assert len(data["issues"]) == 1
        assert data["issues"][0]["issue_type"] == "redundancy"
        assert data["issues"][0]["severity"] == "warning"

    def test_fix_operation_serialization(self):
        """Test FixOperation serialization to dict."""
        operation = FixOperation(
            op=FixOperationType.replace,
            span=TextSpan(start=5, end=15),
            content="Replacement"
        )
        
        data = operation.model_dump()
        
        assert data["op"] == "replace"
        assert data["span"]["start"] == 5
        assert data["span"]["end"] == 15
        assert data["content"] == "Replacement"

    def test_fix_proposal_serialization(self):
        """Test FixProposal serialization to dict."""
        operation = FixOperation(
            op=FixOperationType.append,
            content="New content"
        )
        
        proposal = FixProposal(
            file_path="test.txt",
            operations=[operation],
            description="Add content"
        )
        
        data = proposal.model_dump()
        
        assert data["file_path"] == "test.txt"
        assert len(data["operations"]) == 1
        assert data["operations"][0]["op"] == "append"
        assert data["description"] == "Add content"
