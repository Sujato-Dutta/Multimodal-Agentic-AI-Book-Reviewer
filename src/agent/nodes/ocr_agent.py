import base64
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import settings
from src.agent.state import BookReviewState
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY, API_ERRORS
from src.utils.logging import get_logger

logger = get_logger(__name__)

VISION_PROMPT = """Analyze this book cover image. Extract the following information:

TITLE: [The book title as shown on the cover]
AUTHOR: [The author name as shown on the cover]

Rules:
- Extract exactly what is printed on the cover
- If you cannot determine the title or author, respond with UNKNOWN
- Do not guess or infer — only extract visible text"""


def _parse_vision_response(text: str) -> tuple[str, str]:
    title = ""
    author = ""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            title = line.split(":", 1)[1].strip().strip('"').strip("*")
        elif line.upper().startswith("AUTHOR:"):
            author = line.split(":", 1)[1].strip().strip('"').strip("*")
    return title, author


async def vision_agent(state: BookReviewState) -> dict:
    start = time.time()
    logger.info("Vision Agent: extracting text from book cover via Gemini")

    try:
        image_bytes = state["image_bytes"]
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        llm = ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        message = HumanMessage(
            content=[
                {"type": "text", "text": VISION_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ]
        )

        response = await llm.ainvoke([message])
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                part if isinstance(part, str) else part.get("text", "")
                for part in content
            )
        title, author = _parse_vision_response(content)

        confidence = 0.9 if (title and title != "UNKNOWN") else 0.0

        logger.info(f"Vision extracted - Title: '{title}', Author: '{author}'")
        PIPELINE_STAGE_LATENCY.labels(stage="vision").observe(time.time() - start)

        return {
            "detected_title": title if title != "UNKNOWN" else "",
            "detected_author": author if author != "UNKNOWN" else "",
            "ocr_confidence": confidence,
        }

    except Exception as e:
        logger.error(f"Vision Agent error: {e}")
        API_ERRORS.labels(source="gemini_vision", error_type=type(e).__name__).inc()
        PIPELINE_STAGE_LATENCY.labels(stage="vision").observe(time.time() - start)
        return {
            "detected_title": "",
            "detected_author": "",
            "ocr_confidence": 0.0,
            "error": f"Vision extraction failed: {str(e)}",
        }
