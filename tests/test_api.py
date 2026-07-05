import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data


def test_analyze_no_file(client):
    response = client.post("/api/analyze-book")
    assert response.status_code == 422


def test_analyze_wrong_content_type(client):
    response = client.post(
        "/api/analyze-book",
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


@patch("src.api.routes.analyze_book", new_callable=AsyncMock)
def test_analyze_success(mock_analyze, client, sample_book_state):
    mock_analyze.return_value = {
        "book": {
            "title": "Atomic Habits",
            "author": "James Clear",
            "category": "Self-help",
            "isbn": "123",
            "cover_url": "",
            "verified": True,
        },
        "review": {
            "summary": "Great book about habits.",
            "best_for": "Everyone",
            "not_ideal_for": "Academics",
            "public_sentiment": "Positive",
        },
        "recommendation": {"action": "buy", "reason": "Must read"},
        "confidence": {"overall": 0.88, "breakdown": {}},
        "citations": [{"source": "Goodreads", "url": ""}],
        "sources": ["goodreads.com"],
        "warnings": [],
    }

    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/analyze-book",
        files={"file": ("test.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["book"]["title"] == "Atomic Habits"
    assert data["recommendation"]["action"] == "buy"


def test_feedback_valid(client):
    with patch("src.api.routes.insert_feedback", return_value={"id": "test"}):
        response = client.post(
            "/api/feedback",
            json={"book_id": "test-book", "rating": "helpful"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_feedback_invalid_rating(client):
    response = client.post(
        "/api/feedback",
        json={"book_id": "test-book", "rating": "invalid"},
    )
    assert response.status_code == 422


def test_root_serves_frontend(client):
    response = client.get("/")
    assert response.status_code == 200
