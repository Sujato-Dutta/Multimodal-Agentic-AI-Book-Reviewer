from pinecone import Pinecone
from config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

_index = None


def get_index():
    global _index
    if _index is None:
        if not settings.PINECONE_API_KEY:
            logger.warning("Pinecone API key not set, vector ops will be skipped")
            return None
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _index = pc.Index(settings.PINECONE_INDEX)
        logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX}")
    return _index


def upsert_chunks(chunks: list[dict]):
    """Upsert document chunks. Each chunk: {id, values, metadata}"""
    index = get_index()
    if index is None:
        return
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        vectors = [
            {"id": c["id"], "values": c["values"], "metadata": c["metadata"]}
            for c in batch
        ]
        index.upsert(vectors=vectors)
    logger.info(f"Upserted {len(chunks)} chunks to Pinecone")


def query_similar(query_embedding: list[float], top_k: int = None) -> list[dict]:
    top_k = top_k or settings.RETRIEVAL_TOP_K
    index = get_index()
    if index is None:
        return []
    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return [
        {
            "id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        }
        for match in results.get("matches", [])
    ]


def delete_by_book(book_id: str):
    index = get_index()
    if index is None:
        return
    index.delete(filter={"book_id": book_id})
