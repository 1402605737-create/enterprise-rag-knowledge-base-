from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class EvalSample:
    question: str
    reference_answer: str
    relevant_docs: List[str]


def load_eval_samples() -> List[EvalSample]:
    return [
        EvalSample(
            question="云帆科技的年假有多少天？",
            reference_answer="入职满1年享受5天年假，逐年递增，上限15天。",
            relevant_docs=["employee-handbook.md"],
        ),
        EvalSample(
            question="新员工入职需要携带哪些材料？",
            reference_answer="需要携带：身份证原件及复印件、学历学位证书原件及复印件、离职证明（应届生除外）、体检报告（近3个月内）、银行卡复印件。",
            relevant_docs=["employee-handbook.md"],
        ),
        EvalSample(
            question="公司的五险一金缴纳比例是多少？",
            reference_answer="养老保险公司16%个人8%，医疗保险公司8%个人2%，失业保险公司0.5%个人0.5%，工伤保险公司0.2%，生育保险公司0.8%，住房公积金公司12%个人12%。",
            relevant_docs=["employee-handbook.md"],
        ),
        EvalSample(
            question="云帆AI平台v3.0使用的技术栈有哪些？",
            reference_answer="Python 3.11/Go 1.21, FastAPI/Gin, Milvus 2.3, PostgreSQL 16, Kafka 3.6, Redis 7.2, Kubernetes 1.29。",
            relevant_docs=["technical-spec.md"],
        ),
        EvalSample(
            question="知识库的检索延迟P99目标是多少？",
            reference_answer="检索延迟P99目标小于500ms，当前值为320ms。",
            relevant_docs=["technical-spec.md"],
        ),
        EvalSample(
            question="公司的晋升评审每年有几次？分别在什么时间？",
            reference_answer="晋升评审每年两次：6月和12月。",
            relevant_docs=["hr-policy.md"],
        ),
        EvalSample(
            question="云帆智能客服系统支持多少种语言？",
            reference_answer="支持中文、英文、日文、韩文、法文、西班牙文等20+语言。",
            relevant_docs=["product-manual.md"],
        ),
        EvalSample(
            question="文档摄入管道的切片策略中，默认chunk_size和overlap是多少？",
            reference_answer="默认chunk_size=512 tokens，overlap=50 tokens。",
            relevant_docs=["technical-spec.md"],
        ),
        EvalSample(
            question="员工如何申请年假？需要提前多久？",
            reference_answer="年假需提前3天申请。",
            relevant_docs=["employee-handbook.md"],
        ),
        EvalSample(
            question="公司的学习基金额度是多少？可以用来做什么？",
            reference_answer="每人每年5000元，用于购买书籍、课程或参加技术大会。",
            relevant_docs=["employee-handbook.md"],
        ),
    ]


def run_evaluation():
    from generation.rag_pipeline import rag_search

    samples = load_eval_samples()
    results = []

    for i, sample in enumerate(samples):
        print(f"\n--- 评估样本 {i+1}/{len(samples)} ---")
        print(f"问题: {sample.question}")
        print(f"期望答案: {sample.reference_answer}")

        try:
            result = rag_search(sample.question, top_k=5)
            print(f"实际答案: {result.answer[:200]}...")
            print(f"来源文档: {[s['document_name'] for s in result.sources]}")
            print(f"耗时: {result.elapsed_ms}ms")

            recall = len(set(s["document_name"] for s in result.sources) & set(sample.relevant_docs)) / len(sample.relevant_docs) if sample.relevant_docs else 0

            results.append({
                "question": sample.question,
                "reference_answer": sample.reference_answer,
                "generated_answer": result.answer,
                "sources": [s["document_name"] for s in result.sources],
                "recall": recall,
                "elapsed_ms": result.elapsed_ms,
            })
        except Exception as e:
            print(f"错误: {e}")
            results.append({"question": sample.question, "error": str(e)})

    correct_recalls = sum(1 for r in results if r.get("recall", 0) == 1.0)
    avg_elapsed = sum(r.get("elapsed_ms", 0) for r in results) / len(results) if results else 0

    print(f"\n{'='*50}")
    print(f"评估完成")
    print(f"召回率: {correct_recalls}/{len(results)} ({correct_recalls/len(results)*100:.1f}%)")
    print(f"平均耗时: {avg_elapsed:.0f}ms")
    print(f"{'='*50}")

    return results


if __name__ == "__main__":
    run_evaluation()
