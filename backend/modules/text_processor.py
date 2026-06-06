"""
文本处理模块 —— 中文分词、关键词提取、文本摘要
"""
import re
from loguru import logger

import jieba
import jieba.analyse

from config import CHUNK_SIZE, CHUNK_OVERLAP


class TextProcessor:
    """文本预处理器：分词、关键词提取、文本清洗"""

    # 中文停用词（常见无意义词）
    STOP_WORDS = set([
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
        "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
        "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
        "所", "为", "因为", "所以", "但是", "然而", "而且", "或者", "如果",
        "虽然", "可以", "这个", "那个", "什么", "怎么", "怎样", "哪", "哪能",
        "啊", "吧", "呢", "吗", "哦", "嗯", "哈", "呀", "哇",
    ])

    def __init__(self):
        logger.info("TextProcessor 初始化完成 (jieba 分词器)")

    def clean_text(self, text: str) -> str:
        """
        清洗文本：移除多余空白、控制字符

        Args:
            text: 原始文本

        Returns:
            清洗后的文本
        """
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)
        # 移除控制字符（保留换行）
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()

    def extract_keywords(
        self, text: str, top_k: int = 10, method: str = "textrank"
    ) -> list[tuple[str, float]]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前 K 个关键词
            method: 算法选择 "textrank" 或 "tfidf"

        Returns:
            [(关键词, 权重), ...]
        """
        if not text or len(text.strip()) < 10:
            return []

        if method == "textrank":
            keywords = jieba.analyse.textrank(
                text, topK=top_k, withWeight=True,
                allowPOS=("n", "nr", "ns", "nt", "nz", "v", "vn", "a", "an")
            )
        else:
            keywords = jieba.analyse.extract_tags(
                text, topK=top_k, withWeight=True,
                allowPOS=("n", "nr", "ns", "nt", "nz", "v", "vn", "a", "an")
            )

        # 过滤停用词和过短词
        keywords = [
            (kw, round(w, 4))
            for kw, w in keywords
            if kw not in self.STOP_WORDS and len(kw) >= 2
        ]
        return keywords

    def split_text(
        self, text: str, chunk_size: int | None = None,
        chunk_overlap: int | None = None
    ) -> list[str]:
        """
        将长文本切分为适合嵌入和检索的块

        使用 LangChain 的递归字符分割器，按以下优先级切分：
        段落 > 句子 > 字符

        Args:
            text: 输入文本
            chunk_size: 块大小（字符），默认从 config 读取
            chunk_overlap: 重叠大小，默认从 config 读取

        Returns:
            文本块列表
        """
        chunk_size = chunk_size or CHUNK_SIZE
        chunk_overlap = chunk_overlap or CHUNK_OVERLAP

        if not text or len(text.strip()) == 0:
            return []

        # 递归字符分割：优先按段落→句子→短语切分
        separators = ["\n\n", "\n", "。", "！", "？", "；", "，", ".", "!", "?", ";", ",", " ", ""]
        chunks = self._recursive_split(text, separators, chunk_size, chunk_overlap)
        chunks = [c.strip() for c in chunks if c.strip()]
        return chunks

    def _recursive_split(
        self, text: str, separators: list[str],
        chunk_size: int, overlap: int
    ) -> list[str]:
        """
        递归分割：仿 LangChain RecursiveCharacterTextSplitter 的行为
        按优先级依次尝试分割符，直到文本块小于 chunk_size
        """
        # 如果文本够短，直接返回
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        # 尝试用当前最优分隔符切分
        sep = separators[0] if separators else ""
        if sep:
            parts = text.split(sep)
        else:
            # 最后手段：按字符切分
            parts = list(text)

        # 如果只有一个部分，用下一个分隔符
        if len(parts) <= 1 and len(separators) > 1:
            return self._recursive_split(text, separators[1:], chunk_size, overlap)

        # 合并短片段到 chunk_size
        chunks = []
        current = ""
        for part in parts:
            # 尝试加入当前块
            test = current + (sep if current else "") + part
            if len(test) <= chunk_size:
                current = test
            else:
                # 保存当前块
                if current.strip():
                    chunks.append(current)
                # 处理 part：如果它本身就超过 chunk_size，递归分割
                if len(part) > chunk_size and len(separators) > 1:
                    sub_chunks = self._recursive_split(
                        part, separators[1:], chunk_size, overlap
                    )
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current.strip():
            chunks.append(current)

        # 添加 overlap：在相邻块之间保留重叠
        if overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_end = chunks[i-1][-overlap:] if len(chunks[i-1]) > overlap else chunks[i-1]
                overlapped.append(prev_end + chunks[i])
            return overlapped

        return chunks

    def extract_summary_info(self, text: str) -> dict:
        """
        提取文档摘要信息

        Args:
            text: 文档全文

        Returns:
            {"word_count": 字数, "keywords": [(词,权重),...], "first_line": 首句}
        """
        cleaned = self.clean_text(text)
        keywords = self.extract_keywords(cleaned, top_k=5)
        first_line = cleaned.split("\n")[0][:100] if cleaned else ""

        return {
            "word_count": len(cleaned),
            "keywords": keywords,
            "first_line": first_line,
        }
