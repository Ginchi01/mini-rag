"""Ollama 客户端：embedding 和 chat 两个调用。"""
import requests

from . import config


class OllamaError(RuntimeError):
    pass


def _post(path: str, payload: dict, timeout: int = 180) -> dict:
    try:
        resp = requests.post(f"{config.OLLAMA_URL}{path}", json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        raise OllamaError(
            f"连不上 Ollama（{config.OLLAMA_URL}）。先确认 ollama serve 在跑。") from exc
    except requests.exceptions.HTTPError as exc:
        raise OllamaError(f"Ollama 返回错误：{exc}。检查模型是否已 pull。") from exc


def embed(text: str) -> list[float]:
    return _post("/api/embeddings", {"model": config.EMB_MODEL, "prompt": text})["embedding"]


def chat(system: str, user: str) -> str:
    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "stream": False,
    }
    return _post("/api/chat", payload)["message"]["content"]
