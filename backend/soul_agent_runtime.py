"""Minimal streaming loop for soul.md + primary texts only."""
import asyncio
import json
import time
import uuid
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.utils import message_chunk_to_message
from soul_agents import soul_prompt
from soul_agent_tools import PrimaryTexts


async def stream_soul_agent(question, history, key, language='zh', custom_instructions=None):
    from deep_bare_agent import load_model
    started = time.monotonic()
    texts = PrimaryTexts(key)
    tools = texts.tools()
    registry = {t.name: t for t in tools}
    messages = [SystemMessage(content=soul_prompt(key, language))]
    if custom_instructions:
        messages.append(HumanMessage(content='用户的交流偏好（当前请求优先）：\n' + custom_instructions))
    for entry in history or []:
        cls = {'user': HumanMessage, 'assistant': AIMessage}.get(entry.get('role'))
        if cls:
            messages.append(cls(content=entry.get('content') or ''))
    messages.append(HumanMessage(content=question))
    model = None
    yield {'type': 'status', 'content': '正在思考' if language != 'en' else 'Thinking',
           'agent_id': key, 'runtime_profile': 'soul_preview'}
    try:
        model = load_model()
        client = model.bind_tools(tools)
        for turn in range(20):
            full = None
            stream = client.astream(messages)
            try:
                async for chunk in stream:
                    full = chunk if full is None else full + chunk
                    reasoning = (getattr(chunk, 'additional_kwargs', {}) or {}).get('reasoning_content')
                    if reasoning:
                        yield {'type': 'thinking_summary_delta', 'content': reasoning, 'agent_id': key}
            finally:
                await stream.aclose()
            if full is None:
                yield {'type': 'error', 'content': '模型未返回内容。'}
                return
            message = message_chunk_to_message(full)
            messages.append(message)
            calls = list(message.tool_calls or []) + [dict(c, _invalid=True) for c in message.invalid_tool_calls or []]
            if not calls:
                finish = (getattr(full, 'response_metadata', {}) or {}).get('finish_reason')
                if message.content:
                    yield {'type': 'token', 'content': message.content}
                yield {'type': 'done', 'content': message.content, 'complete': finish in (None, 'stop'),
                       'agent_id': key, 'runtime_profile': 'soul_preview', 'status': 'preview',
                       'finish_reason': finish, 'suggestions': [], 'citations': used_citations(texts.reads, message.content),
                       'primary_passages_read': len(texts.reads),
                       'duration_seconds': round(time.monotonic() - started, 3)}
                return
            if message.content:
                yield {'type': 'thinking_summary', 'content': message.content}
            for call in calls:
                call_id = call.get('id') or uuid.uuid4().hex
                name, args = call['name'], call.get('args') or {}
                yield {'type': 'tool_start', 'name': name, 'call_id': call_id, 'tool_call_id': call_id}
                at = time.monotonic()
                try:
                    if call.get('_invalid') or name not in registry:
                        result = {'error': 'INVALID_TOOL_CALL'}
                    else:
                        result = await registry[name].ainvoke(args)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    result = {'error': 'PRIMARY_TOOL_ERROR', 'message': str(exc)[:300]}
                serialized = json.dumps(result, ensure_ascii=False)
                messages.append(ToolMessage(content=serialized, tool_call_id=call_id, name=name))
                yield {'type': 'tool', 'name': name, 'args': args, 'result': serialized,
                       'call_id': call_id, 'tool_call_id': call_id,
                       'status': 'error' if result.get('error') else 'success',
                       'duration_seconds': round(time.monotonic() - at, 3)}
        yield {'type': 'error', 'content': '本次研究尚未完成，请缩小问题或继续对话。'}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        yield {'type': 'error', 'content': str(exc), 'agent_id': key}
    finally:
        if getattr(model, 'root_async_client', None) is not None:
            await model.root_async_client.close()
        if getattr(model, 'root_client', None) is not None:
            model.root_client.close()


def used_citations(reads, answer):
    """Show only actually read passages whose label or URL occurs in the answer."""
    citations = {}
    for read in reads:
        if read.get('book_id') and (read.get('citation_label', '\x00') in answer
                                   or f'《{read["book_title"]}》' in answer):
            key = (read['book_id'], read['chapter_idx'])
            citations[key] = {'book': read['book_title'], 'chapter': read['chapter_title'],
                              'book_id': read['book_id'], 'chapter_idx': read['chapter_idx'],
                              'source_type': read['source_type'], 'access_level': 'PASSAGE_READ',
                              'used': True, 'verified': False, 'excerpt': read['text'][:700]}
        elif read.get('url') and read['url'] in answer:
            citations[read['url']] = {'title': read.get('title'), 'url': read['url'],
                                      'source_type': 'web', 'access_level': 'WEB_PASSAGE_READ',
                                      'source_status': read.get('source_status'),
                                      'used': True, 'verified': False, 'excerpt': read['text'][:700]}
    return list(citations.values())
