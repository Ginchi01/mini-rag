"""FastAPI 入口：启动时建索引，暴露 /health 和 /ask。"""
import glob
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import config
from .chunker import split_text
from .index import VectorIndex
from .rag import answer
from .schemas import AskRequest, AskResponse, HealthResponse, Hit

index = VectorIndex()


def load_documents() -> list:
    paths = sorted(glob.glob(os.path.join(config.DOC_DIR, "*.txt"))
                   + glob.glob(os.path.join(config.DOC_DIR, "*.md")))
    chunks = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            chunks += split_text(fh.read(), os.path.basename(path),
                                 config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.MIN_CHUNK)
    return chunks


@asynccontextmanager
async def lifespan(_app: FastAPI):
    index.build(load_documents())
    yield


app = FastAPI(title="Mini RAG Service", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", chunks=index.size,
                          llm=config.LLM_MODEL, embed=config.EMB_MODEL)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if index.size == 0:
        raise HTTPException(status_code=503, detail="索引为空，请往 docs/ 放文档后重启")
    try:
        reply, hits = answer(index, req.question, req.top_k)
    except Exception as exc:  # 模型没起来 / 超时
        raise HTTPException(status_code=502, detail=f"生成失败：{exc}") from exc

    return AskResponse(
        answer=reply,
        hits=[Hit(source=c.source, score=s, snippet=c.text[:80].replace("\n", " "))
              for c, s in hits],
    )
