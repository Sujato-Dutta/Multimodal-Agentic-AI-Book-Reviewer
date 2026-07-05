from rank_bm25 import BM25Okapi
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BM25Index:
    def __init__(self):
        self._corpus = []
        self._metadata = []
        self._index: BM25Okapi | None = None

    def build(self, documents: list[dict]):
        """Build BM25 index from documents. Each doc: {text, metadata}"""
        self._corpus = [doc["text"].lower().split() for doc in documents]
        self._metadata = [doc.get("metadata", {}) for doc in documents]
        if self._corpus:
            self._index = BM25Okapi(self._corpus)
            logger.info(f"BM25 index built with {len(self._corpus)} documents")

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        if self._index is None or not self._corpus:
            return []
        tokenized_query = query.lower().split()
        scores = self._index.get_scores(tokenized_query)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            {
                "index": idx,
                "score": float(score),
                "text": " ".join(self._corpus[idx]),
                "metadata": self._metadata[idx],
            }
            for idx, score in ranked
            if score > 0
        ]
