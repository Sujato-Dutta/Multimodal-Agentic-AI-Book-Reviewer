import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from src.api.schemas import (
    AnalyzeResponse, FeedbackRequest, FeedbackResponse, HealthResponse,
)
from src.agent.graph import analyze_book
from src.database.operations import (
    insert_upload, insert_detected_book, insert_source,
    insert_review, insert_confidence_score, insert_feedback,
)
from src.monitoring.metrics import (
    REQUEST_LATENCY, REQUEST_COUNT, ACTIVE_ANALYSES, FEEDBACK_SATISFACTION,
)
from config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _persist_results(upload_id: str, result: dict):
    """Persist analysis results to Supabase. Failures are logged but don't block the response."""
    try:
        book = result.get("book", {})
        review = result.get("review", {})
        rec = result.get("recommendation", {})
        conf = result.get("confidence", {})
        breakdown = conf.get("breakdown", {})

        book_record = insert_detected_book(
            upload_id=upload_id,
            title=book.get("title", ""),
            author=book.get("author", ""),
            ocr_raw_text="",
            ocr_confidence=breakdown.get("ocr", 0.0),
            isbn=book.get("isbn"),
            category=book.get("category"),
            verified=book.get("verified", False),
            verification_source=None,
            cover_url=book.get("cover_url"),
        )
        book_id = book_record.get("id", "mock-book-id") if book_record else "mock-book-id"

        for citation in result.get("citations", []):
            insert_source(
                book_id=book_id,
                source_name=citation.get("source", ""),
                source_url=citation.get("url", ""),
                content_snippet="",
                reliability_score=0.0,
            )

        insert_review(
            book_id=book_id,
            summary=review.get("summary", ""),
            best_for=review.get("best_for", ""),
            not_ideal_for=review.get("not_ideal_for", ""),
            public_sentiment=review.get("public_sentiment", ""),
            recommendation=rec.get("action", "borrow"),
            recommendation_reason=rec.get("reason", ""),
        )

        insert_confidence_score(
            book_id=book_id,
            overall=conf.get("overall", 0.0),
            ocr=breakdown.get("ocr", 0.0),
            verification=breakdown.get("verification", 0.0),
            source=breakdown.get("source_reliability", 0.0),
            review=breakdown.get("review_quality", 0.0),
        )

        logger.info(f"Persisted results for book_id={book_id}")
    except Exception as e:
        logger.error(f"Failed to persist results to Supabase: {e}")


@router.post("/analyze-book", response_model=AnalyzeResponse)
async def analyze_book_endpoint(file: UploadFile = File(...)):
    start = time.time()
    ACTIVE_ANALYSES.inc()

    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        contents = await file.read()
        max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Image exceeds {settings.MAX_IMAGE_SIZE_MB}MB limit",
            )

        upload_record = insert_upload(
            filename=file.filename or "unknown",
            file_size=len(contents),
            mime_type=file.content_type or "image/unknown",
        )
        upload_id = upload_record.get("id", "mock-upload-id") if upload_record else "mock-upload-id"

        result = await analyze_book(contents, file.filename or "upload")

        _persist_results(upload_id, result)

        latency = time.time() - start
        REQUEST_LATENCY.labels(endpoint="/analyze-book", method="POST").observe(latency)
        REQUEST_COUNT.labels(endpoint="/analyze-book", method="POST", status="200").inc()
        logger.info(f"Analysis completed in {latency:.2f}s")
        return AnalyzeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        REQUEST_COUNT.labels(endpoint="/analyze-book", method="POST", status="500").inc()
        raise HTTPException(status_code=500, detail="Analysis failed")
    finally:
        ACTIVE_ANALYSES.dec()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    try:
        insert_feedback(
            book_id=request.book_id,
            rating=request.rating,
            comment=request.comment,
        )
        FEEDBACK_SATISFACTION.labels(rating=request.rating).inc()
        return FeedbackResponse()
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
    )

