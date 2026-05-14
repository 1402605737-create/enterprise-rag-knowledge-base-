from typing import List
from models import SearchResult


class Reranker:
    def rerank(self, query: str, results: List[SearchResult], top_k: int = 5) -> List[SearchResult]:
        return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]


reranker = Reranker()


def get_reranker() -> Reranker:
    return reranker
