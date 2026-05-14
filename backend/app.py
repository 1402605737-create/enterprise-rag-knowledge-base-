import os, json, time, uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / "backend" / ".env")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

import jieba
from rank_bm25 import BM25Okapi
import pypdf, docx

# ── Document store (in-memory) ──
documents = []
bm25_index = None
tokenized_corpus = []


def _tokenize(text):
    return list(jieba.cut(text))


def extract_text(file_path: str) -> list[str]:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        reader = pypdf.PdfReader(file_path)
        return [p.extract_text() or "" for p in reader.pages]
    elif ext == ".docx":
        doc = docx.Document(file_path)
        return [p.text for p in doc.paragraphs if p.text.strip()]
    elif ext in (".txt", ".md"):
        return [Path(file_path).read_text(encoding="utf-8")]
    return []


def chunk_text(text: str, chunk_size=512, overlap=50) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks, pos = [], 0
    while pos < len(text):
        end = min(pos + chunk_size, len(text))
        chunks.append(text[pos:end])
        pos += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def search(query: str, top_k=5) -> list[dict]:
    global bm25_index
    if not documents or bm25_index is None:
        return []
    scores = bm25_index.get_scores(_tokenize(query))
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for i, score in ranked[:top_k]:
        if score <= 0:
            break
        doc = documents[i]
        results.append({
            "text": doc["text"],
            "doc_name": doc["doc_name"],
            "page": doc["page"],
            "score": min(score / 10.0, 1.0),
        })
    return results


def rebuild_index():
    global bm25_index, tokenized_corpus
    tokenized_corpus = [_tokenize(d["text"]) for d in documents]
    bm25_index = BM25Okapi(tokenized_corpus) if tokenized_corpus else None


def ingest_demo():
    sample_dir = PROJECT_ROOT / "data" / "sample-docs"
    if not sample_dir.is_dir():
        return 0
    for fpath in sorted(sample_dir.iterdir()):
        if fpath.suffix.lower() not in {".pdf", ".docx", ".txt", ".md"}:
            continue
        for text in extract_text(str(fpath)):
            for chunk in chunk_text(text):
                documents.append({
                    "id": uuid.uuid4().hex,
                    "text": chunk,
                    "doc_name": fpath.name,
                    "page": len(documents) + 1,
                })
    rebuild_index()
    return len(documents)


# ── FastAPI app ──
app = FastAPI(title="Enterprise RAG Demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/api/v1/health")
async def health():
    debug_dir = str(PROJECT_ROOT / "data" / "sample-docs")
    exists = os.path.isdir(debug_dir)
    files = os.listdir(debug_dir) if exists else []
    return {"status": "ok", "documents": len(documents), "version": "2.0-light", "data_dir": debug_dir, "data_exists": exists, "data_files": len(files)}


@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    try:
        start = time.time()
        hits = search(req.query, req.top_k)

        if not hits:
            return {"answer": "知识库为空，请先上传文档。", "sources": [], "elapsed_ms": int((time.time() - start) * 1000)}

        llm = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        ctx = "\n\n---\n\n".join(f"[{j+1}] 来源: {h['doc_name']} (第{h['page']}页)\n{h['text']}" for j, h in enumerate(hits))
        prompt = f"""你是企业知识库助手。仅用参考资料回答。

## 规则
1. 仅用参考资料中的信息
2. 不足时说"根据现有资料无法回答"
3. 关键信息后标注来源 [1]、[2]
4. 简洁专业

## 参考资料
{ctx}

## 问题
{req.query}"""

        resp = llm.chat.completions.create(model=LLM_MODEL, messages=[
            {"role": "system", "content": "你是专业的企业知识库助手。"},
            {"role": "user", "content": prompt},
        ], temperature=0.3, max_tokens=1024)

        sources = [{"ref": j+1, "document_name": h["doc_name"], "page": h["page"],
                     "text": h["text"][:300], "score": round(h["score"], 4)} for j, h in enumerate(hits)]

        return {"answer": resp.choices[0].message.content, "sources": sources,
                "elapsed_ms": int((time.time() - start) * 1000)}
    except Exception as e:
        return {"answer": f"错误: {str(e)}", "sources": [], "elapsed_ms": 0}


@app.post("/api/v1/documents/upload")
async def upload_doc(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in {".pdf", ".docx", ".txt", ".md"}:
        raise HTTPException(400, "不支持的文件格式")
    tmp = f"/tmp/{uuid.uuid4().hex}{ext}"
    os.makedirs("/tmp", exist_ok=True)
    with open(tmp, "wb") as f:
        f.write(await file.read())
    count = 0
    for text in extract_text(tmp):
        for chunk in chunk_text(text):
            documents.append({"id": uuid.uuid4().hex, "text": chunk, "doc_name": file.filename, "page": count + 1})
            count += 1
    os.unlink(tmp)
    rebuild_index()
    return {"message": f"上传成功", "chunks": count, "total": len(documents)}


@app.get("/api/v1/knowledge-bases")
async def list_kbs():
    return {"knowledge_bases": [{"kb_id": "demo", "name": "云帆科技知识库", "chunk_count": len(documents)}]}


# ── Startup ──
@app.on_event("startup")
async def startup():
    count = ingest_demo()
    print(f"Auto-ingested {count} chunks from sample docs")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
