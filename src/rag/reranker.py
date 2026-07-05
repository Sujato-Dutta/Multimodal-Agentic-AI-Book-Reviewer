from sentence_transformers import CrossEncoder
from config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

_reranker: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info(f"Loading reranker model: {settings.RERANKER_MODEL}")
        _reranker = CrossEncoder(settings.RERANKER_MODEL)
    return _reranker


def rerank(query: str, documents: list[dict],
           top_k: int = None) -> list[dict]:
    """Cross-encoder reranking of retrieved documents."""
    top_k = top_k or settings.RERANK_TOP_K
    if not documents:
        return []

    reranker = get_reranker()
    texts = [d.get("text", d.get("metadata", {}).get("text", "")) for d in documents]
    pairs = [[query, text] for text in texts]
    scores = reranker.predict(pairs)

    for doc, score in zip(documents, scores):
        doc["rerank_score"] = float(score)

    reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)
    logger.info(f"Reranked {len(documents)} docs, returning top {top_k}")
    return reranked[:top_k]
