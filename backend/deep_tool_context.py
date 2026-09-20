"""Bounded, non-semantic delivery of general research and generated artifacts."""
import hashlib
import json

from tool_contracts import TOOL_TAXONOMY

MAX_ARTIFACT_CONTEXT_CHARS = 24000
PRIMARY_CONTEXT_TOOLS = frozenset({'search_books', 'get_chapter', 'get_book_detail', 'concept_trace'})
SCHOLARLY_CONTEXT_TOOLS = frozenset({'search_scholarship', 'get_scholarly_source'})


def preserves_artifact(name, agent):
    capability = TOOL_TAXONOMY.get(name, {})
    return agent == "general" and bool(
        capability.get("USES_INTERNAL_LLM") or capability.get("USER_VISIBLE_ARTIFACT")
        or name == "websearch" or name in PRIMARY_CONTEXT_TOOLS | SCHOLARLY_CONTEXT_TOOLS)
    # Keep actual book IDs, read_args, catalogue matches and passage windows
    # together. Later turns must not reduce a primary source to its opening.


def tool_context(name, result, agent, fallback_content=None):
    """Return model content plus delivery metadata; never mutate the actual result.

    Within the mechanical bound, all fields survive unchanged. Oversized
    artifacts are explicitly omitted as a whole, rather than selecting a
    conclusion and silently dropping later objections or artifact endings.
    Other tools and persona callers retain their legacy serialization.
    """
    if not preserves_artifact(name, agent):
        content = fallback_content if fallback_content is not None else (
            json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result))
        return content[:4000], None
    content = json.dumps(result, ensure_ascii=False)
    delivery = {"status": "complete", "original_chars": len(content),
                "max_chars": MAX_ARTIFACT_CONTEXT_CHARS}
    if len(content) <= MAX_ARTIFACT_CONTEXT_CHARS:
        return content, {**delivery, "transmitted_chars": len(content)}
    paths = []
    if isinstance(result, dict):
        for key, value in result.items():
            paths.extend(f"{key}.{child}" for child in value) if isinstance(value, dict) else paths.append(str(key))
    else:
        paths = ["result"]
    omitted = [path[:120] for path in paths[:64]]
    notice = {
        "error": "TOOL_CONTEXT_TOO_LARGE", "tool": name, "context_delivery": "omitted",
        "message": "工具产物超过本次上下文交付上限，正文整体未传给主模型；不能将其当作已读材料或已完成的检验。",
        "original_chars": len(content), "max_chars": MAX_ARTIFACT_CONTEXT_CHARS,
        "omitted_fields": omitted, "omitted_field_count": len(paths),
        "omission_list_complete": len(paths) <= 64 and all(len(path) <= 120 for path in paths),
        "result_sha256": hashlib.sha256(content.encode()).hexdigest(),
    }
    rendered = json.dumps(notice, ensure_ascii=False)
    return rendered, {**delivery, "status": "omitted", "transmitted_chars": len(rendered),
                      "omitted_fields": omitted, "omitted_field_count": len(paths)}
