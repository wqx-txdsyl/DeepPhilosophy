"""
嵌入模型模块 —— 文本向量化
1. 优先: BAAI/bge-small-zh-v1.5 (中文优化, 需下载 ~95MB)
2. 回退: jieba TF-IDF (零下载, 无网络依赖)
"""
import os
import numpy as np
from loguru import logger

from config import EMBEDDING_MODEL_NAME, USE_BGE_MODEL

# 国内网络环境：自动设置 HuggingFace 镜像
_HF_MIRROR = "https://hf-mirror.com"
os.environ.setdefault("HF_ENDPOINT", _HF_MIRROR)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


class TFIDFEmbedding:
    """
    基于 jieba TF-IDF 的轻量嵌入（回退方案）
    优势：零依赖下载，纯本地运行
    局限：语义理解能力弱于深度学习模型
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.vocab: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self._fitted = False

    def fit(self, documents: list[str]):
        """从文档集合中构建 TF-IDF 词表"""
        import jieba

        doc_count = len(documents)
        word_doc_count: dict[str, int] = {}

        # 统计词频和文档频率
        for doc in documents:
            words = set(jieba.cut(doc))
            for w in words:
                word_doc_count[w] = word_doc_count.get(w, 0) + 1

        # 构建词表（取IDF最高的词）
        sorted_words = sorted(
            word_doc_count.items(), key=lambda x: -x[1]
        )
        self.vocab = {
            w: i for i, (w, _) in enumerate(sorted_words[:self.dim])
        }
        # 计算 IDF
        for w, cnt in word_doc_count.items():
            if w in self.vocab:
                self.idf[w] = np.log((doc_count + 1) / (cnt + 1)) + 1
        self._fitted = True

    def encode(self, texts: list[str]) -> list[list[float]]:
        """编码文本为 TF-IDF 向量"""
        import jieba
        import math

        if not self._fitted:
            # 未 fit 过，使用零向量
            return [[0.0] * max(1, self.dim) for _ in texts]

        result = []
        for text in texts:
            words = list(jieba.cut(text))
            vec = np.zeros(self.dim)
            word_count: dict[str, int] = {}
            for w in words:
                word_count[w] = word_count.get(w, 0) + 1

            total = max(1, len(words))
            for w, cnt in word_count.items():
                if w in self.vocab:
                    tf = cnt / total
                    weight = tf * self.idf.get(w, 0)
                    vec[self.vocab[w]] = weight

            # L2 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            result.append(vec.tolist())
        return result

    def build_and_encode(self, texts: list[str]) -> list[list[float]]:
        """构建词表并编码（合并 fit + encode）"""
        if not self._fitted:
            self.fit(texts)
        return self.encode(texts)


class EmbeddingManager:
    """嵌入模型管理器：自动选择最佳可用的嵌入方案"""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        self.model = None
        self.fallback = None
        self.ready = False
        self.dimension = 0
        self._load_model()

    def _load_model(self):
        """尝试加载模型，失败则回退到 TF-IDF"""
        # ---- 检查配置开关 ----
        if not USE_BGE_MODEL:
            logger.info("USE_BGE_MODEL=False，直接使用 TF-IDF 回退方案")
            self._use_fallback()
            return

        # ---- 策略1：尝试加载 BGE 中文模型 ----
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"正在下载/加载嵌入模型: {self.model_name}...")
            logger.info(f"HF_ENDPOINT={os.environ.get('HF_ENDPOINT', 'default')}")
            logger.info("首次运行需下载 ~95MB，请耐心等待...")

            self.model = SentenceTransformer(
                self.model_name,
                local_files_only=False,
            )
            self.dimension = self.model.get_sentence_embedding_dimension()
            self.ready = True
            logger.info(
                f"BGE 嵌入模型加载成功 (维度: {self.dimension})"
            )
            return
        except ImportError:
            logger.warning("sentence-transformers 未安装，回退到 TF-IDF")
        except Exception as e:
            logger.warning(f"BGE 模型加载失败: {e}")
            logger.warning("将使用 jieba TF-IDF 回退方案")

        self._use_fallback()

    def _use_fallback(self):
        """启用 TF-IDF 回退方案"""
        self.fallback = TFIDFEmbedding(dim=256)
        self.dimension = self.fallback.dim
        self.ready = True
        logger.info(
            f"TF-IDF 回退嵌入方案就绪 (维度: {self.dimension})\n"
            "   提示：设置 config.USE_BGE_MODEL=True 可启用更优的BGE模型"
        )

    def encode(self, texts: list[str]) -> list[list[float]]:
        """编码文本为向量列表"""
        if not self.ready:
            raise RuntimeError("嵌入模型未就绪")

        if self.model is not None:
            # BGE 模型
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        elif self.fallback is not None:
            # TF-IDF 回退
            return self.fallback.build_and_encode(texts)
        else:
            raise RuntimeError("没有可用的嵌入方案")

    def encode_single(self, text: str) -> list[float]:
        """编码单条文本"""
        return self.encode([text])[0]

    def get_embedding_function(self):
        """返回 ChromaDB 可用的嵌入函数"""
        def _embed(texts: list[str]) -> list[list[float]]:
            return self.encode(texts)
        return _embed
