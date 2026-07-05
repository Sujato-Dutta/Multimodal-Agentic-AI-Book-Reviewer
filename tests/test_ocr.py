import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.agent.nodes.ocr_agent import _parse_vision_response, vision_agent


def test_parse_vision_response_standard():
    text = "TITLE: Atomic Habits\nAUTHOR: James Clear"
    title, author = _parse_vision_response(text)
    assert title == "Atomic Habits"
    assert author == "James Clear"


def test_parse_vision_response_with_quotes():
    text = 'TITLE: "The Midnight Library"\nAUTHOR: "Matt Haig"'
    title, author = _parse_vision_response(text)
    assert title == "The Midnight Library"
    assert author == "Matt Haig"


def test_parse_vision_response_unknown():
    text = "TITLE: UNKNOWN\nAUTHOR: UNKNOWN"
    title, author = _parse_vision_response(text)
    assert title == "UNKNOWN"
    assert author == "UNKNOWN"


def test_parse_vision_response_empty():
    title, author = _parse_vision_response("")
    assert title == ""
    assert author == ""


def test_parse_vision_response_with_markdown_bold():
    text = "TITLE: **Sapiens**\nAUTHOR: **Yuval Noah Harari**"
    title, author = _parse_vision_response(text)
    assert title == "Sapiens"
    assert author == "Yuval Noah Harari"


@pytest.mark.asyncio
@patch("src.agent.nodes.ocr_agent.ChatGoogleGenerativeAI")
async def test_vision_agent_success(mock_llm_class, mock_image_bytes):
    mock_response = MagicMock()
    mock_response.content = "TITLE: Atomic Habits\nAUTHOR: James Clear"
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mock_llm_class.return_value = mock_llm

    state = {"image_bytes": mock_image_bytes, "filename": "test.png"}
    result = await vision_agent(state)

    assert result["detected_title"] == "Atomic Habits"
    assert result["detected_author"] == "James Clear"
    assert result["ocr_confidence"] == 0.9


@pytest.mark.asyncio
@patch("src.agent.nodes.ocr_agent.ChatGoogleGenerativeAI")
async def test_vision_agent_failure(mock_llm_class):
    mock_llm_class.side_effect = Exception("API error")

    state = {"image_bytes": b"fake", "filename": "bad.png"}
    result = await vision_agent(state)

    assert result["detected_title"] == ""
    assert result["ocr_confidence"] == 0.0
    assert "error" in result


@pytest.mark.asyncio
@patch("src.agent.nodes.ocr_agent.ChatGoogleGenerativeAI")
async def test_vision_agent_unknown_result(mock_llm_class, mock_image_bytes):
    mock_response = MagicMock()
    mock_response.content = "TITLE: UNKNOWN\nAUTHOR: UNKNOWN"
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    mock_llm_class.return_value = mock_llm

    state = {"image_bytes": mock_image_bytes, "filename": "blurry.png"}
    result = await vision_agent(state)

    assert result["detected_title"] == ""
    assert result["detected_author"] == ""
    assert result["ocr_confidence"] == 0.0
