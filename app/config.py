"""集中配置：所有可调参数走环境变量，方便 Docker 覆盖。"""
import os

OLLAMA_URL = os.getenv("OLLAMA_HOST_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("RAG_LLM", "qwen2.5:7b")
EMB_MODEL = os.getenv("RAG_EMB", "bge-m3")

DOC_DIR = os.getenv("RAG_DOCS", "docs")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK", "400"))
CHUNK_OVERLAP = int(os.getenv("RAG_OVERLAP", "60"))
TOP_K = int(os.getenv("RAG_TOP_K", "3"))
MIN_CHUNK = 30
