from config import settings
from src.rag.embeddings import embed_query, embed_texts
from src.rag.pinecone_store import query_similar, upsert_chunks
from src.rag.bm25 import BM25Index
from src.utils.logging import get_logger
import hashlib

logger = get_logger(__name__)


def chunk_text(text: str, source_name: str, book_id: str,
               chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """Source-aware chunking with overlap."""
    chunks = []
    words = text.split()
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if not chunk_words:
            break
        chunk_text = " ".join(chunk_words)
        chunk_id = hashlib.md5(f"{book_id}:{source_name}:{i}".encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "text": chunk_text,
            "metadata": {
                "book_id": book_id,
                "source": source_name,
                "chunk_index": i,
            },
        })
    return chunks


def reciprocal_rank_fusion(dense_results: list[dict], sparse_results: list[dict],
                           k: int = None) -> list[dict]:
    """RRF combining dense (Pinecone) and sparse (BM25) results."""
    k = k or settings.RRF_K
    scores = {}

    for rank, result in enumerate(dense_results):
        doc_id = result.get("id") or result.get("metadata", {}).get("source", str(rank))
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        if doc_id not in scores:
            scores[doc_id] = {"score": 0, "data": result}
        if isinstance(scores[doc_id], float):
            scores[doc_id] = {"score": scores[doc_id], "data": result}

    for rank, result in enumerate(sparse_results):
        doc_id = result.get("metadata", {}).get("source", f"bm25_{rank}")
        if doc_id in scores:
            scores[doc_id]["score"] += 1.0 / (k + rank + 1)
        else:
            scores[doc_id] = {
                "score": 1.0 / (k + rank + 1),
                "data": result,
            }

    fused = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    return [{"id": doc_id, "rrf_score": info["score"], **info["data"]}
            for doc_id, info in fused]


def index_sources(sources: list[dict], book_id: str):
    """Index source documents into both Pinecone and prepare for BM25."""
    all_chunks = []
    for source in sources:
        chunks = chunk_text(
            text=source.get("content", ""),
            source_name=source.get("source_name", "unknown"),
            book_id=book_id,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        return []

    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)

    pinecone_vectors = [
        {"id": c["id"], "values": emb, "metadata": c["metadata"]}
        for c, emb in zip(all_chunks, embeddings)
    ]
    upsert_chunks(pinecone_vectors)
    return all_chunks


def hybrid_retrieve(query: str, chunks: list[dict],
                    top_k: int = None) -> list[dict]:
    """Hybrid retrieval: dense (Pinecone) + sparse (BM25) with RRF."""
    top_k = top_k or settings.RETRIEVAL_TOP_K

    query_emb = embed_query(query)
    dense_results = query_similar(query_emb, top_k=top_k)

    bm25 = BM25Index()
    bm25.build([{"text": c["text"], "metadata": c["metadata"]} for c in chunks])
    sparse_results = bm25.search(query, top_k=top_k)

    fused = reciprocal_rank_fusion(dense_results, sparse_results)
    logger.info(f"Hybrid retrieval returned {len(fused)} results")
    return fused[:top_k]
