import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Settings


def test_default_model_name():
    s = Settings(GOOGLE_API_KEY="test", SUPABASE_URL="https://x.supabase.co", SUPABASE_KEY="k")
    assert s.MODEL_NAME == "gemini-3.1-flash-lite"


def test_default_embedding_model():
    s = Settings(GOOGLE_API_KEY="test")
    assert s.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"


def test_default_reranker_model():
    s = Settings()
    assert s.RERANKER_MODEL == "cross-encoder/ms-marco-MiniLM-L-6-v2"


def test_pinecone_defaults():
    s = Settings()
    assert s.PINECONE_INDEX == "ledgera-books"
    assert s.PINECONE_DIMENSION == 384


def test_retrieval_defaults():
    s = Settings()
    assert s.RETRIEVAL_TOP_K == 10
    assert s.RERANK_TOP_K == 5
    assert s.RRF_K == 60


def test_allowed_domains():
    s = Settings()
    assert "books.google.com" in s.ALLOWED_DOMAINS
    assert "openlibrary.org" in s.ALLOWED_DOMAINS
    assert "goodreads.com" in s.ALLOWED_DOMAINS


def test_guardrail_defaults():
    s = Settings()
    assert s.MIN_CONFIDENCE_THRESHOLD == 0.3
    assert s.MIN_CITATIONS_REQUIRED == 2
    assert len(s.SPOILER_KEYWORDS) > 0


def test_source_weights():
    s = Settings()
    assert s.SOURCE_WEIGHTS["books.google.com"] == 0.95
    assert s.SOURCE_WEIGHTS["openlibrary.org"] == 0.90


def test_cors_origins():
    s = Settings()
    assert isinstance(s.CORS_ORIGINS, list)
    assert len(s.CORS_ORIGINS) > 0


def test_max_image_size():
    s = Settings()
    assert s.MAX_IMAGE_SIZE_MB == 10
