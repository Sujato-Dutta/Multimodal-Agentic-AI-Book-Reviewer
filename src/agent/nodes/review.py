import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import settings
from src.agent.state import BookReviewState
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY, API_ERRORS
from src.utils.logging import get_logger

logger = get_logger(__name__)

REVIEW_PROMPT = """You are a professional book reviewer. Based on the verified book information and retrieved sources below, generate a comprehensive, spoiler-free review.

Book: {title}
Author: {author}
Category: {category}

Retrieved Context:
{context}

Generate the review in this exact format:
SUMMARY: [A spoiler-free summary of what the book is about, 2-3 sentences]
BEST_FOR: [Types of readers who would enjoy this book]
NOT_IDEAL_FOR: [Types of readers who might not enjoy this book]
PUBLIC_SENTIMENT: [What most readers and critics say about this book]
CITATIONS: [List the source names used, separated by commas]

Rules:
- Never reveal plot twists, endings, or major spoilers
- Be specific and informative
- Base claims on the provided sources
- If sources are insufficient, say so honestly"""


def _parse_review(text: str) -> dict:
    sections = {}
    current_key = None
    current_value = []

    for line in text.split("\n"):
        line = line.strip()
        for key in ["SUMMARY:", "BEST_FOR:", "NOT_IDEAL_FOR:", "PUBLIC_SENTIMENT:", "CITATIONS:"]:
            if line.upper().startswith(key):
                if current_key:
                    sections[current_key] = " ".join(current_value).strip()
                current_key = key.rstrip(":")
                current_value = [line[len(key):].strip()]
                break
        else:
            if current_key and line:
                current_value.append(line)

    if current_key:
        sections[current_key] = " ".join(current_value).strip()

    citations_str = sections.get("CITATIONS", "")
    citations = [
        {"source": c.strip()} for c in citations_str.split(",") if c.strip()
    ]

    return {
        "summary": sections.get("SUMMARY", ""),
        "best_for": sections.get("BEST_FOR", ""),
        "not_ideal_for": sections.get("NOT_IDEAL_FOR", ""),
        "public_sentiment": sections.get("PUBLIC_SENTIMENT", ""),
        "citations": citations,
    }


async def review_agent(state: BookReviewState) -> dict:
    start = time.time()
    title = state.get("verified_title", state.get("detected_title", ""))
    author = state.get("verified_author", state.get("detected_author", ""))
    category = state.get("category", "")
    context = state.get("retrieved_context", "")
    logger.info(f"Review Agent: generating review for '{title}'")

    if not context:
        context = "No detailed sources available. Generate based on general knowledge."

    prompt = REVIEW_PROMPT.format(
        title=title, author=author, category=category, context=context
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            max_output_tokens=settings.LLM_MAX_TOKENS,
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                part if isinstance(part, str) else part.get("text", "")
                for part in content
            )
        parsed = _parse_review(content)

        PIPELINE_STAGE_LATENCY.labels(stage="review").observe(time.time() - start)
        logger.info("Review generated successfully")
        return parsed

    except Exception as e:
        logger.error(f"Review Agent error: {e}")
        API_ERRORS.labels(source="gemini", error_type=type(e).__name__).inc()
        PIPELINE_STAGE_LATENCY.labels(stage="review").observe(time.time() - start)
        return {
            "summary": "Unable to generate review due to an error.",
            "best_for": "",
            "not_ideal_for": "",
            "public_sentiment": "",
            "citations": [],
            "error": str(e),
        }
