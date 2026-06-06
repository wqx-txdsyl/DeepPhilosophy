"""
向量数据库模块 —— 基于 ChromaDB 的文档向量存储与检索
"""
import os
from loguru import logger

from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, TOP_K_RETRIEVAL


class VectorStoreManager:
    """ChromaDB 向量数据库管理器"""

    def __init__(self, embedding_function=None):
        """
        初始化 ChromaDB

        Args:
            embedding_function: 嵌入函数，将文本转为向量
        """
        self.embedding_function = embedding_function
        self.client = None
        self.collection = None
        self.ready = False
        self._init_chroma()

    def _init_chroma(self):
        """初始化 ChromaDB 客户端和集合"""
        try:
            import chromadb
            from chromadb.config import Settings

            # 确保持久化目录存在
            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

            # 创建客户端（持久化模式）
            self.client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False),
            )

            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},  # 余弦相似度
            )

            self.ready = True
            logger.info(
                f"ChromaDB 初始化成功 "
                f"(集合: {CHROMA_COLLECTION_NAME}, "
                f"文档数: {self.collection.count()})"
            )
        except ImportError:
            logger.error("chromadb 未安装！请运行: pip install chromadb")
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败: {e}")

    def add_documents(
        self,
        chunks: list[str],
        metadata_list: list[dict] | None = None,
        doc_id_prefix: str = "doc",
    ) -> None:
        """
        将文本块添加进向量数据库

        Args:
            chunks: 文本块列表
            metadata_list: 每个块的元数据列表（文件名、页码等）
            doc_id_prefix: ID 前缀
        """
        if not self.ready or not self.collection:
            raise RuntimeError("ChromaDB 未就绪")

        if not chunks:
            logger.warning("没有文本块需要添加")
            return

        # 生成 ID
        ids = [f"{doc_id_prefix}_{i}" for i in range(len(chunks))]

        # 如果没有提供元数据，用空字典
        if metadata_list is None:
            metadata_list = [{} for _ in chunks]

        # ChromaDB 最大批处理大小
        MAX_BATCH = 4000

        # 分批添加（避免超限）
        total_added = 0
        for batch_start in range(0, len(chunks), MAX_BATCH):
            batch_end = min(batch_start + MAX_BATCH, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            batch_ids = ids[batch_start:batch_end]
            batch_meta = metadata_list[batch_start:batch_end]

            if self.embedding_function:
                embeddings = self.embedding_function(batch_chunks)
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_chunks,
                    metadatas=batch_meta,
                    embeddings=embeddings,
                )
            else:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_chunks,
                    metadatas=batch_meta,
                )
            total_added += len(batch_chunks)

        logger.info(f"已添加 {total_added} 个文本块到向量数据库")

    def similarity_search(
        self, query: str, top_k: int | None = None
    ) -> list[dict]:
        """
        语义相似度检索

        Args:
            query: 查询文本
            top_k: 返回数量，默认从 config 读取

        Returns:
            [{"content": 文本, "metadata": 元数据, "distance": 距离}, ...]
        """
        if not self.ready or not self.collection:
            raise RuntimeError("ChromaDB 未就绪")

        top_k = top_k or TOP_K_RETRIEVAL

        # 如果有嵌入函数，用嵌入函数；否则 ChromaDB 用内置的
        if self.embedding_function:
            query_embedding = self.embedding_function([query])
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
            )
        else:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
            )

        # 整理结果
        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                item = {"content": doc}
                if results["metadatas"] and results["metadatas"][0]:
                    item["metadata"] = results["metadatas"][0][i] or {}
                if results["distances"] and results["distances"][0]:
                    item["distance"] = round(results["distances"][0][i], 4)
                documents.append(item)

        return documents

    def delete_by_document(self, doc_name: str) -> int:
        """
        删除指定文档的所有向量块

        Args:
            doc_name: 文档文件名

        Returns:
            删除的块数量
        """
        if not self.collection:
            return 0

        try:
            results = self.collection.get(
                where={"source": doc_name}
            )
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"已删除文档 [{doc_name}] 的 {len(results['ids'])} 个向量块")
                return len(results["ids"])
            return 0
        except Exception as e:
            logger.error(f"删除文档失败 [{doc_name}]: {e}")
            return 0

    def list_documents(self) -> list[str]:
        """列出知识库中的所有文档（去重）"""
        if not self.collection:
            return []
        try:
            results = self.collection.get()
            sources = set()
            if results["metadatas"]:
                for meta in results["metadatas"]:
                    src = meta.get("source", "")
                    if src:
                        sources.add(src)
            return sorted(sources)
        except Exception:
            return []

    def get_collection_stats(self) -> dict:
        """获取集合统计信息"""
        if not self.collection:
            return {"document_count": 0, "chunk_count": 0}
        docs = self.list_documents()
        return {
            "document_count": len(docs),
            "chunk_count": self.collection.count(),
        }
