from typing import List, Optional
from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL, EMBEDDING_DEVICE
from models import SearchResult


class Reranker:
    def __init__(self):
        self._model: Optional[CrossEncoder] = None

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(RERANKER_MODEL, device=EMBEDDING_DEVICE)
        return self._model

    def rerank(self, query: str, results: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        if not results:
            return []

        model = self._get_model()
        pairs = [(query, r.chunk.text) for r in results]
        scores = model.predict(pairs)

        scored = list(zip(results, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for result, score in scored[:top_k]:
            result.score = float(score)
            result.source_type = "reranked"
            reranked.append(result)
        return reranked


reranker = Reranker()


def get_reranker() -> Reranker:
    return reranker
