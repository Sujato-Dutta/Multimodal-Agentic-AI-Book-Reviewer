import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import settings
from src.agent.state import BookReviewState
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY, CONFIDENCE_DISTRIBUTION
from src.utils.logging import get_logger

logger = get_logger(__name__)

RECOMMENDATION_PROMPT = """Based on the following book review, provide a recommendation.

Book: {title} by {author}
Category: {category}

Review Summary: {summary}
Best For: {best_for}
Not Ideal For: {not_ideal_for}
Public Sentiment: {public_sentiment}
Source Confidence: {confidence:.0%}

Respond in this exact format:
RECOMMENDATION: [buy/borrow/skip]
REASON: [1-2 sentence explanation of why]"""


async def recommendation_agent(state: BookReviewState) -> dict:
    start = time.time()
    title = state.get("verified_title", state.get("detected_title", ""))
    author = state.get("verified_author", state.get("detected_author", ""))
    logger.info(f"Recommendation Agent: generating recommendation for '{title}'")

    # Calculate overall confidence from component scores
    ocr_conf = state.get("ocr_confidence", 0.0)
    ver_conf = state.get("verification_confidence", 0.0)
    source_scores = state.get("source_reliability_scores", {})
    avg_source = sum(source_scores.values()) / len(source_scores) if source_scores else 0.0

    # Weighted confidence
    overall = (ocr_conf * 0.15) + (ver_conf * 0.35) + (avg_source * 0.25) + (0.25 if state.get("summary") else 0.0)
    overall = min(max(overall, 0.0), 1.0)

    confidence_breakdown = {
        "ocr": ocr_conf,
        "verification": ver_conf,
        "source_reliability": avg_source,
        "review_quality": 1.0 if state.get("summary") else 0.0,
    }

    CONFIDENCE_DISTRIBUTION.observe(overall)

    prompt = RECOMMENDATION_PROMPT.format(
        title=title,
        author=author,
        category=state.get("category", ""),
        summary=state.get("summary", ""),
        best_for=state.get("best_for", ""),
        not_ideal_for=state.get("not_ideal_for", ""),
        public_sentiment=state.get("public_sentiment", ""),
        confidence=overall,
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            max_output_tokens=256,
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        text = response.content
        if isinstance(text, list):
            text = " ".join(
                part if isinstance(part, str) else part.get("text", "")
                for part in text
            )

        recommendation = "borrow"
        reason = ""

        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("RECOMMENDATION:"):
                rec = line.split(":", 1)[1].strip().lower()
                if rec in ("buy", "borrow", "skip"):
                    recommendation = rec
            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        PIPELINE_STAGE_LATENCY.labels(stage="recommendation").observe(time.time() - start)
        return {
            "recommendation": recommendation,
            "recommendation_reason": reason,
            "overall_confidence": overall,
            "confidence_breakdown": confidence_breakdown,
        }

    except Exception as e:
        logger.error(f"Recommendation Agent error: {e}")
        PIPELINE_STAGE_LATENCY.labels(stage="recommendation").observe(time.time() - start)
        return {
            "recommendation": "borrow",
            "recommendation_reason": "Unable to determine - defaulting to borrow recommendation.",
            "overall_confidence": overall,
            "confidence_breakdown": confidence_breakdown,
        }
