import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from src.api.schemas import (
    AnalyzeResponse, FeedbackRequest, FeedbackResponse, HealthResponse,
)
from src.agent.graph import analyze_book
from src.database.operations import insert_upload, insert_feedback
from src.monitoring.metrics import (
    REQUEST_LATENCY, REQUEST_COUNT, ACTIVE_ANALYSES, FEEDBACK_SATISFACTION,
)
from config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


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

        insert_upload(
            filename=file.filename or "unknown",
            file_size=len(contents),
            mime_type=file.content_type or "image/unknown",
        )

        result = await analyze_book(contents, file.filename or "upload")

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
