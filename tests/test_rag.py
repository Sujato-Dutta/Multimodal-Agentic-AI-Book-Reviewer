import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from src.rag.bm25 import BM25Index
from src.rag.hybrid import chunk_text, reciprocal_rank_fusion


def test_bm25_build_and_search():
    bm25 = BM25Index()
    docs = [
        {"text": "Atomic Habits is about building good habits", "metadata": {"source": "goodreads"}},
        {"text": "Python programming language tutorial", "metadata": {"source": "docs"}},
        {"text": "James Clear explains habit formation", "metadata": {"source": "amazon"}},
    ]
    bm25.build(docs)
    results = bm25.search("habits building", top_k=2)
    assert len(results) > 0
    assert results[0]["score"] > 0


def test_bm25_empty_corpus():
    bm25 = BM25Index()
    bm25.build([])
    results = bm25.search("test")
    assert results == []


def test_bm25_no_match():
    bm25 = BM25Index()
    bm25.build([{"text": "completely unrelated content xyz", "metadata": {}}])
    results = bm25.search("quantum physics black holes")
    # BM25 may return results with score 0 or empty
    high_score = [r for r in results if r["score"] > 0.1]
    assert len(high_score) == 0


def test_chunk_text():
    text = " ".join([f"word{i}" for i in range(100)])
    chunks = chunk_text(text, "test_source", "book_123", chunk_size=30, overlap=5)
    assert len(chunks) > 0
    assert all(c["metadata"]["source"] == "test_source" for c in chunks)
    assert all(c["metadata"]["book_id"] == "book_123" for c in chunks)
    assert all(c["id"] for c in chunks)


def test_chunk_text_short():
    chunks = chunk_text("short text", "src", "b1")
    assert len(chunks) == 1


def test_rrf_basic():
    dense = [
        {"id": "a", "score": 0.9, "text": "doc a", "metadata": {"source": "s1"}},
        {"id": "b", "score": 0.7, "text": "doc b", "metadata": {"source": "s2"}},
    ]
    sparse = [
        {"text": "doc b", "score": 5.0, "metadata": {"source": "s2"}},
        {"text": "doc c", "score": 3.0, "metadata": {"source": "s3"}},
    ]
    fused = reciprocal_rank_fusion(dense, sparse, k=60)
    assert len(fused) >= 2


def test_rrf_empty():
    fused = reciprocal_rank_fusion([], [])
    assert fused == []
