"""Opt-in request context for general-agent stateful tools.

Identity comes from the authenticated route dependency, never from request body
fields. Conversation identifiers are namespaced by that identity; requests that
omit one receive their own disposable scope. No context is installed for persona
agents, whose existing memory-key behavior remains unchanged.
"""
from contextvars import ContextVar
import hashlib
import json
import secrets


current_memory_key: ContextVar[str | None] = ContextVar("deep_memory_key", default=None)
current_memory_overlay: ContextVar[dict | None] = ContextVar("deep_memory_overlay", default=None)
current_request_question: ContextVar[str | None] = ContextVar("deep_request_question", default=None)
current_tool_agent: ContextVar[str | None] = ContextVar("deep_tool_agent", default=None)
current_account_id: ContextVar[int | None] = ContextVar("deep_account_id", default=None)


def reset_owned_context(variable, token):
    """ASGI may close an async generator in a different cleanup task.

    That task does not own the token. Leave its context untouched; the original
    request task's context ends with that task. Normal completion still resets.
    """
    try:
        variable.reset(token)
        return True
    except ValueError:
        return False


def general_memory_key(user, ip, conversation_id):
    user_id = (user or {}).get("id")
    authenticated = user_id is not None
    owner = ["user", str(user_id)] if authenticated else ["ip", str(ip or "unknown")]
    conversation = conversation_id or ("request:" + secrets.token_hex(16))
    payload = json.dumps([owner, str(conversation)], ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    # Keep the persisted memory loader's existing u/ip prefix recognition.
    return ("u:general:" if authenticated else "ip:general:") + digest
