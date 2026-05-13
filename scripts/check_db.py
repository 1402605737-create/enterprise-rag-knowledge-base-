import sys
sys.path.insert(0, "F:/opencode-config/enterprise-rag-knowledge-base/backend")
from config import CHROMA_PERSIST_DIR
print(f"ChromaDB path: {CHROMA_PERSIST_DIR}")

import chromadb
from chromadb.config import Settings
c = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR, settings=Settings(anonymized_telemetry=False))
coll = c.get_collection("knowledge_base")
count = coll.count()
print(f"Total rows: {count}")

d = coll.get(include=["metadatas"], limit=3)
if d["metadatas"]:
    for m in d["metadatas"][:3]:
        print(f"  kb_id={m.get('kb_id')}, doc={m.get('doc_name')}")
else:
    print("  No metadata found")

kb_ids = set()
all_data = coll.get(include=["metadatas"], limit=count)
for m in all_data["metadatas"]:
    kb_ids.add(m.get("kb_id", ""))
print(f"Unique KB IDs: {kb_ids}")
