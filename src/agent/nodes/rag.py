import time
from src.agent.state import BookReviewState
from src.rag.hybrid import index_sources, hybrid_retrieve
from src.rag.reranker import rerank
from src.monitoring.metrics import PIPELINE_STAGE_LATENCY
from src.utils.logging import get_logger
from config import settings

logger = get_logger(__name__)


def rag_agent(state: BookReviewState) -> dict:
    start = time.time()
    title = state.get("verified_title", state.get("detected_title", ""))
    author = state.get("verified_author", state.get("detected_author", ""))
    sources = state.get("sources", [])
    logger.info(f"RAG Agent: processing {len(sources)} sources for '{title}'")

    if not sources:
        PIPELINE_STAGE_LATENCY.labels(stage="rag").observe(time.time() - start)
        return {
            "rag_chunks": [],
            "retrieved_context": "",
            "source_reliability_scores": {},
        }

    book_id = state.get("book_id", "unknown")
    indexed_chunks = index_sources(sources, book_id)

    query = f"{title} by {author} book review summary themes audience"
    hybrid_results = hybrid_retrieve(query, indexed_chunks)

    reranked = rerank(query, hybrid_results, top_k=settings.RERANK_TOP_K)

    # Build citation-aware context
    context_parts = []
    reliability_scores = {}
    for chunk in reranked:
        source = chunk.get("metadata", {}).get("source", "unknown")
        text = chunk.get("text", "")
        if text:
            context_parts.append(f"[Source: {source}]\n{text}")
            if source not in reliability_scores:
                reliability_scores[source] = chunk.get("rerank_score", 0.5)

    retrieved_context = "\n\n".join(context_parts)

    PIPELINE_STAGE_LATENCY.labels(stage="rag").observe(time.time() - start)
    logger.info(f"RAG produced context from {len(reranked)} chunks")
    return {
        "rag_chunks": reranked,
        "retrieved_context": retrieved_context,
        "source_reliability_scores": reliability_scores,
    }
