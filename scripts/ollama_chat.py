"""最小多轮对话：调用本地 Ollama 的 7B 模型。

用法：
    1. 装 Ollama：https://ollama.com
    2. ollama pull qwen2.5:7b
    3. pip install requests
    4. python ollama_chat.py
"""
import requests

OLLAMA = "http://localhost:11434"
# 3050 Ti 是 4GB 显存：7B 会溢出到内存（约 3 tok/s），3B 流畅（约 15 tok/s）
# 想跑快就把下面改成 "qwen2.5:3b"，先 ollama pull qwen2.5:3b
MODEL = "qwen2.5:7b"


def chat(messages, model=MODEL, temperature=0.7):
    """把整段历史发给 Ollama，返回回复文本。模型本身无状态，上下文靠 messages 维持。"""
    resp = requests.post(
        f"{OLLAMA}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def trim(history, keep=20):
    """上下文太长会拖慢推理，只保留 system + 最近 N 条。"""
    if len(history) <= keep + 1:
        return history
    return [history[0]] + history[-keep:]


def main():
    history = [{"role": "system", "content": "你是一个简洁的中文助手，回答控制在三句以内。"}]
    print(f"模型：{MODEL}　输入 exit 退出\n")

    while True:
        try:
            question = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if question.lower() in ("exit", "quit", "q"):
            break
        if not question:
            continue

        history.append({"role": "user", "content": question})
        try:
            answer = chat(history)
        except requests.exceptions.ConnectionError:
            print("\n[错误] 连不上 Ollama，先确认它启动了：ollama serve\n")
            break
        except requests.exceptions.HTTPError as exc:
            print(f"\n[错误] {exc}　可能是模型名不对，先跑 ollama list 看看\n")
            break

        history.append({"role": "assistant", "content": answer})
        history = trim(history)
        print(f"模型：{answer}\n")


if __name__ == "__main__":
    main()


