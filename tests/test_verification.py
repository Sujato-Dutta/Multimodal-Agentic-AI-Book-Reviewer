import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, AsyncMock
from src.agent.nodes.verification import _match_score, verification_agent


def test_match_score_exact():
    assert _match_score("Atomic Habits", "Atomic Habits") == 1.0


def test_match_score_substring():
    score = _match_score("Atomic", "Atomic Habits")
    assert score >= 0.5


def test_match_score_partial_overlap():
    score = _match_score("Atomic Habits Guide", "Atomic Habits")
    assert score > 0.0


def test_match_score_empty():
    assert _match_score("", "something") == 0.0
    assert _match_score("something", "") == 0.0


def test_match_score_no_overlap():
    score = _match_score("xyz", "abc")
    assert score == 0.0


@pytest.mark.asyncio
@patch("src.agent.nodes.verification._search_open_library", new_callable=AsyncMock)
@patch("src.agent.nodes.verification._search_google_books", new_callable=AsyncMock)
async def test_verification_agent_verified(mock_google, mock_ol):
    mock_google.return_value = {
        "title": "Atomic Habits",
        "authors": ["James Clear"],
        "isbn": "9780735211292",
        "categories": ["Self-help"],
        "cover_url": "https://example.com/cover.jpg",
        "source": "google_books",
    }
    mock_ol.return_value = None

    state = {"detected_title": "Atomic Habits", "detected_author": "James Clear"}
    result = await verification_agent(state)

    assert result["verified"] is True
    assert result["verified_title"] == "Atomic Habits"
    assert result["verified_author"] == "James Clear"
    assert result["verification_confidence"] > 0.4


@pytest.mark.asyncio
@patch("src.agent.nodes.verification._search_open_library", new_callable=AsyncMock)
@patch("src.agent.nodes.verification._search_google_books", new_callable=AsyncMock)
async def test_verification_agent_unverified(mock_google, mock_ol):
    mock_google.return_value = None
    mock_ol.return_value = None

    state = {"detected_title": "Unknown Book XYZ", "detected_author": "Nobody"}
    result = await verification_agent(state)

    assert result["verified"] is False
    assert result["verification_confidence"] == 0.0
