import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

import argparse
from ingestion.ingest import ingest_file, allowed_file
from retrieval.vector_store import get_vector_store
from retrieval.bm25_search import get_bm25


def main():
    parser = argparse.ArgumentParser(description="RAG Knowledge Base - Sample Data Ingest")
    parser.add_argument("--kb-id", default="demo", help="Knowledge base ID")
    parser.add_argument("--kb-name", default="云帆科技知识库", help="Knowledge base name")
    parser.add_argument("--data-dir", default=os.path.join(PROJECT_ROOT, "data", "sample-docs"), help="Directory with sample documents")
    args = parser.parse_args()

    kb_id = args.kb_id
    data_dir = args.data_dir

    from api.main import knowledge_bases
    knowledge_bases[kb_id] = {"name": args.kb_name, "description": "企业示例知识库"}

    vs = get_vector_store()
    bm25 = get_bm25()

    total_chunks = 0
    for filename in os.listdir(data_dir):
        if not allowed_file(filename):
            continue
        file_path = os.path.join(data_dir, filename)
        print(f"正在处理: {filename}")
        chunks = ingest_file(file_path, kb_id)
        vs.add_chunks(chunks)
        for chunk in chunks:
            bm25.add(chunk)
        total_chunks += len(chunks)
        print(f"  -> {len(chunks)} 个切片已入库")

    print(f"\n总计 {total_chunks} 个切片已摄入知识库 '{args.kb_name}'")
    print(f"知识库ID: {kb_id}")


if __name__ == "__main__":
    main()
