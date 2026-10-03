"""One canonical system prompt + tools + provider messages; no runtime budgets.

The original controlled engine remains available with DEEP_AGENT_RUNTIME=controlled.
Provider capacity and individual tool implementations remain their own contracts.
"""
import asyncio
import inspect
import json
import time
import uuid
import httpx

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.messages.utils import message_chunk_to_message


async def load_tools():
    from engine_langgraph import _build_tools
    from mcp_client import get_mcp_tools
    # Research declarations govern the old budget system, not an actual
    # research capability. All content tools and configured MCP tools remain.
    from account_memory_tools import memory_tools
    return _build_tools(general=True, bare=True) + memory_tools() + await get_mcp_tools()


def load_model():
    from engine_langgraph import _llm_for_agent
    from routes import agent_llm
    base = _llm_for_agent('general')
    # Rebuild the SDK client too: model_copy alone would leave its old retry
    # configuration attached to the cached root client.
    return type(base)(model=base.model_name, api_key=agent_llm.API_KEY,
                      base_url=agent_llm.API_URL, temperature=base.temperature,
                      extra_body=base.extra_body, max_tokens=None,
                      max_retries=0, timeout=httpx.Timeout(None), stream_usage=True)


async def execute(tool, args, question, agent='general'):
    from deep_context import current_tool_agent, current_request_question
    from deep_stateful import STATEFUL_TOOLS, execute_stateful
    agent_token = current_tool_agent.set(agent)
    question_token = current_request_question.set(question)
    try:
        if tool is None:
            return {'error': 'UNKNOWN_TOOL'}
        if tool.coroutine is not None:
            return await tool.ainvoke(args)
        if inspect.iscoroutinefunction(tool.func):
            if tool.args_schema:
                tool.args_schema.model_validate(args)
            return await tool.func(**args)
        if tool.name in STATEFUL_TOOLS:
            return await execute_stateful(lambda **values: tool.invoke(values), args, timeout=None)
        return await asyncio.to_thread(tool.invoke, args)
    finally:
        current_request_question.reset(question_token)
        current_tool_agent.reset(agent_token)


def tool_status(result):
    if not isinstance(result, dict):
        return 'empty' if result == [] else 'success'
    if result.get('error') or result.get('accepted') is False or result.get('success') is False or result.get('ok') is False:
        return 'error'
    if result.get('status') in {'error','blocked','partial','empty'}:
        return result['status']
    if result.get('provider_errors'):
        return 'partial'
    if any(isinstance(result.get(k), list) and not result[k] for k in ('results','items','matches')):
        return 'empty'
    return 'success'


async def exploration_questions(question, answer, language):
    from deep_exploration import generate_exploration
    return await asyncio.to_thread(generate_exploration, question, answer, language)


def source_metadata(calls, answer, language):
    """Display-only provenance: never changes or rejects the model's answer."""
    from evidence_contract import build_evidence_contract
    from deep_sources import enrich_citations, primary_research
    evidence = build_evidence_contract(calls, answer, 'general', language)
    citations = enrich_citations(evidence['citations'], evidence, calls, answer)
    evidence['display_citations'] = citations
    evidence['primary_research'] = primary_research(citations, calls, answer)
    return citations, evidence


