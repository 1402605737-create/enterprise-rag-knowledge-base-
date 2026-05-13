import os
from typing import List, Optional
import numpy as np
from rank_bm25 import BM25Okapi
import jieba

from models import DocumentChunk, SearchResult


def _tokenize(text: str) -> List[str]:
    return list(jieba.cut(text))


class BM25Index:
    def __init__(self):
        self.corpus: List[str] = []
        self.chunks: List[DocumentChunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self._index: Optional[BM25Okapi] = None

    def add(self, chunk: DocumentChunk):
        self.corpus.append(chunk.text)
        self.chunks.append(chunk)
        self.tokenized_corpus.append(_tokenize(chunk.text))
        self._index = BM25Okapi(self.tokenized_corpus)

    def remove_by_doc_id(self, doc_id: str):
        indices_to_keep = [
            i for i, c in enumerate(self.chunks) if c.document_id != doc_id
        ]
        self.corpus = [self.corpus[i] for i in indices_to_keep]
        self.chunks = [self.chunks[i] for i in indices_to_keep]
        self.tokenized_corpus = [self.tokenized_corpus[i] for i in indices_to_keep]
        self._index = BM25Okapi(self.tokenized_corpus) if self.corpus else None

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        if self._index is None or not self.corpus:
            return []
        tokenized_query = _tokenize(query)
        scores = self._index.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(
                chunk=self.chunks[i],
                score=float(scores[i]),
                source_type="bm25",
            )
            for i in top_indices
            if scores[i] > 0
        ]


bm25_index = BM25Index()


def get_bm25() -> BM25Index:
    return bm25_index
