# Enterprise RAG Knowledge Base — 企业级RAG知识库检索系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js" />
  <img src="https://img.shields.io/badge/ChromaDB-0.5-orange?logo=chroma" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</p>

> **AI产品经理作品集项目** — 从产品设计到技术落地的完整RAG系统实现
>
> 演示视频 / 在线Demo: *部署后补充链接*

## 项目概述

一款面向企业内部的知识库智能检索与问答系统。支持自然语言提问，基于RAG（Retrieval-Augmented Generation）技术从企业文档中精准检索信息并生成回答，且每条回答均标注引用来源。

### 核心功能

| 功能 | 说明 |
|------|------|
| 多知识库管理 | 创建多个知识库，独立检索，互不干扰 |
| 文档智能解析 | 支持PDF/DOCX/TXT/Markdown格式自动解析 |
| 混合检索 | 向量语义检索 + BM25关键词检索融合 |
| 重排序 | BGE-Reranker精排，提升准确率 |
| 引用溯源 | 每条回答标注来源文档、页码和原文 |
| RAG评估体系 | 内置评估数据集和自动化评估脚本 |
| Docker一键部署 | 前后端容器化，一条命令启动 |

### 系统架构

```
用户提问 → Query预处理 → 混合检索(向量+BM25) → 重排序 → LLM生成 → 回答+来源
                                  ↓
                           文档摄入管道
                    (PDF/DOCX/TXT → 解析 → 切片 → 向量化)
```

详细架构文档见 [docs/architecture.md](docs/architecture.md)

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+ (前端)
- Docker & Docker Compose (可选)

### 1. 克隆项目

```bash
git clone https://github.com/1402605737-create/enterprise-rag-knowledge-base-.git
cd enterprise-rag-knowledge-base
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env，填入LLM API Key
```

### 3. Docker 一键启动 (推荐)

```bash
# 启动全部服务
docker compose up -d

# 摄入示例数据
docker compose exec backend python scripts/ingest_demo.py --kb-id demo

# 打开浏览器访问
# 前端: http://localhost:3000
# API文档: http://localhost:8000/docs
```

### 4. 本地开发启动

```bash
# 后端
cd backend
pip install -r requirements.txt
python scripts/ingest_demo.py --kb-id demo   # 先摄入示例数据
uvicorn api.main:app --reload --port 8000

# 前端 (新终端)
cd frontend
npm install
npm run dev
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/knowledge-bases` | 创建知识库 |
| GET | `/api/v1/knowledge-bases` | 获取知识库列表 |
| DELETE | `/api/v1/knowledge-bases/{id}` | 删除知识库 |
| POST | `/api/v1/knowledge-bases/{id}/documents` | 上传文档 |
| DELETE | `/api/v1/knowledge-bases/{id}/documents/{doc_id}` | 删除文档 |
| POST | `/api/v1/chat` | 知识库问答 |

详细API文档：启动后端后访问 `http://localhost:8000/docs`

## 示例问题

系统已内置4份企业示例文档，可直接提问：

| 问题 | 预期从哪份文档检索 |
|------|-------------------|
| 年假有几天？ | 员工手册 |
| 新员工入职需要哪些材料？ | 员工手册 |
| 云帆AI平台v3.0的技术栈是什么？ | 技术架构说明书 |
| 公司的晋升评审每年几次？ | HR政策汇编 |
| 智能客服系统支持多少种语言？ | 产品使用手册 |

## 评估结果

运行评估脚本：

```bash
cd backend
python -m evaluation.evaluate
```

预期结果：检索召回率 > 90%，平均响应 < 5秒。

详见 [docs/evaluation-report.md](docs/evaluation-report.md)

## 技术栈

| 层 | 技术 | 选型理由 |
|----|------|---------|
| 后端框架 | FastAPI | 异步高性能、自动文档 |
| RAG框架 | 自研（基于LlamaIndex模式） | 可控、可定制 |
| 向量数据库 | ChromaDB | 轻量零配置，可迁移Milvus |
| 嵌入模型 | BGE-small-zh-v1.5 | 开源、中文SOTA |
| 重排序 | BGE-Reranker-Base | 开源、精排效果好 |
| 关键词检索 | BM25 (rank-bm25) | 经典算法，互补语义检索 |
| 前端 | Next.js 14 + Tailwind | 现代化、SSR支持 |
| LLM | DeepSeek/通义千问 (OpenAI兼容API) | 中文效果好、成本低 |
| 部署 | Docker Compose | 一键启动、环境一致 |

## 项目文档

| 文档 | 说明 |
|------|------|
| [PRD.md](docs/PRD.md) | 产品需求文档（含用户画像、功能需求、KPI） |
| [competitive-analysis.md](docs/competitive-analysis.md) | 竞品分析（Glean/Notion AI/Dify等） |
| [architecture.md](docs/architecture.md) | 系统架构设计（含数据流、技术选型） |
| [evaluation-report.md](docs/evaluation-report.md) | RAG评估报告 |

## 作品集亮点

作为AI产品经理作品集项目，本项目展示了：

1. **产品思维**：完整的PRD文档，包含用户画像、需求优先级、KPI体系
2. **竞品分析**：深度对比国内外主流产品，明确差异化定位
3. **架构设计**：清晰的技术架构和数据流设计，体现工程理解
4. **落地能力**：可运行的完整系统（前端+后端+Docker部署）
5. **评估体系**：内置RAG质量评估，体现数据驱动思维
6. **文档规范**：中英文文档齐全，注重可读性和专业性

## License

MIT