async def stream_bare_agent(question, history, language='zh', conversation_id=None, message_id=None, _evaluation_prompt_profile=None, custom_instructions=None, agent='general', _persona=None):
    from agent_release import prompt_spec, release_descriptor, fingerprint
    from routes.agent_llm import MODEL
    release = release_descriptor(language,_evaluation_prompt_profile)
    persona = _persona
    if agent == 'nietzsche' and persona is None:
        import nietzsche_runtime as persona
    if persona is not None:
        system = persona.system_text(language, question)
        import hashlib
        persona_version = getattr(persona, 'prompt_version', 'nietzsche-shared-1')
        release = {**release, 'responder':agent, 'prompt_version':persona_version,
                   'effective_prompt_sha256':hashlib.sha256(system.encode()).hexdigest(),
                   'prompt_matches_manifest':None,'persona_prompt_version':persona_version}
    else:
        system = prompt_spec(language,_evaluation_prompt_profile)['text']
    messages = [SystemMessage(content=system)]
    from deep_context import current_account_id
    from account_context_messages import personalization_messages
    context = None
    if user_id := current_account_id.get():
        from account_data import account_context
        context = await asyncio.to_thread(account_context, user_id, conversation_id)
    messages.extend(personalization_messages(context, custom_instructions))
    for entry in history or []:
        cls = {'user': HumanMessage, 'assistant': AIMessage}.get(entry.get('role'))
        if cls is not None:
            messages.append(cls(content=entry.get('content') or ''))
    messages.append(HumanMessage(content=question))
    started = time.monotonic()
    invocation = uuid.uuid4().hex
    calls = []
    from reading_coverage import ReadingCoverage
    reading_coverage = ReadingCoverage()
    round_index = 0
    tasks = set()
    model = None
    round_usage = []
    returned_models = set()
    yield {'type': 'status', 'content': '开始思考' if language != 'en' else 'Thinking',
           'runtime_profile': 'bare', 'release':release}
    try:
        tools = await persona.tools() if persona else await load_tools()
        contracts=[{'name':t.name,'description':t.description,
            'schema':t.args_schema.model_json_schema() if hasattr(t.args_schema,'model_json_schema')
                else t.args_schema if isinstance(t.args_schema,dict) else {}} for t in tools]
        import hashlib
        release['toolset_sha256']=hashlib.sha256(json.dumps(contracts,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        release['installed_tool_count']=len(tools)
        release['configuration_fingerprint']=fingerprint(release)
        yield {'type':'runtime_metadata','release':release}
        registry = {tool.name: tool for tool in tools}
        model = load_model()
        client = model.bind_tools(tools)
        while True:
            round_index += 1
            group = f'{invocation}:{round_index}'
            full = None
            text = ''
            segment = 0
            announced = set()
            call_started = False
            stream = client.astream(messages)
            try:
                async for chunk in stream:
                    full = chunk if full is None else full + chunk
                    reasoning = (getattr(chunk, 'additional_kwargs', {}) or {}).get('reasoning_content')
                    if reasoning:
                        if text and not call_started:
                            yield {'type': 'assistant_commentary', 'id': f'{group}:note:{segment}', 'content': text}
                            yield {'type': 'answer_preview_reset'}
                            text = ''
                            segment += 1
                        yield {'type': 'provider_reasoning_delta', 'source': 'deepseek' if 'deepseek' in MODEL else MODEL,
                               'id': f'{group}:reasoning:{segment}', 'content': reasoning, 'decision_group_id': group}
                    for call in getattr(chunk, 'tool_call_chunks', None) or []:
                        if not call.get('name'):
                            continue
                        if not call_started:
                            call_started = True
                            if text:
                                yield {'type': 'assistant_commentary', 'id': f'{group}:note:{segment}', 'content': text}
                                yield {'type': 'answer_preview_reset'}
                        key = call.get('id') or f'{group}:tool-{call.get("index", 0)}'
                        if key not in announced:
                            announced.add(key)
                            yield {'type': 'tool_start', 'name': call['name'], 'call_id': key,
                                   'tool_call_id': key, 'decision_group_id': group}
                    if isinstance(chunk.content, str) and chunk.content:
                        text += chunk.content
                        if not call_started:
                            yield {'type': 'answer_preview', 'content': chunk.content}
                        else:
                            yield {'type': 'assistant_commentary', 'id': f'{group}:note:{segment}', 'content': text}
            finally:
                await stream.aclose()
            if full is None:
                yield {'type': 'error', 'content': '模型未返回内容。'}
                return
            message = message_chunk_to_message(full)
            round_usage.append(getattr(full,'usage_metadata',None))
            actual_model=(getattr(full,'response_metadata',{}) or {}).get('model_name')
            if actual_model: returned_models.add(actual_model)
            messages.append(message)
            requested = list(message.tool_calls or [])
            # Malformed arguments are returned to the model as tool errors;
            # no automatic rewrite, retry or manufactured tool invocation.
            requested += [{**call, '_invalid': True} for call in (message.invalid_tool_calls or [])]
            if not requested:
                finish = (getattr(full, 'response_metadata', {}) or {}).get('finish_reason')
                complete = finish in (None, 'stop')
                try:
                    citations, evidence = persona.citations(calls, text, language) if persona else source_metadata(calls, text, language)
                except Exception:
                    citations, evidence = [], None
                # Compatibility consumers use token events; the website has
                # already painted preview deltas and will not duplicate them.
                if text:
                    yield {'type': 'token', 'content': text}
                from deep_streaming import wants_suggestions
                suggest = agent == 'general' and complete and wants_suggestions(question) and bool(text.strip())
                usage = None
                if round_usage and all(isinstance(item,dict) for item in round_usage):
                    usage = {key:sum(item.get(key,0) for item in round_usage) for key in ('input_tokens','output_tokens','total_tokens')}
                yield {'type': 'done', 'content': text, 'complete': complete, 'runtime_profile': 'bare',
                       'release':release,'main_model_usage':{'scope':'main_agent_only','usage':usage,
                         'round_count':len(round_usage),'reported_rounds':sum(isinstance(u,dict) for u in round_usage),
                         'includes_auxiliary_tool_models':False,'provider_model_names':sorted(returned_models)},
                       'citations': citations, 'evidence': evidence, 'suggestions': [],
                       'suggestions_status': 'pending' if suggest else 'disabled', 'validation': {'enabled': False},
                       'finish_reason': finish, 'duration_seconds': round(time.monotonic() - started, 3)}
                if suggest:
                    try:
                        result = await exploration_questions(question, text, language)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        result = {'suggestions':[], 'status':'unavailable'}
                    yield {'type':'suggestions', **result}
                return
            if not call_started:
                if text:
                    yield {'type': 'assistant_commentary', 'id': f'{group}:note:{segment}', 'content': text}
                yield {'type': 'answer_preview_reset'}

            async def run_call(index, call):
                at = time.monotonic()
                args = call.get('args') or {}
                try:
                    result = ({'error': 'INVALID_TOOL_ARGUMENTS', 'arguments': args} if call.get('_invalid')
                              else await execute(registry.get(call['name']), args, question, agent=agent) if persona else await execute(registry.get(call['name']), args, question))
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    result = {'error': str(exc), 'error_type': type(exc).__name__}
                return index, call, args, result, time.monotonic() - at

            # Each requested call executes, including identical siblings and
            # repeated calls in later rounds. Context is never truncated here.
            results = {}
            for index, call in enumerate(requested):
                key = call.get('id') or f'{group}:tool-{index}'
                call['id'] = key
                if key not in announced:
                    yield {'type': 'tool_start', 'name': call['name'], 'call_id': key,
                           'tool_call_id': key, 'decision_group_id': group}
                tasks.add(asyncio.create_task(run_call(index, call)))
            for completed in asyncio.as_completed(tasks):
                index, call, args, result, seconds = await completed
                if call['name'] in {'get_chapter','verify_quote'}:
                    result = reading_coverage.observe(result)
                serialized = json.dumps(result, ensure_ascii=False, default=str)
                status = tool_status(result)
                calls.append({'name': call['name'], 'args': args, 'result_full': result, 'call_id': call['id']})
                results[index] = ToolMessage(content=serialized, name=call['name'], tool_call_id=call['id'])
                yield {'type': 'tool', 'name': call['name'], 'args': args, 'result': serialized,
                       'call_id': call['id'], 'tool_call_id': call['id'], 'status': status,
                       'duration_seconds': round(seconds, 3),
                       'decision_group_id': group}
            tasks.clear()
            messages.extend(results[index] for index in range(len(requested)))
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        yield {'type': 'error', 'content': str(exc), 'runtime_profile': 'bare'}
    finally:
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if getattr(model, 'root_async_client', None) is not None:
            await model.root_async_client.close()
        if getattr(model, 'root_client', None) is not None:
            model.root_client.close()
