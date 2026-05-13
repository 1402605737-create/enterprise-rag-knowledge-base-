from dataclasses import dataclass, field
from typing import List


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    document_name: str
    kb_id: str
    text: str
    page: int = 0
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    chunk: DocumentChunk
    score: float
    source_type: str


@dataclass
class RAGResponse:
    answer: str
    sources: List[dict]
    elapsed_ms: int
