# DeepPhilosophy Backend Dockerfile
# Multi-stage: Node.js builds frontend, Python runs backend
FROM node:20-slim AS frontend
WORKDIR /app
COPY app/package.json app/package-lock.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖（分层缓存）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --default-timeout=300 \
    -r requirements.txt

# 复制应用代码
COPY backend/config.py .
COPY backend/main.py .
COPY backend/auth.py .
COPY backend/philosophers_db.py .
COPY backend/admin.py .
COPY backend/modules/ ./modules/

# 复制静态数据
RUN mkdir -p /app/data
COPY backend/data/book_summaries.json /app/data/
COPY backend/data/books_cache.json /app/data/
COPY backend/data/github_manifest.json /app/data/
COPY backend/data/oss_manifest.json /app/data/
COPY backend/data/philosophers.json /app/data/
COPY backend/data/name_aliases.json /app/data/

# 复制前端构建产物（多阶段构建，无需 backend/app-dist）
COPY --from=frontend /app/dist/ ./static/

# 环境变量默认值（可在 Render 面板覆盖）
ENV KNOWLEDGE_DIR=/app/data/books
ENV CHROMA_PERSIST_DIR=/app/data/vectordb
ENV EXTRACTED_DIR=/app/data/extracted
ENV USE_BGE_MODEL=false
ENV HF_ENDPOINT=https://hf-mirror.com
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000
ENV USE_OSS=true

EXPOSE 8000

CMD ["python", "main.py"]
