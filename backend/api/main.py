import os
import uuid
import shutil
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB
from ingestion.ingest import ingest_file, allowed_file
from retrieval.vector_store import get_vector_store
from retrieval.bm25_search import get_bm25
from generation.rag_pipeline import rag_search

app = FastAPI(
    title="Enterprise RAG Knowledge Base",
    description="企业级RAG知识库检索系统API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB_REGISTRY_FILE = os.path.join(PROJECT_ROOT, "data", "kb_registry.json")

knowledge_bases: dict[str, dict] = {}


def _persist_kb_registry():
    os.makedirs(os.path.dirname(KB_REGISTRY_FILE), exist_ok=True)
    with open(KB_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge_bases, f, ensure_ascii=False)


def _load_kb_registry():
    if os.path.exists(KB_REGISTRY_FILE):
        with open(KB_REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            knowledge_bases.update(data)


import threading

# ... existing imports ...

def _auto_init_demo_kb():
    """Auto-create demo KB with sample documents on first startup."""
    if "demo" in knowledge_bases:
        return
    sample_dir = os.path.join(PROJECT_ROOT, "data", "sample-docs")
    if not os.path.isdir(sample_dir):
        return
    knowledge_bases["demo"] = {"name": "云帆科技知识库", "description": "企业示例知识库（自动初始化）"}
    _persist_kb_registry()
    vs = get_vector_store()
    bm25 = get_bm25()
    for filename in sorted(os.listdir(sample_dir)):
        if not allowed_file(filename):
            continue
        file_path = os.path.join(sample_dir, filename)
        chunks = ingest_file(file_path, "demo")
        vs.add_chunks(chunks)
        for chunk in chunks:
            bm25.add(chunk)

_load_kb_registry()
threading.Thread(target=_auto_init_demo_kb, daemon=True).start()


class CreateKBRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    kb_id: Optional[str] = None
    top_k: Optional[int] = 5


class KBInfo(BaseModel):
    kb_id: str
    name: str
    chunk_count: int


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/v1/knowledge-bases")
async def create_knowledge_base(req: CreateKBRequest):
    kb_id = str(uuid.uuid4())[:8]
    knowledge_bases[kb_id] = {"name": req.name, "description": req.description}
    _persist_kb_registry()
    return {"kb_id": kb_id, "name": req.name}


@app.get("/api/v1/knowledge-bases")
async def list_knowledge_bases():
    vs = get_vector_store()
    kbs = []
    for kb_id, info in knowledge_bases.items():
        kbs.append(KBInfo(
            kb_id=kb_id,
            name=info["name"],
            chunk_count=vs.count_by_kb(kb_id),
        ))
    return {"knowledge_bases": kbs}


@app.delete("/api/v1/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    if kb_id not in knowledge_bases:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    vs = get_vector_store()
    vs.delete_by_kb_id(kb_id)
    del knowledge_bases[kb_id]
    _persist_kb_registry()
    return {"message": "Knowledge base deleted"}


@app.post("/api/v1/knowledge-bases/{kb_id}/documents")
async def upload_document(kb_id: str, file: UploadFile = File(...)):
    if kb_id not in knowledge_bases:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: .pdf, .docx, .txt, .md",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        chunks = ingest_file(tmp_path, kb_id)
        vs = get_vector_store()
        vs.add_chunks(chunks)

        bm25 = get_bm25()
        for chunk in chunks:
            bm25.add(chunk)

        return {
            "message": "Document uploaded and indexed",
            "kb_id": kb_id,
            "document_name": file.filename,
            "chunks_count": len(chunks),
        }
    finally:
        os.unlink(tmp_path)


@app.delete("/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}")
async def delete_document(kb_id: str, doc_id: str):
    vs = get_vector_store()
    vs.delete_by_doc_id(doc_id)
    bm25 = get_bm25()
    bm25.remove_by_doc_id(doc_id)
    return {"message": "Document deleted"}


@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = rag_search(query=req.query, kb_id=req.kb_id, top_k=req.top_k)
    return {
        "answer": result.answer,
        "sources": result.sources,
        "elapsed_ms": result.elapsed_ms,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
