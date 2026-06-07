# DeepPhilosophy Backend Dockerfile
# 用于 Zeabur / 任意 Docker 云平台部署
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（分层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=300 \
    -r requirements.txt

# 复制应用代码
COPY config.py .
COPY main.py .
COPY auth.py .
COPY philosophers_db.py .
COPY modules/ ./modules/

# 数据目录（书籍通过 API 上传或挂载卷）
RUN mkdir -p /app/data/books /app/data/extracted /app/data/vectordb

# 环境变量默认值（可在 Zeabur 面板覆盖）
ENV KNOWLEDGE_DIR=/app/data/books
ENV CHROMA_PERSIST_DIR=/app/data/vectordb
ENV EXTRACTED_DIR=/app/data/extracted
ENV USE_BGE_MODEL=true
ENV HF_ENDPOINT=https://hf-mirror.com
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
