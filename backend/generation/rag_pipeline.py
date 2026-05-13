from typing import List
import time

from models import DocumentChunk, SearchResult, RAGResponse
from retrieval.vector_store import get_vector_store
from retrieval.bm25_search import get_bm25
from retrieval.reranker import get_reranker

FUSION_ALPHA = 0.7


def _merge_results(
    vector_results: List[SearchResult],
    bm25_results: List[SearchResult],
    alpha: float = FUSION_ALPHA,
    top_k: int = 20,
) -> List[SearchResult]:
    all_results: dict[str, tuple[SearchResult, float]] = {}

    for r in vector_results:
        score = alpha * r.score
        all_results[r.chunk.chunk_id] = (r, score)

    for r in bm25_results:
        score = (1 - alpha) * _normalize_bm25(r.score)
        if r.chunk.chunk_id in all_results:
            existing_r, existing_score = all_results[r.chunk.chunk_id]
            all_results[r.chunk.chunk_id] = (existing_r, existing_score + score)
        else:
            all_results[r.chunk.chunk_id] = (r, score)

    sorted_results = sorted(all_results.values(), key=lambda x: x[1], reverse=True)
    merged = []
    for result, score in sorted_results[:top_k]:
        result.score = score
        result.source_type = "hybrid"
        merged.append(result)
    return merged


def _normalize_bm25(score: float) -> float:
    return min(max(score / 10.0, 0.0), 1.0)


def rag_search(query: str, kb_id: str = None, top_k: int = 5) -> RAGResponse:
    start = time.time()

    vs = get_vector_store()
    bm25 = get_bm25()
    reranker = get_reranker()

    vector_results = vs.search(query, kb_id=kb_id, top_k=20)
    bm25_results = bm25.search(query, top_k=10)

    merged = _merge_results(vector_results, bm25_results)

    reranked = reranker.rerank(query, merged, top_k=top_k)

    from generation.llm_gen import generate_answer
    answer, sources = generate_answer(query, reranked)

    elapsed = int((time.time() - start) * 1000)

    return RAGResponse(answer=answer, sources=sources, elapsed_ms=elapsed)
