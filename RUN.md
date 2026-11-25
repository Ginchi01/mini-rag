# 跑通指南（照着做，每步都有预期输出）

> 目标：**一次跑完，同时把 FastAPI / Docker / Git / Linux 四项技能变成真的。**
> 前提：Ollama 已装、`qwen2.5:7b` 和 `bge-m3` 已 pull。

---

## 阶段 0：先跑测试（不需要模型，1 分钟）

```powershell
cd "C:\Users\芦靖琪\Documents\deepseek-harness\default-workspace\mini-rag"
pip install -r requirements.txt
pytest -v
```

**预期输出：**

```
tests/test_chunker.py::test_empty_text PASSED
tests/test_chunker.py::test_single_short_chunk_is_dropped PASSED
tests/test_chunker.py::test_overlap_makes_chunks_share_text PASSED
tests/test_chunker.py::test_no_infinite_loop_on_exact_boundary PASSED
tests/test_chunker.py::test_source_is_recorded PASSED
tests/test_chunker.py::test_invalid_params PASSED
============================== 6 passed ==============================
```

✅ 全绿就说明**代码逻辑没问题**，剩下的都是环境和模型。

---

## 阶段 1：本地起服务（FastAPI，5 分钟）

### 1.1 确认 Ollama 在跑

```powershell
ollama list
```

要能看到 `qwen2.5:7b` 和 `bge-m3`。没有就先 pull。

### 1.2 启动

```powershell
uvicorn app.main:app --reload --port 8000
```

**预期输出：**

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

> 第一次启动会**逐段算 embedding**，8 段文档大概 10–30 秒，然后才出现 `Application startup complete`。**别以为卡死了。**

### 1.3 打开浏览器

**http://127.0.0.1:8000/docs**

你会看到自动生成的 Swagger 页面，两个接口：`/health` 和 `/ask`。

### 1.4 点开 `/health` → Try it out → Execute

**预期返回：**

```json
{"status": "ok", "chunks": 8, "llm": "qwen2.5:7b", "embed": "bge-m3"}
```

✅ `chunks` 不为 0，说明文档加载成功。

### 1.5 点开 `/ask` → Try it out，填入

```json
{"question": "骨龄和实际年龄差多少算异常", "top_k": 3}
```

**预期返回：** 一段引用资料的回答，加 3 条命中的片段（带来源和分数）。

✅ 到这里，**FastAPI 这项技能就成立了**。

---

## 阶段 2：容器化（Docker，20 分钟）

### 2.1 装 Docker Desktop

下载 https://www.docker.com/products/docker-desktop/ → 安装 → **重启电脑**。

重启后打开 Docker Desktop，等托盘图标变成绿色（Engine running）。

```powershell
docker --version
```

**预期：** `Docker version 27.x.x`

### 2.2 构建镜像

```powershell
docker build -t mini-rag .
```

**预期输出（节选）：**

```
[1/6] FROM docker.io/library/python:3.11-slim
[3/6] COPY requirements.txt .
[4/6] RUN pip install --no-cache-dir -r requirements.txt
[6/6] COPY app ./app
 => exporting to image
 => => naming to docker.io/library/mini-rag:latest
```

**第一次要 3–8 分钟（下载基础镜像 + 装依赖）。第二次改代码再 build，只要几秒——这就是层缓存。**

### 2.3 看镜像

```powershell
docker images mini-rag
```

**预期：** 一个几百 MB 的镜像。

### 2.4 跑容器

```powershell
docker run -p 8000:8000 -e OLLAMA_HOST_URL=http://host.docker.internal:11434 mini-rag
```

**预期：**

```
INFO:     Started server process [1]
INFO:     Application startup complete.
```

### 2.5 再打开 http://127.0.0.1:8000/docs

**功能和本地跑的一模一样。**

✅ 到这里，**Docker 这项技能就成立了**。

### 2.6 常用命令（顺手记住）

```powershell
docker ps                        # 看运行中的容器
docker ps -a                     # 看全部（含已停止）
docker logs <容器ID>              # 看日志（排错第一招）
docker stop <容器ID>              # 停
docker rm <容器ID>                # 删容器
docker rmi mini-rag              # 删镜像
docker stats                     # 实时看 CPU / 内存
```

---

## 阶段 3：Linux 练手（WSL2，15 分钟）

### 3.1 装 WSL

```powershell
wsl --install -d Ubuntu
```

重启后设置用户名密码。然后：

```powershell
wsl
```

### 3.2 在 WSL 里跑同一个服务

