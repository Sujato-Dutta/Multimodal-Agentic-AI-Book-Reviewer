from typing import Optional
from src.database.client import get_supabase
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _table(name: str):
    client = get_supabase()
    if client is None:
        return None
    return client.table(name)


def insert_upload(filename: str, file_size: int, mime_type: str) -> Optional[dict]:
    t = _table("uploads")
    if t is None:
        return {"id": "mock-upload-id"}
    result = t.insert({
        "filename": filename,
        "file_size_bytes": file_size,
        "mime_type": mime_type,
    }).execute()
    return result.data[0] if result.data else None


def insert_detected_book(upload_id: str, title: str, author: str,
                         ocr_raw_text: str, ocr_confidence: float,
                         isbn: str = None, category: str = None,
                         verified: bool = False, verification_source: str = None,
                         cover_url: str = None) -> Optional[dict]:
    t = _table("detected_books")
    if t is None:
        return {"id": "mock-book-id"}
    result = t.insert({
        "upload_id": upload_id,
        "title": title,
        "author": author,
        "isbn": isbn,
        "category": category,
        "ocr_raw_text": ocr_raw_text,
        "ocr_confidence": ocr_confidence,
        "verified": verified,
        "verification_source": verification_source,
        "cover_url": cover_url,
    }).execute()
    return result.data[0] if result.data else None


def insert_source(book_id: str, source_name: str, source_url: str,
                  content_snippet: str, reliability_score: float) -> Optional[dict]:
    t = _table("sources")
    if t is None:
        return {"id": "mock-source-id"}
    result = t.insert({
        "book_id": book_id,
        "source_name": source_name,
        "source_url": source_url,
        "content_snippet": content_snippet,
        "reliability_score": reliability_score,
    }).execute()
    return result.data[0] if result.data else None


def insert_review(book_id: str, summary: str, best_for: str,
                  not_ideal_for: str, public_sentiment: str,
                  recommendation: str, recommendation_reason: str) -> Optional[dict]:
    t = _table("reviews")
    if t is None:
        return {"id": "mock-review-id"}
    result = t.insert({
        "book_id": book_id,
        "summary": summary,
        "best_for": best_for,
        "not_ideal_for": not_ideal_for,
        "public_sentiment": public_sentiment,
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
    }).execute()
    return result.data[0] if result.data else None


def insert_confidence_score(book_id: str, overall: float, ocr: float,
                            verification: float, source: float,
                            review: float) -> Optional[dict]:
    t = _table("confidence_scores")
    if t is None:
        return {"id": "mock-confidence-id"}
    result = t.insert({
        "book_id": book_id,
        "overall_score": overall,
        "ocr_confidence": ocr,
        "verification_confidence": verification,
        "source_confidence": source,
        "review_confidence": review,
    }).execute()
    return result.data[0] if result.data else None


def insert_feedback(book_id: str, rating: str, comment: str = None) -> Optional[dict]:
    t = _table("feedback")
    if t is None:
        return {"id": "mock-feedback-id"}
    result = t.insert({
        "book_id": book_id,
        "rating": rating,
        "comment": comment,
    }).execute()
    return result.data[0] if result.data else None


def insert_eval_run(run_name: str, total: int, passed: int,
                    failed: int, metrics: dict) -> Optional[dict]:
    t = _table("eval_runs")
    if t is None:
        return {"id": "mock-eval-id"}
    result = t.insert({
        "run_name": run_name,
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "metrics": metrics,
    }).execute()
    return result.data[0] if result.data else None
