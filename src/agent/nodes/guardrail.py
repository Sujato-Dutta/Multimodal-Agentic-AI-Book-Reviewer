import time
from config import settings
from src.agent.state import BookReviewState
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _check_spoilers(text: str) -> list[str]:
    warnings = []
    lower = text.lower()
    for keyword in settings.SPOILER_KEYWORDS:
        if keyword in lower:
            warnings.append(f"Potential spoiler detected: contains '{keyword}'")
    return warnings


def _check_citations(state: BookReviewState) -> list[str]:
    warnings = []
    citations = state.get("citations", [])
    if len(citations) < settings.MIN_CITATIONS_REQUIRED:
        warnings.append(
            f"Insufficient citations: {len(citations)} found, "
            f"minimum {settings.MIN_CITATIONS_REQUIRED} required"
        )
    return warnings


def _check_source_whitelist(state: BookReviewState) -> list[str]:
    warnings = []
    sources = state.get("sources", [])
    for source in sources:
        url = source.get("source_url", "")
        if url and not any(d in url for d in settings.ALLOWED_DOMAINS):
            warnings.append(f"Source outside whitelist: {url}")
    return warnings


def _check_confidence(state: BookReviewState) -> list[str]:
    warnings = []
    confidence = state.get("overall_confidence", 0.0)
    if confidence < settings.MIN_CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Low confidence ({confidence:.0%}): results may be unreliable"
        )
    return warnings


def _check_completeness(state: BookReviewState) -> list[str]:
    warnings = []
    required = ["summary", "recommendation"]
    for field in required:
        if not state.get(field):
            warnings.append(f"Missing required field: {field}")
    return warnings


def guardrail_agent(state: BookReviewState) -> dict:
    start = time.time()
    logger.info("Guardrail Agent: validating output")

    warnings = []
    summary = state.get("summary", "")

    warnings.extend(_check_spoilers(summary))
    warnings.extend(_check_citations(state))
    warnings.extend(_check_source_whitelist(state))
    warnings.extend(_check_confidence(state))
    warnings.extend(_check_completeness(state))

    is_valid = not any(
        w.startswith("Missing required") for w in warnings
    )

    # Low confidence fallback: add disclaimer
    confidence = state.get("overall_confidence", 0.0)
    if confidence < settings.MIN_CONFIDENCE_THRESHOLD:
        summary = (
            f"⚠️ Low confidence result ({confidence:.0%}). "
            f"The following review may not be fully accurate.\n\n{summary}"
        )

    title = state.get("verified_title", state.get("detected_title", "Unknown"))
    author = state.get("verified_author", state.get("detected_author", "Unknown"))

    final_output = {
        "book": {
            "title": title,
            "author": author,
            "category": state.get("category", ""),
            "isbn": state.get("isbn", ""),
            "cover_url": state.get("cover_url", ""),
            "verified": state.get("verified", False),
        },
        "review": {
            "summary": summary,
            "best_for": state.get("best_for", ""),
            "not_ideal_for": state.get("not_ideal_for", ""),
            "public_sentiment": state.get("public_sentiment", ""),
        },
        "recommendation": {
            "action": state.get("recommendation", "borrow"),
            "reason": state.get("recommendation_reason", ""),
        },
        "confidence": {
            "overall": confidence,
            "breakdown": state.get("confidence_breakdown", {}),
        },
        "citations": [
            {
                "source": c.get("source", ""),
                "url": c.get("url", ""),
            }
            for c in state.get("citations", [])
        ],
        "sources": [
            s.get("source_name", "") for s in state.get("sources", [])
        ],
        "warnings": warnings,
    }

    PIPELINE_STAGE_LATENCY.labels(stage="guardrail").observe(time.time() - start)
    logger.info(f"Guardrail passed: {is_valid}, warnings: {len(warnings)}")
    return {
        "is_valid": is_valid,
        "guardrail_warnings": warnings,
        "final_output": final_output,
        "summary": summary,
    }
