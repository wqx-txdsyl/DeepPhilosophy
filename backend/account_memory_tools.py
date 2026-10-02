"""Explicit cross-conversation memory, separate from tool workflow state."""
from langchain_core.tools import StructuredTool
from deep_context import current_account_id, current_request_question
import account_data


def recall_account_memory():
    """读取当前登录账号明确保存的长期记忆。匿名用户不保存账号记忆。"""
    uid = current_account_id.get()
    if not uid:
        return {"error": "LOGIN_REQUIRED"}
    from account_memory_profile import get_profile
    profile = get_profile(uid)
    if not profile['enabled']:
        return {"error": "MEMORY_DISABLED"}
    return {"memories": account_data.list_memories(uid), "memory_profile": profile['text']}


def remember_account_memory(source_quote: str):
    """仅在用户明确要求记住时，将当前消息的原话保存到账号长期记忆。

    source_quote 必须逐字摘自当前用户消息，不得推断或改写为人格、信念标签。
    """
    uid = current_account_id.get()
    question = current_request_question.get() or ""
    markers = ("记住", "记着", "记下来", "remember", "keep in mind")
    if not uid:
        return {"error": "LOGIN_REQUIRED"}
    from account_memory_profile import get_profile
    if not get_profile(uid)['enabled']:
        return {"error": "MEMORY_DISABLED"}
    refusals = ("不要记住", "别记住", "不许记住", "don't remember", "do not remember")
    if (any(marker in question.lower() for marker in refusals)
            or not any(marker in question.lower() for marker in markers)
            or not source_quote.strip() or source_quote not in question):
        return {"error": "EXPLICIT_MEMORY_REQUEST_REQUIRED"}
    return {"memory": account_data.remember(uid, source_quote.strip())}


def forget_account_memory(memory_id: str):
    """用户要求忘记时，按 recall_account_memory 返回的真实 memory_id 删除长期记忆。"""
    uid = current_account_id.get()
    question = (current_request_question.get() or "").lower()
    if not uid:
        return {"error": "LOGIN_REQUIRED"}
    if not any(word in question for word in ("忘", "删除", "清除", "forget", "delete", "remove")):
        return {"error": "EXPLICIT_FORGET_REQUEST_REQUIRED"}
    return {"deleted": account_data.forget(uid, memory_id)}


def search_account_history(query: str):
    """按关键词查找当前账号以前的提问和回答，返回可继续读取的真实会话ID。

    查询的是保存的正文，不是用户立场或已核验的哲学证据。无匹配时可换关键词。
    """
    uid = current_account_id.get()
    if not uid:
        return {"error": "LOGIN_REQUIRED"}
    if not query.strip():
        return {"error": "QUERY_REQUIRED"}
    return {"results": account_data.search_history(uid, query.strip())}


def read_account_conversation(conversation_id: str):
    """读取当前账号检索命中的历史会话正文，供继续讨论；其他账号的会话不可读。"""
    uid = current_account_id.get()
    if not uid:
        return {"error": "LOGIN_REQUIRED"}
    data = account_data.get_conversation(uid, conversation_id)
    if not data:
        return {"error": "CONVERSATION_NOT_FOUND"}
    return {"conversation_id": conversation_id, "title": data.get('title'),
            "messages": [{"role": m.get('role'), "content": m.get('content'),
                          "message_id": m.get('message_id')} for m in data.get('messages', [])]}


def memory_tools():
    return [StructuredTool.from_function(fn) for fn in
            (recall_account_memory, remember_account_memory, forget_account_memory,
             search_account_history, read_account_conversation)]
