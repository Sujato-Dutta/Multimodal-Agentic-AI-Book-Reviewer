from typing import TypedDict, Optional


class BookReviewState(TypedDict, total=False):
    # Input
    image_bytes: bytes
    filename: str

    # Vision output
    ocr_confidence: float
    detected_title: str
    detected_author: str

    # Verification output
    verified: bool
    verified_title: str
    verified_author: str
    isbn: str
    category: str
    cover_url: str
    verification_source: str
    verification_confidence: float

    # Retrieval output
    sources: list[dict]
    source_texts: list[str]

    # RAG output
    rag_chunks: list[dict]
    retrieved_context: str
    source_reliability_scores: dict

    # Review output
    summary: str
    best_for: str
    not_ideal_for: str
    public_sentiment: str
    citations: list[dict]

    # Recommendation output
    recommendation: str
    recommendation_reason: str

    # Confidence
    overall_confidence: float
    confidence_breakdown: dict

    # Guardrail output
    is_valid: bool
    guardrail_warnings: list[str]
    final_output: Optional[dict]

    # Metadata
    upload_id: str
    book_id: str
    error: Optional[str]
