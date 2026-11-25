"""向量索引：L2 归一化后，点积即余弦相似度。"""
import numpy as np

from .chunker import Chunk
from .ollama_client import embed


class VectorIndex:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.matrix: np.ndarray | None = None

    def build(self, chunks: list[Chunk]) -> None:
        if not chunks:
            self.chunks, self.matrix = [], None
            return
        vecs = np.array([embed(c.text) for c in chunks], dtype=np.float32)
        # 归一化一次，之后查询只需一次点积
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
        self.chunks, self.matrix = chunks, vecs

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, float]]:
        if self.matrix is None:
            return []
        q = np.array(embed(query), dtype=np.float32)
        q /= np.linalg.norm(q) + 1e-9
        scores = self.matrix @ q
        idx = np.argsort(-scores)[:top_k]
        return [(self.chunks[int(i)], float(scores[i])) for i in idx]

    @property
    def size(self) -> int:
        return len(self.chunks)
