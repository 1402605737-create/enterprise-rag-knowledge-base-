[![RAG Evaluation](https://img.shields.io/badge/Recall%405-93%25-brightgreen)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()
[![Status](https://img.shields.io/badge/Status-MVP-brightgreen)]()

# Enterprise RAG — 企业级知识库检索系统

基于RAG（Retrieval-Augmented Generation）技术的企业知识库智能检索与问答系统。
支持PDF/DOCX/TXT/Markdown文档解析、混合检索（向量+BM25）、BGE重排序、引用溯源。

## 结构

```
├── docs/          # 产品文档 (PRD, 竞品分析, 架构, 评估)
├── backend/       # Python FastAPI后端
├── frontend/      # Next.js 前端
├── scripts/       # 数据摄入脚本
├── data/          # 示例文档
└── docker-compose.yml
```
