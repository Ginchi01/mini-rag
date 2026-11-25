# Mini RAG Service

一个最小但完整的 **RAG 检索问答服务**：文档切分 → 向量化 → 余弦检索 → 拼 prompt → LLM 生成。

**它是一个可运行的工程样本**，包含 FastAPI 接口、Docker 容器化、单元测试和 Git 工作流——用来证明「会写代码、会部署、能交付」，而不只是「跑过 demo」。

---

## 技术栈

| 层 | 选型 |
|---|---|
| 推理 | Ollama（本地 7B 模型，OpenAI 兼容风格 HTTP API） |
| 向量 | Ollama `bge-m3` embedding + NumPy 余弦检索 |
| 服务 | FastAPI + Uvicorn（Pydantic 自动校验 + Swagger 文档） |
| 部署 | Docker + docker-compose |
| 测试 | pytest（纯函数单测，不依赖模型，可离线跑） |

---

## 快速开始

```bash
# 1. 拉依赖
pip install -r requirements.txt

# 2. 确认 Ollama 在跑，且模型已下载
ollama list                     # 要有 qwen2.5:7b 和 bge-m3

# 3. 启动
uvicorn app.main:app --reload --port 8000

# 4. 打开接口文档
#    http://127.0.0.1:8000/docs
```

**问一句试试：**

```bash
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"骨龄和实际年龄差多少算异常\"}"
```

---

## 目录结构

```
mini-rag/
├── app/                   # FastAPI 服务版（推荐）
│   ├── config.py          # 所有参数走环境变量，方便容器覆盖
│   ├── chunker.py         # 文本切分（纯函数，可单测）
│   ├── ollama_client.py   # embedding / chat 调用
│   ├── index.py           # 向量索引 + 余弦检索
│   ├── rag.py             # 检索 → 拼 prompt → 生成
│   ├── schemas.py         # Pydantic 请求/响应模型
│   └── main.py            # FastAPI 入口
├── scripts/               # 命令行版（更早的版本，见 scripts/README.md）
│   ├── ollama_chat.py     # 多轮对话，验证上下文
│   └── mini_rag.py        # 最小 RAG，单文件实现
├── tests/
│   └── test_chunker.py    # 6 个单测，不需要模型
├── docs/                  # 知识库文档（.md / .txt）
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

**为什么这样拆模块**：切分、索引、生成三件事的变更频率不同——换 chunk 策略不动接口，换模型不动切分。

**为什么保留 `scripts/`**：那是从「一次性 demo」演进到「可部署服务」的过程记录。
先写通单文件，再拆分成模块，这条路径本身比最终代码更能说明问题。

---

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 返回索引片段数、当前模型名 |
| POST | `/ask` | 传 `question` 和 `top_k`，返回答案 + 命中片段 |
| GET | `/docs` | 自动生成的 Swagger 交互文档 |

---

## Docker 部署

```bash
# 构建
docker build -t mini-rag .

# 运行（Ollama 在宿主机，容器通过 host.docker.internal 访问）
docker run -p 8000:8000 -e OLLAMA_HOST_URL=http://host.docker.internal:11434 mini-rag

# 或者用 compose
docker compose up --build
```

### 一个刻意的设计取舍

**Ollama 留在宿主机，容器只调 HTTP 接口，不做 GPU 透传。**

理由：容器内用 GPU 需要 `nvidia-container-toolkit`，Windows + WSL2 下配置成本高。把模型留在宿主机、容器只做业务层，**牺牲一点网络开销，换来部署简单**。

> 面试被问「容器里怎么用 GPU」时，这个回答比背 `--gpus all` 有分量。

---

## 跑测试

```bash
pytest -v
```

6 个用例全部覆盖 `chunker.py`——**故意不让测试依赖模型**，这样 CI 上不装 Ollama 也能跑。

---

## 实测记录

### 召回质量的三次迭代

| 版本 | 改动 | top-1 分数 | top-1 内容 |
|---|---|---|---|
| v1 | 原始 | 0.535 | **文档元信息**（“本文档是示例”）❌ |
| v2 | 清理知识库中的非知识性文本 | **0.548** | 真正的 RUS-CHN 定义 ✅ |

**发现**：知识库里混入“这是示例文档”这类元信息，会被检索到且排在第一位，污染上下文。

**结论**：RAG 的上限由知识库质量决定，不只是检索算法。

### 拒答能力验证

| 问题 | 结果 | 最高召回分 |
|---|---|---|
| 骨龄和实际年龄差多少算异常 | ✅ 答对 ±2 岁 | 0.548 |
| RUS-CHN 和 GP 图谱法有什么区别 | ✅ 答对计分法 / 图谱法 | 0.537 |
| **今天北京天气怎么样** | ✅ **“资料中没有提到”** | **0.343** |

**观察到的规律**：
- 能回答的问题 → 召回分数 **0.55 以上**
- 不相关的问题 → 召回分数 **0.35 以下**

**据此设计 0.4 的分数阈值做拒答**：低于阈值直接返回“资料中没有提到”，不调用 LLM。
比只靠 prompt 约束更可靠，还省一次推理。

### 硬件实测（RTX 3050 Ti Laptop，4GB 显存）

| 模型 | Q4 大小 | `ollama ps` | 生成速度 |
|---|---|---|---|
| qwen2.5:7b | 4.7 GB | **55% CPU / 45% GPU** | 200 字约 **13 秒**（≈15 tok/s） |
| qwen2.5:3b | 2.0 GB | 100% GPU | 更快 |

**7B 的 Q4 权重 4.4GB，比可用显存（约 3GB）还大，必然溢出到 CPU。**
通过 `OLLAMA_FLASH_ATTENTION=1` 和 `OLLAMA_KV_CACHE_TYPE=q8_0` 压缩 KV cache 缓解。

---

## 可以继续做的方向

| 方向 | 改动 | 能讲什么 |
|---|---|---|
| 混合检索 | 加 BM25，与向量结果 RRF 融合 | 向量对专有名词不敏感，关键词补上 |
| 重排 | 召回 20 条后用 bge-reranker 取 5 条 | 精度换延迟 |
| 评测 | 30 条 QA 测试集，算 recall@k | 有数据支撑优化 |
| 流式返回 | SSE 逐字输出 | 首字延迟从 8s 降到 1s |
| 持久化 | 向量存 Chroma/SQLite | 启动不用重建索引 |
