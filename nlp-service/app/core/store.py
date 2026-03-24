"""
In-memory FAISS vector store.
- Stores documents as embeddings using sentence-transformers.
- Supports add, search (bi-encoder), re-rank (cross-encoder), and clear.
- State is in-memory only; resets on service restart.
"""
import numpy as np
import faiss
from app.core.config import settings

_bi_encoder = None
_cross_encoder = None

# In-memory store
_index: faiss.IndexFlatIP | None = None
_documents: list[dict] = []   # [{id, text, metadata}]
_dim: int = 0


def _load_bi():
    global _bi_encoder
    if _bi_encoder is None:
        from sentence_transformers import SentenceTransformer
        _bi_encoder = SentenceTransformer(settings.EMBED_MODEL)


def _load_cross():
    global _cross_encoder
    if _cross_encoder is None:
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder(settings.CROSS_ENCODER_MODEL)


def _embed(texts: list[str]) -> np.ndarray:
    _load_bi()
    vecs = _bi_encoder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vecs.astype("float32")


def _get_index(dim: int) -> faiss.IndexFlatIP:
    global _index, _dim
    if _index is None or _dim != dim:
        _index = faiss.IndexFlatIP(dim)   # Inner product = cosine on normalized vecs
        _dim = dim
    return _index


# ── Public API ──────────────────────────────────────────────────────────────

def add_documents(docs: list[dict]) -> int:
    """
    Add documents to the index.
    Each doc: {text: str, metadata: dict (optional)}
    Returns total document count.
    """
    global _documents
    texts = [d["text"] for d in docs]
    vecs = _embed(texts)
    idx = _get_index(vecs.shape[1])
    idx.add(vecs)
    for i, doc in enumerate(docs):
        _documents.append({
            "id": len(_documents),
            "text": doc["text"],
            "metadata": doc.get("metadata", {}),
        })
    return len(_documents)


def search(query: str, top_k: int | None = None, rerank: bool = True) -> list[dict]:
    """Semantic search with optional cross-encoder re-ranking."""
    if _index is None or _index.ntotal == 0:
        return []

    k = min(top_k or settings.TOP_K, _index.ntotal)
    q_vec = _embed([query])
    scores, indices = _index.search(q_vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        doc = _documents[idx]
        results.append({
            "id": doc["id"],
            "text": doc["text"],
            "metadata": doc["metadata"],
            "bi_score": round(float(score), 4),
        })

    if rerank and results:
        _load_cross()
        pairs = [[query, r["text"]] for r in results]
        ce_scores = _cross_encoder.predict(pairs)
        for r, s in zip(results, ce_scores):
            r["score"] = round(float(s), 4)
        results.sort(key=lambda x: x["score"], reverse=True)
    else:
        for r in results:
            r["score"] = r["bi_score"]

    return results


def find_duplicates(texts: list[str], threshold: float | None = None) -> list[dict]:
    """
    Find duplicate/near-duplicate pairs within a list of texts.
    Returns pairs with similarity above threshold.
    """
    thresh = threshold if threshold is not None else settings.DUPLICATE_THRESHOLD
    if len(texts) < 2:
        return []

    vecs = _embed(texts)
    # Compute all pairwise cosine similarities (vecs are normalized)
    sim_matrix = np.dot(vecs, vecs.T)

    pairs = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = float(sim_matrix[i, j])
            if sim >= thresh:
                pairs.append({
                    "text_a": texts[i],
                    "text_b": texts[j],
                    "similarity": round(sim, 4),
                    "is_duplicate": True,
                })

    pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return pairs


def get_stats() -> dict:
    return {
        "total_documents": len(_documents),
        "index_size": _index.ntotal if _index else 0,
        "embed_model": settings.EMBED_MODEL,
        "duplicate_threshold": settings.DUPLICATE_THRESHOLD,
    }


def clear_index():
    global _index, _documents
    _index = None
    _documents = []
