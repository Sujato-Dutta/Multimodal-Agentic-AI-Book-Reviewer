import httpx
import time
from ddgs import DDGS
from config import settings
from src.agent.state import BookReviewState
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY, RETRIEVAL_FAILURES
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "source_name": r.get("href", "").split("/")[2] if "/" in r.get("href", "") else "web",
                "source_url": r.get("href", ""),
                "content": r.get("body", ""),
                "title": r.get("title", ""),
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")
        RETRIEVAL_FAILURES.labels(source="duckduckgo").inc()
        return []


async def _fetch_google_books_description(title: str, author: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                settings.GOOGLE_BOOKS_API_URL,
                params={"q": f"{title} {author}", "maxResults": 1},
            )
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items", [])
        if not items:
            return None

        vol = items[0]["volumeInfo"]
        description = vol.get("description", "")
        if not description:
            return None

        return {
            "source_name": "books.google.com",
            "source_url": vol.get("infoLink", ""),
            "content": description,
            "title": f"Google Books - {vol.get('title', '')}",
        }
    except Exception as e:
        logger.warning(f"Google Books description fetch error: {e}")
        RETRIEVAL_FAILURES.labels(source="google_books").inc()
        return None


async def _fetch_open_library_description(title: str, author: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            search_resp = await client.get(
                f"{settings.OPEN_LIBRARY_API_URL}/search.json",
                params={"q": f"{title} {author}", "limit": 1},
            )
            search_resp.raise_for_status()
            docs = search_resp.json().get("docs", [])
            if not docs:
                return None

            work_key = docs[0].get("key", "")
            if not work_key:
                return None

            work_resp = await client.get(
                f"{settings.OPEN_LIBRARY_API_URL}{work_key}.json"
            )
            work_resp.raise_for_status()
            work_data = work_resp.json()

        description = work_data.get("description", "")
        if isinstance(description, dict):
            description = description.get("value", "")

        if not description:
            return None

        return {
            "source_name": "openlibrary.org",
            "source_url": f"https://openlibrary.org{work_key}",
            "content": description,
            "title": f"Open Library - {docs[0].get('title', '')}",
        }
    except Exception as e:
        logger.warning(f"Open Library description fetch error: {e}")
        RETRIEVAL_FAILURES.labels(source="open_library").inc()
        return None


def _compute_reliability(source_name: str) -> float:
    for domain, weight in settings.SOURCE_WEIGHTS.items():
        if domain in source_name:
            return weight
    return 0.5


async def retrieval_agent(state: BookReviewState) -> dict:
    start = time.time()
    title = state.get("verified_title", state.get("detected_title", ""))
    author = state.get("verified_author", state.get("detected_author", ""))
    logger.info(f"Retrieval Agent: gathering sources for '{title}' by '{author}'")

    sources = []

    ddg_results = _search_duckduckgo(
        f"{title} {author} book review summary", max_results=5
    )
    sources.extend(ddg_results)

    google_desc = await _fetch_google_books_description(title, author)
    if google_desc:
        sources.append(google_desc)

    ol_desc = await _fetch_open_library_description(title, author)
    if ol_desc:
        sources.append(ol_desc)

    # Filter to allowed domains where possible, keep all if too few results
    filtered = [
        s for s in sources
        if any(d in s.get("source_url", "") for d in settings.ALLOWED_DOMAINS)
    ]
    if len(filtered) < 2:
        filtered = sources

    for s in filtered:
        s["reliability_score"] = _compute_reliability(s.get("source_name", ""))

    source_texts = [s.get("content", "") for s in filtered if s.get("content")]

    PIPELINE_STAGE_LATENCY.labels(stage="retrieval").observe(time.time() - start)
    logger.info(f"Retrieved {len(filtered)} sources with {len(source_texts)} text snippets")
    return {
        "sources": filtered,
        "source_texts": source_texts,
    }
