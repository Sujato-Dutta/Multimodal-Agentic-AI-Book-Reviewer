import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
from src.database.operations import (
    insert_upload, insert_detected_book, insert_feedback,
    insert_source, insert_review, insert_confidence_score,
)


@patch("src.database.operations.get_supabase", return_value=None)
def test_insert_upload_mock_mode(mock_db):
    result = insert_upload("test.jpg", 1024, "image/jpeg")
    assert result is not None
    assert "id" in result


@patch("src.database.operations.get_supabase", return_value=None)
def test_insert_detected_book_mock_mode(mock_db):
    result = insert_detected_book(
        upload_id="u1", title="Test", author="Author",
        ocr_raw_text="raw", ocr_confidence=0.9,
    )
    assert result is not None


@patch("src.database.operations.get_supabase", return_value=None)
def test_insert_feedback_mock_mode(mock_db):
    result = insert_feedback("book1", "helpful", "Great review!")
    assert result is not None


@patch("src.database.operations.get_supabase", return_value=None)
def test_insert_source_mock_mode(mock_db):
    result = insert_source("book1", "goodreads", "https://goodreads.com", "snippet", 0.85)
    assert result is not None


@patch("src.database.operations.get_supabase", return_value=None)
def test_insert_review_mock_mode(mock_db):
    result = insert_review(
        "book1", "summary", "best for", "not ideal",
        "positive", "buy", "great book",
    )
    assert result is not None


@patch("src.database.operations.get_supabase", return_value=None)
def test_insert_confidence_mock_mode(mock_db):
    result = insert_confidence_score("book1", 0.88, 0.85, 0.92, 0.90, 1.0)
    assert result is not None


@patch("src.database.operations.get_supabase")
def test_insert_upload_with_db(mock_get_db):
    mock_table = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [{"id": "real-id", "filename": "test.jpg"}]
    mock_table.insert.return_value.execute.return_value = mock_result
    mock_client = MagicMock()
    mock_client.table.return_value = mock_table
    mock_get_db.return_value = mock_client

    result = insert_upload("test.jpg", 1024, "image/jpeg")
    assert result["id"] == "real-id"
    mock_client.table.assert_called_with("uploads")
