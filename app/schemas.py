"""请求与响应的数据结构（Pydantic 会据此自动校验和生成文档）。"""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="要问的问题")
    top_k: int = Field(3, ge=1, le=10, description="检索几段资料")


class Hit(BaseModel):
    source: str
    score: float
    snippet: str


class AskResponse(BaseModel):
    answer: str
    hits: list[Hit]


class HealthResponse(BaseModel):
    status: str
    chunks: int
    llm: str
    embed: str
