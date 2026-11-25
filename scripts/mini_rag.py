"""最小 RAG：文档切分 → 向量化 → 余弦检索 → 拼 prompt 生成。

这是「Coze 知识库智能体」的自研版——平台封装的三步，这里全部自己做。

用法：
    ollama pull qwen2.5:7b
    ollama pull bge-m3
    pip install requests numpy
    python mini_rag.py
"""
import glob
import os

import numpy as np
import requests

OLLAMA = "http://localhost:11434"
# 3050 Ti 4GB 显存：7B 会溢出（慢），3B 流畅。改这里即可切换
LLM = "qwen2.5:7b"
EMB = "bge-m3"

BASE = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.join(BASE, "..", "docs")   # 复用仓库根目录的 docs/

CHUNK = 400       # 每个片段字符数
OVERLAP = 60      # 相邻片段重叠，避免切断句子
TOP_K = 3         # 检索几条


# ---------- 1. 向量化 ----------
def embed(text, model=EMB):
    resp = requests.post(
        f"{OLLAMA}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=120,
    )
    resp.raise_for_status()
    return np.array(resp.json()["embedding"], dtype=np.float32)


# ---------- 2. 读文档并切分 ----------
def load_chunks():
    paths = sorted(
        glob.glob(os.path.join(DOC_DIR, "*.txt")) + glob.glob(os.path.join(DOC_DIR, "*.md"))
    )
    if not paths:
        raise SystemExit(f"没有找到文档，请往 {DOC_DIR} 放几个 .txt 或 .md 文件")

    chunks = []
    step = CHUNK - OVERLAP
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            text = fh.read().strip()
        for start in range(0, max(1, len(text)), step):
            piece = text[start:start + CHUNK].strip()
            if len(piece) < 30:
                continue
            chunks.append({"text": piece, "source": os.path.basename(path)})
    return chunks


# ---------- 3. 建索引（L2 归一化后，点积 = 余弦） ----------
def build_index(chunks):
    matrix = np.vstack([embed(c["text"]) for c in chunks])
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    return matrix


# ---------- 4. 检索 ----------
def search(matrix, chunks, query, k=TOP_K):
    q = embed(query)
    q /= np.linalg.norm(q) + 1e-9
    scores = matrix @ q
    idx = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in idx]


# ---------- 5. 生成 ----------
def generate(question, hits):
    context = "\n\n".join(
        f"[{i + 1}]（来源：{item['source']}）\n{item['text']}"
        for i, (item, _score) in enumerate(hits)
    )
    messages = [
        {
            "role": "system",
            "content": (
                "只根据用户提供的资料回答。资料里没有的信息，直接说「资料中没有提到」，"
                "不要自己编。回答末尾用 [编号] 标注引用了哪段资料。"
            ),
        },
        {"role": "user", "content": f"资料：\n{context}\n\n问题：{question}"},
    ]
    resp = requests.post(
        f"{OLLAMA}/api/chat",
        json={"model": LLM, "messages": messages, "stream": False},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def main():
    print("正在读文档并建索引……（首次会慢一点）")
    chunks = load_chunks()
    matrix = build_index(chunks)
    print(f"索引就绪：{len(chunks)} 个片段，来自 {len({c['source'] for c in chunks})} 个文件\n")

    while True:
        try:
            question = input("问题：").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in ("exit", "quit", "q"):
            break
        if not question:
            continue

        try:
            hits = search(matrix, chunks, question)
            answer = generate(question, hits)
        except requests.exceptions.ConnectionError:
            print("\n[错误] 连不上 Ollama，先确认它启动了：ollama serve\n")
            break
        except requests.exceptions.HTTPError as exc:
            print(f"\n[错误] {exc}　可能是 embedding 模型没拉：ollama pull bge-m3\n")
            break

        print(f"\n回答：{answer}\n")
        print("命中片段：")
        for i, (item, score) in enumerate(hits, start=1):
            snippet = item["text"].replace("\n", " ")[:60]
            print(f"  [{i}] {score:.3f} | {item['source']} | {snippet}…")
        print()


if __name__ == "__main__":
    main()



