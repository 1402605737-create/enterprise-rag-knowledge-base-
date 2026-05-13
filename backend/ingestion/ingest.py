import os
import uuid
import hashlib
from typing import List
import pypdf
import docx

from config import UPLOAD_DIR
from models import DocumentChunk


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 50

SEPARATORS = ["\n## ", "\n### ", "\n#### ", "\n", "。", ".", "；", ";", " "]


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext in (".txt", ".md"):
        return _extract_text(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(file_path: str) -> str:
    text_parts = []
    with open(file_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts)


def _extract_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    separators: List[str] = None,
) -> List[str]:
    if separators is None:
        separators = SEPARATORS

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    pos = 0
    while pos < len(text):
        end = pos + chunk_size
        if end >= len(text):
            chunks.append(text[pos:].strip())
            break

        boundary = end
        for sep in separators:
            search_start = max(end - chunk_overlap, pos)
            idx = text.find(sep, search_start, end + chunk_overlap)
            if idx != -1:
                boundary = idx + len(sep)
                break

        chunks.append(text[pos:boundary].strip())
        pos = boundary - chunk_overlap if boundary - chunk_overlap > pos else boundary

    return [c for c in chunks if c.strip()]


def ingest_file(file_path: str, kb_id: str, doc_id: str = None) -> List[DocumentChunk]:
    doc_name = os.path.basename(file_path)
    text = extract_text(file_path)
    chunk_texts = chunk_text(text)

    if doc_id is None:
        doc_id = hashlib.md5(doc_name.encode()).hexdigest()[:12]

    chunks = []
    for i, ct in enumerate(chunk_texts):
        chunk = DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            document_id=doc_id,
            document_name=doc_name,
            kb_id=kb_id,
            text=ct,
            page=i + 1,
            chunk_index=i,
            metadata={"total_chunks": len(chunk_texts)},
        )
        chunks.append(chunk)

    return chunks