```bash
cd /mnt/c/Users/芦靖琪/Documents/deepseek-harness/default-workspace/mini-rag
sudo apt update && sudo apt install -y python3-pip python3-venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> WSL 里访问宿主机的 Ollama 用 `http://localhost:11434`（WSL2 默认能通）。

### 3.3 另开一个 WSL 窗口验证

```bash
curl http://localhost:8000/health
```

**预期：** JSON 输出。

### 3.4 必练的几条命令

```bash
ps aux | grep uvicorn          # 服务在不在
tail -f 日志文件                # 实时看日志
df -h                          # 磁盘
du -sh *                       # 各目录大小
netstat -tlnp | grep 8000      # 端口占用
kill -9 <pid>                  # 杀进程
```

✅ 到这里，**Linux 这项技能就成立了**。

---

## 阶段 4：Git 工作流（20 分钟）

### 4.1 初始化

```powershell
cd "C:\Users\芦靖琪\Documents\deepseek-harness\default-workspace\mini-rag"
git init
git add .
git status                     # 确认 __pycache__ 之类的没被加进来
git commit -m "feat: 最小 RAG 检索问答服务"
```

### 4.2 开分支做一个改进

```powershell
git checkout -b feat/health-uptime
```

改 `app/main.py`，给 `/health` 加一个 `uptime_seconds` 字段（随便练手）。

```powershell
git add app/main.py
git commit -m "feat: health 接口返回运行时长"
git checkout main
git merge feat/health-uptime
```

### 4.3 制造并解决一次冲突（重要，面试会问）

```powershell
git checkout -b feat/a
# 改 README 第一行，commit
git checkout main
# 改 README 第一行（不同内容），commit
git merge feat/a
```

**你会看到：**

```
CONFLICT (content): Merge conflict in README.md
```

**解决流程：**

1. 打开 README.md，找到：
   ```
   <<<<<<< HEAD
   main 分支的内容
   =======
   feat/a 的内容
   >>>>>>> feat/a
   ```
2. 留下你要的，删掉三行标记
3. `git add README.md`
4. `git commit -m "fix: 解决 README 冲突"`

✅ **亲手解过一次冲突，这条技能才算真的。**

### 4.4 推到 GitHub

先在 GitHub 建空仓库 `mini-rag`，然后：

```powershell
git remote add origin https://github.com/你的用户名/mini-rag.git
git branch -M main
git push -u origin main
```

**去网页确认：代码上去了，而且没有 `__pycache__`、没有模型文件。**

✅ 到这里，**Git 这项技能就成立了，而且简历可以放 GitHub 链接了。**

---

## 阶段 5：把技能写回简历（5 分钟）

全跑通后，告诉我，我把这两行加回去：

| 位置 | 内容 |
|---|---|
| 工程工具 | **Git 分支管理与合并、Docker 容器化部署、Linux 常用命令、FastAPI**、PyQt5、SQLite |
| 大模型实践 第 2 条 | 将 RAG 检索与生成封装为 FastAPI 接口并容器化，容器内通过 `host.docker.internal` 调用宿主机 Ollama，**避免 GPU 透传**；单元测试覆盖切分逻辑，可离线跑 CI。 |

---

## 常见报错对照表

| 报错 | 原因 | 解决 |
|---|---|---|
| `连不上 Ollama` | 服务没起 | `ollama serve` 或重开 Ollama |
| `Ollama 返回错误 404` | 模型名不对 | `ollama list` 看实际名字，改 `RAG_LLM` |
| `503 索引为空` | docs/ 里没文档 | 放几个 .md 进去，重启服务 |
| `pytest: command not found` | 没装依赖 | `pip install -r requirements.txt` |
| `docker: command not found` | Docker 没装/没启动 | 打开 Docker Desktop 等图标变绿 |
| `docker build` 卡住 | 在拉基础镜像 | 正常，第一次慢 |
| 容器里 502 | 容器访问不到宿主机 | 确认 `-e OLLAMA_HOST_URL=http://host.docker.internal:11434` |
| `port is already allocated` | 8000 被占 | 换端口 `-p 8001:8000` |

---

## 时间预算

| 阶段 | 内容 | 时长 |
|---|---|---|
| 0 | pytest | 1 min |
| 1 | FastAPI 本地 | 5 min |
| 2 | Docker | 20 min |
| 3 | WSL2 / Linux | 15 min |
| 4 | Git + GitHub | 20 min |
| **合计** | | **约 1 小时** |

**一小时，四项技能，一个能放进简历的 GitHub 仓库。**
