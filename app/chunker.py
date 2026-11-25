"""文本切分：不依赖网络和模型，纯函数，方便写单元测试。"""
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    start: int


def split_text(text: str, source: str, size: int = 400, overlap: int = 60,
               min_len: int = 30) -> list[Chunk]:
    """按固定长度切分，相邻块保留 overlap 个字符，避免切断句子。

    >>> len(split_text("a" * 1000, "t.md", size=400, overlap=60))
    3
    """
    if size <= 0:
        raise ValueError("size 必须为正")
    if overlap >= size:
        raise ValueError("overlap 必须小于 size")

    text = text.strip()
    if not text:
        return []

    step = size - overlap
    chunks: list[Chunk] = []
    for start in range(0, len(text), step):
        piece = text[start:start + size].strip()
        if len(piece) >= min_len:
            chunks.append(Chunk(text=piece, source=source, start=start))
        if start + size >= len(text):
            break
    return chunks
