"""
云端部署配置 —— DeepPhilosophy API 服务器
所有路径使用环境变量，适配容器化部署
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# DeepSeek API 配置
# ============================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# ============================================================
# 路径配置（云端适配）
# ============================================================
# 知识库书籍存储目录
KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", os.path.join(os.path.dirname(__file__), "data", "books"))

# OCR提取文本存储
EXTRACTED_DIR = os.getenv("EXTRACTED_DIR", os.path.join(os.path.dirname(__file__), "data", "extracted"))

# 向量数据库持久化目录
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(os.path.dirname(__file__), "data", "vectordb"))

# 向量数据库集合名
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "deephilosophy_knowledge")

# ============================================================
# 嵌入模型配置
# ============================================================
EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# ============================================================
# 文本分块配置
# ============================================================
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ============================================================
# 检索配置
# ============================================================
TOP_K_RETRIEVAL = 5

# ============================================================
# 嵌入模型策略
# ============================================================
# Render 免费版内存有限，默认用 TF-IDF；付费后可改为 True
USE_BGE_MODEL = os.getenv("USE_BGE_MODEL", "False").lower() in ("true", "1", "yes")

# ============================================================
# LLM 生成参数
# ============================================================
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 1024

# ============================================================
# 服务器配置
# ============================================================
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ============================================================
# HuggingFace 镜像（国内加速）
# ============================================================
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# ============================================================
# Cloudflare R2 云存储配置（备选）
# ============================================================
USE_R2 = os.getenv("USE_R2", "False").lower() in ("true", "1", "yes")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_BUCKET = os.getenv("R2_BUCKET", "deepphilosophy-books")

# ============================================================
# GitHub Release 云存储配置（无需信用卡，境外访问）
# ============================================================
USE_GITHUB = os.getenv("USE_GITHUB", "False").lower() in ("true", "1", "yes")
GITHUB_MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "data", "github_manifest.json")

# ============================================================
# 阿里云 OSS 存储配置（国内高速）
# ============================================================
USE_OSS = os.getenv("USE_OSS", "False").lower() in ("true", "1", "yes")
OSS_MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "data", "oss_manifest.json")
OSS_BUCKET_HOST = os.getenv("OSS_BUCKET_HOST", "deepphilosophy.oss-cn-shanghai.aliyuncs.com")
