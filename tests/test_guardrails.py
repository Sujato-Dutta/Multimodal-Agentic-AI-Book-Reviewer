import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.agent.nodes.guardrail import (
    _check_spoilers, _check_citations, _check_source_whitelist,
    _check_confidence, _check_completeness, guardrail_agent,
)


def test_spoiler_detection():
    text = "The character dies at the ending"
    warnings = _check_spoilers(text)
    assert len(warnings) >= 1
    assert any("spoiler" in w.lower() or "ending" in w.lower() or "dies" in w.lower() for w in warnings)


def test_no_spoiler():
    text = "This is a great book about personal growth"
    warnings = _check_spoilers(text)
    assert len(warnings) == 0


def test_citation_check_insufficient():
    state = {"citations": [{"source": "one"}]}
    warnings = _check_citations(state)
    assert len(warnings) == 1
    assert "insufficient" in warnings[0].lower()


def test_citation_check_sufficient():
    state = {"citations": [{"source": "one"}, {"source": "two"}, {"source": "three"}]}
    warnings = _check_citations(state)
    assert len(warnings) == 0


def test_source_whitelist_valid():
    state = {
        "sources": [
            {"source_url": "https://goodreads.com/book/123"},
            {"source_url": "https://books.google.com/books?id=abc"},
        ]
    }
    warnings = _check_source_whitelist(state)
    assert len(warnings) == 0


def test_source_whitelist_invalid():
    state = {
        "sources": [
            {"source_url": "https://shady-site.com/reviews"},
        ]
    }
    warnings = _check_source_whitelist(state)
    assert len(warnings) == 1
    assert "whitelist" in warnings[0].lower()


def test_low_confidence():
    state = {"overall_confidence": 0.1}
    warnings = _check_confidence(state)
    assert len(warnings) == 1


def test_adequate_confidence():
    state = {"overall_confidence": 0.8}
    warnings = _check_confidence(state)
    assert len(warnings) == 0


def test_completeness_missing():
    state = {"summary": "", "recommendation": ""}
    warnings = _check_completeness(state)
    assert len(warnings) == 2


def test_completeness_ok():
    state = {"summary": "Great book", "recommendation": "buy"}
    warnings = _check_completeness(state)
    assert len(warnings) == 0


def test_guardrail_agent_full(sample_book_state):
    result = guardrail_agent(sample_book_state)
    assert result["is_valid"] is True
    assert "final_output" in result
    output = result["final_output"]
    assert output["book"]["title"] == "Atomic Habits"
    assert output["recommendation"]["action"] == "buy"
    assert output["confidence"]["overall"] == 0.88


def test_guardrail_low_confidence_fallback():
    state = {
        "summary": "Test review.",
        "recommendation": "borrow",
        "overall_confidence": 0.1,
        "confidence_breakdown": {},
        "citations": [],
        "sources": [],
        "verified_title": "Test",
        "verified_author": "Author",
    }
    result = guardrail_agent(state)
    assert "⚠️" in result["summary"]
    assert any("low confidence" in w.lower() for w in result["guardrail_warnings"])
