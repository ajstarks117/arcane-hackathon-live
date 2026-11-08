"""Tests for the Mermaid diagram generator and validator."""
import pytest
from agents.mermaid_generator import validate_mermaid, generate_mermaid_diagram, FALLBACK_MERMAID


def test_validate_mermaid_valid_flowchart():
    valid = "flowchart LR\n  A --> B"
    assert validate_mermaid(valid) is True


def test_validate_mermaid_valid_graph():
    valid = "graph TD\n  X --> Y --> Z"
    assert validate_mermaid(valid) is True


def test_validate_mermaid_invalid_missing_arrow():
    invalid = "flowchart LR\n  A - B"
    assert validate_mermaid(invalid) is False


def test_validate_mermaid_invalid_prefix():
    invalid = "Hello flowchart LR\n A --> B"
    assert validate_mermaid(invalid) is False


def test_validate_mermaid_empty():
    assert validate_mermaid("") is False


def test_generate_mermaid_returns_fenced_block():
    result = generate_mermaid_diagram("dummy_patch", "dummy_cause")
    assert result.startswith("```mermaid")
    assert result.strip().endswith("```")


def test_generate_mermaid_contains_pipeline_nodes():
    result = generate_mermaid_diagram("patch", "cause")
    assert "CI Failure Detected" in result
    assert "Patch Generator" in result
    assert "Validator Agent" in result
    assert "PR Created" in result


def test_fallback_mermaid_is_valid():
    """The fallback diagram itself should pass validation after stripping fences."""
    inner = FALLBACK_MERMAID.replace("```mermaid\n", "").replace("\n```", "").strip()
    assert validate_mermaid(inner) is True
