import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_book_state():
    return {
        "image_bytes": b"fake_image_data",
        "filename": "test_book.jpg",
        "detected_title": "Atomic Habits",
        "detected_author": "James Clear",
        "ocr_confidence": 0.85,
        "verified": True,
        "verified_title": "Atomic Habits",
        "verified_author": "James Clear",
        "isbn": "9780735211292",
        "category": "Self-help",
        "cover_url": "https://example.com/cover.jpg",
        "verification_source": "google_books",
        "verification_confidence": 0.92,
        "sources": [
            {
                "source_name": "goodreads.com",
                "source_url": "https://goodreads.com/book/123",
                "content": "A practical guide to building good habits.",
                "reliability_score": 0.85,
            },
            {
                "source_name": "books.google.com",
                "source_url": "https://books.google.com/books?id=abc",
                "content": "Atomic Habits by James Clear focuses on small changes.",
                "reliability_score": 0.95,
            },
        ],
        "summary": "A practical guide about building good habits through small changes.",
        "best_for": "Anyone wanting to build better habits.",
        "not_ideal_for": "Readers seeking deep academic psychology.",
        "public_sentiment": "Highly praised for clarity and practical advice.",
        "recommendation": "buy",
        "recommendation_reason": "Essential reading for habit building.",
        "overall_confidence": 0.88,
        "confidence_breakdown": {
            "ocr": 0.85,
            "verification": 0.92,
            "source_reliability": 0.90,
            "review_quality": 1.0,
        },
        "citations": [
            {"source": "Goodreads"},
            {"source": "Google Books"},
        ],
    }


@pytest.fixture
def mock_image_bytes():
    """Create a minimal valid PNG image."""
    from PIL import Image
    import io
    img = Image.new("RGB", (200, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
