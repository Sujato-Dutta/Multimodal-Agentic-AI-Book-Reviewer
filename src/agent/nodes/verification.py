import httpx
import time
from config import settings
from src.agent.state import BookReviewState
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY, API_ERRORS
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def _search_google_books(title: str, author: str) -> dict | None:
    query = f"{title} {author}".strip()
    if not query:
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                settings.GOOGLE_BOOKS_API_URL,
                params={"q": query, "maxResults": 3},
            )
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        vol = items[0]["volumeInfo"]
        return {
            "title": vol.get("title", ""),
            "authors": vol.get("authors", []),
            "isbn": next(
                (i["identifier"] for i in vol.get("industryIdentifiers", [])
                 if i["type"] in ("ISBN_13", "ISBN_10")),
                "",
            ),
            "categories": vol.get("categories", []),
            "cover_url": vol.get("imageLinks", {}).get("thumbnail", ""),
            "source": "google_books",
        }
    except Exception as e:
        logger.warning(f"Google Books API error: {e}")
        API_ERRORS.labels(source="google_books", error_type=type(e).__name__).inc()
        return None


async def _search_open_library(title: str, author: str) -> dict | None:
    query = f"{title} {author}".strip()
    if not query:
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.OPEN_LIBRARY_API_URL}/search.json",
                params={"q": query, "limit": 3},
            )
            resp.raise_for_status()
            data = resp.json()

        docs = data.get("docs", [])
        if not docs:
            return None

        doc = docs[0]
        isbn_list = doc.get("isbn", [])
        cover_id = doc.get("cover_i")
        return {
            "title": doc.get("title", ""),
            "authors": doc.get("author_name", []),
            "isbn": isbn_list[0] if isbn_list else "",
            "categories": doc.get("subject", [])[:5],
            "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else "",
            "source": "open_library",
        }
    except Exception as e:
        logger.warning(f"Open Library API error: {e}")
        API_ERRORS.labels(source="open_library", error_type=type(e).__name__).inc()
        return None


def _match_score(detected: str, candidate: str) -> float:
    if not detected or not candidate:
        return 0.0
    d = detected.lower().strip()
    c = candidate.lower().strip()
    if d == c:
        return 1.0
    if d in c or c in d:
        return 0.8
    d_words = set(d.split())
    c_words = set(c.split())
    if not d_words:
        return 0.0
    overlap = len(d_words & c_words) / max(len(d_words), len(c_words))
    return overlap


async def verification_agent(state: BookReviewState) -> dict:
    start = time.time()
    title = state.get("detected_title", "")
    author = state.get("detected_author", "")
    logger.info(f"Verification Agent: verifying '{title}' by '{author}'")

    google_result = await _search_google_books(title, author)
    ol_result = await _search_open_library(title, author)

    best_result = None
    best_score = 0.0
    best_source = ""

    for result, source_name in [(google_result, "google_books"), (ol_result, "open_library")]:
        if result is None:
            continue
        title_score = _match_score(title, result["title"])
        author_score = max(
            (_match_score(author, a) for a in result.get("authors", [""])),
            default=0.0,
        )
        combined = (title_score * 0.6) + (author_score * 0.4)
        if combined > best_score:
            best_score = combined
            best_result = result
            best_source = source_name

    if best_result and best_score > 0.4:
        verified_author = best_result["authors"][0] if best_result["authors"] else author
        categories = best_result.get("categories", [])
        result = {
            "verified": True,
            "verified_title": best_result["title"],
            "verified_author": verified_author,
            "isbn": best_result.get("isbn", ""),
            "category": categories[0] if categories else "",
            "cover_url": best_result.get("cover_url", ""),
            "verification_source": best_source,
            "verification_confidence": best_score,
        }
    else:
        result = {
            "verified": False,
            "verified_title": title,
            "verified_author": author,
            "isbn": "",
            "category": "",
            "cover_url": "",
            "verification_source": "",
            "verification_confidence": 0.0,
        }

    PIPELINE_STAGE_LATENCY.labels(stage="verification").observe(time.time() - start)
    logger.info(f"Verification result: verified={result['verified']}, confidence={result.get('verification_confidence', 0):.2f}")
    return result
