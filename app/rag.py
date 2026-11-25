"""RAG 主流程：检索 + 拼 prompt + 生成。"""
from . import config
from .index import VectorIndex
from .ollama_client import chat

SYSTEM = (
    "只根据用户提供的资料回答。资料里没有的信息，直接说“资料中没有提到”，不要自己编。"
    "回答末尾用 [编号] 标注引用了哪段资料。"
)


def answer(index: VectorIndex, question: str, top_k: int = config.TOP_K):
    hits = index.search(question, top_k)
    if not hits:
        return "索引为空，请先往 docs/ 放文档。", []

    context = "\n\n".join(
        f"[{i}]（来源：{c.source}）\n{c.text}" for i, (c, _s) in enumerate(hits, start=1)
    )
    reply = chat(SYSTEM, f"资料：\n{context}\n\n问题：{question}")
    return reply, hits
