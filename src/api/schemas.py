from pydantic import BaseModel, Field
from typing import Optional


class BookInfo(BaseModel):
    title: str = ""
    author: str = ""
    category: str = ""
    isbn: str = ""
    cover_url: str = ""
    verified: bool = False


class ReviewInfo(BaseModel):
    summary: str = ""
    best_for: str = ""
    not_ideal_for: str = ""
    public_sentiment: str = ""


class RecommendationInfo(BaseModel):
    action: str = "borrow"
    reason: str = ""


class ConfidenceInfo(BaseModel):
    overall: float = 0.0
    breakdown: dict = Field(default_factory=dict)


class CitationInfo(BaseModel):
    source: str = ""
    url: str = ""


class AnalyzeResponse(BaseModel):
    book: BookInfo = Field(default_factory=BookInfo)
    review: ReviewInfo = Field(default_factory=ReviewInfo)
    recommendation: RecommendationInfo = Field(default_factory=RecommendationInfo)
    confidence: ConfidenceInfo = Field(default_factory=ConfidenceInfo)
    citations: list[CitationInfo] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    book_id: str
    rating: str = Field(pattern=r"^(helpful|not_helpful)$")
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "ok"
    message: str = "Feedback recorded"


class HealthResponse(BaseModel):
    status: str = "healthy"
    environment: str = ""
    version: str = "1.0.0"
