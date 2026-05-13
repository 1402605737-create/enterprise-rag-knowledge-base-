from typing import List
from openai import OpenAI

from config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from models import SearchResult

SYSTEM_PROMPT = """你是一个专业的企业知识库助手。请严格根据以下参考资料回答用户问题。

## 规则
1. 仅使用参考资料中明确包含的信息回答
2. 如果资料信息不足以回答，请明确说"抱歉，根据现有资料我无法回答这个问题。"
3. 回答时在关键信息后标注引用来源编号，格式如 [1]、[2]
4. 保持回答简洁、专业、有条理
5. 如果用户的问题与参考资料完全无关，礼貌地引导用户提出与知识库相关的问题

## 回答格式
- 先用1-2句话直接回答问题
- 然后补充细节（如适用）
- 确保每个关键事实都有来源引用"""


def _build_context(results: List[SearchResult]) -> tuple[str, list]:
    context_parts = []
    sources = []
    for i, r in enumerate(results):
        ref_num = i + 1
        context_parts.append(
            f"[{ref_num}] 来源: {r.chunk.document_name} (第{r.chunk.page}页)\n{r.chunk.text}"
        )
        sources.append({
            "ref": ref_num,
            "document_name": r.chunk.document_name,
            "page": r.chunk.page,
            "text": r.chunk.text[:300] + ("..." if len(r.chunk.text) > 300 else ""),
            "score": round(r.score, 4),
        })
    return "\n\n---\n\n".join(context_parts), sources


def generate_answer(query: str, results: List[SearchResult], stream: bool = False) -> tuple[str, list]:
    context_text, sources = _build_context(results)

    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"## 参考资料\n\n{context_text}\n\n## 用户问题\n{query}"},
    ]

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content
    return answer, sources
