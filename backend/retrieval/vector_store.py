from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, EMBEDDING_DEVICE
from models import DocumentChunk, SearchResult

COLLECTION_NAME = "knowledge_base"


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedding_model: Optional[SentenceTransformer] = None

    def _get_embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(
                EMBEDDING_MODEL,
                device=EMBEDDING_DEVICE,
            )
        return self._embedding_model

    def _embed(self, texts: List[str]) -> List[List[float]]:
        model = self._get_embedding_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def add_chunks(self, chunks: List[DocumentChunk]):
        if not chunks:
            return
        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "kb_id": c.kb_id,
                "doc_id": c.document_id,
                "doc_name": c.document_name,
                "page": c.page,
                "chunk_index": c.chunk_index,
                "total_chunks": c.metadata.get("total_chunks", 0),
            }
            for c in chunks
        ]
        embeddings = self._embed(documents)
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)

    def search(self, query: str, kb_id: str = None, top_k: int = 20) -> List[SearchResult]:
        query_embedding = self._embed([query])[0]
        where_filter = {"kb_id": kb_id} if kb_id else None
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                score = 1.0 - (distance / 2.0)
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=metadata.get("doc_id", ""),
                    document_name=metadata.get("doc_name", ""),
                    kb_id=metadata.get("kb_id", ""),
                    text=results["documents"][0][i],
                    page=metadata.get("page", 0),
                    chunk_index=metadata.get("chunk_index", 0),
                    metadata=metadata,
                )
                search_results.append(SearchResult(chunk=chunk, score=score, source_type="vector"))
        return search_results

    def delete_by_doc_id(self, doc_id: str):
        existing = self.collection.get(where={"doc_id": doc_id})
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])

    def delete_by_kb_id(self, kb_id: str):
        existing = self.collection.get(where={"kb_id": kb_id})
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])

    def count_by_kb(self, kb_id: str) -> int:
        try:
            existing = self.collection.get(where={"kb_id": kb_id})
            return len(existing["ids"]) if existing["ids"] else 0
        except Exception:
            return 0


vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    return vector_store
