# 构建：docker build -t mini-rag .
# 运行：docker run -p 8000:8000 -e OLLAMA_HOST_URL=http://host.docker.internal:11434 mini-rag

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 先只拷依赖清单 —— 只要它没变，这一层就命中缓存，不重装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷代码
COPY app ./app
COPY docs ./docs

ENV OLLAMA_HOST_URL=http://host.docker.internal:11434 \
    RAG_LLM=qwen2.5:7b \
    RAG_EMB=bge-m3

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
