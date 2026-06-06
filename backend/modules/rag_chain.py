"""
RAG 检索增强生成链 —— 将检索到的文档上下文注入 DeepSeek 生成回答
"""
from loguru import logger

from config import TOP_K_RETRIEVAL, LLM_TEMPERATURE, LLM_MAX_TOKENS


RAG_SYSTEM_PROMPT = """你是一个个人知识库助手，基于哲学文献知识库回答问题。

核心规则：
1. 只根据提供的「参考文档」内容回答，不要使用外部知识
2. 如果「参考文档」中没有相关信息，请明确告知用户："抱歉，当前知识库中没有找到相关信息。"
3. 使用中文回答，语言简洁准确
4. 【必须】每次回答末尾必须标注参考文献来源，格式如下：

---
📎 **参考文献：**
- 《来源文件名1》（如知道页码标注第X页）
- 《来源文件名2》

5. 在回答中引用文档原文时，用引号标出并注明来自哪个文档"""


class RAGChain:
    """RAG 链：检索 + 增强生成"""

    def __init__(self, vector_store, llm_client):
        """
        初始化 RAG 链

        Args:
            vector_store: VectorStoreManager 实例
            llm_client: DeepSeekClient 实例
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.conversation_history: list[dict] = []
        logger.info("RAG 链初始化完成")

    def query(self, question: str) -> dict:
        """
        执行 RAG 问答

        流程: 检索 → 构建Prompt → LLM生成 → 返回答案+来源

        Args:
            question: 用户自然语言提问

        Returns:
            {"answer": 回答, "sources": [来源信息], "question": 原始问题}
        """
        if not question.strip():
            return {"answer": "请输入有效的问题。", "sources": [], "question": question}

        # ---- 第1步：语义检索 ----
        logger.info(f"开始检索: {question[:50]}...")
        retrieved = self.vector_store.similarity_search(question, top_k=TOP_K_RETRIEVAL)

        if not retrieved:
            return {
                "answer": "知识库中暂无文档。请先在 `Data/` 目录下放入 PDF 文件并执行文档入库。",
                "sources": [],
                "question": question,
            }

        # ---- 第2步：构建 Prompt ----
        # 拼接检索到的文档片段
        context_parts = []
        sources = []
        for i, item in enumerate(retrieved, 1):
            content = item.get("content", "")
            meta = item.get("metadata", {})
            source_name = meta.get("source", "未知文档")
            page = meta.get("page", "")
            context_parts.append(
                f"[片段{i}] 来源: {source_name}"
                + (f" 第{page}页" if page else "")
                + f"\n{content}"
            )
            if source_name not in sources:
                sources.append(source_name)

        context_text = "\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": f"""参考文档内容：
{context_text}

用户问题：{question}

请基于以上文档内容回答问题，并标注信息来源。"""},
        ]

        # 如果有对话历史，追加最近2轮
        if self.conversation_history:
            history = self.conversation_history[-4:]  # 最近2轮 = 4条消息
            messages = messages[:1] + history + messages[1:]

        # ---- 第3步：调用 DeepSeek 生成回答 ----
        logger.info("正在调用 DeepSeek API 生成回答...")
        try:
            answer = self.llm_client.chat(
                messages=messages,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            answer = f"回答生成失败: {e}"

        # ---- 第4步：更新对话历史 ----
        self.conversation_history.append({"role": "user", "content": question})
        self.conversation_history.append({"role": "assistant", "content": answer})

        # 限制历史长度
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

        logger.info(f"RAG 问答完成，检索到 {len(retrieved)} 个相关片段")

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_count": len(retrieved),
            "question": question,
        }

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        logger.info("对话历史已清空")
