"""Default dispatch stays on the current release; compatibility is explicit."""
import asyncio
import pytest
import agent_release
import engine_langgraph as engine
import deep_bare_agent as bare


@pytest.mark.parametrize('agent', ['general', 'nietzsche'])
def test_default_dispatch_uses_current_bare_loop(monkeypatch, agent):
    monkeypatch.delenv('DEEP_AGENT_RUNTIME', raising=False)
    calls = []

    async def stream(question, history, **kwargs):
        calls.append((question, kwargs.get('agent', 'general')))
        yield {'type':'done', 'content':'offline'}

    monkeypatch.setattr(bare, 'stream_bare_agent', stream)

    async def collect():
        return [event async for event in engine.stream_agent('问题', [], agent=agent)]

    assert asyncio.run(collect()) == [{'type':'done', 'content':'offline'}]
    assert calls == [('问题', agent)]


def test_profile_switch_keeps_current_policy_separate_from_controlled_protocol(monkeypatch):
    monkeypatch.delenv('DEEP_AGENT_RUNTIME', raising=False)
    monkeypatch.delenv('PHIAGENT_PROMPT_VERSION', raising=False)
    monkeypatch.setenv('DEEP_PROMPT_VERSION', 'v2')
    assert engine.get_system_prompt('general') == agent_release.prompt_spec()['text']
    messages = engine._build_context_messages('general', 'zh', repair_mode=True,
                                               repair_output_mode='LOCAL_PATCH')
    assert len(messages) == 1 and messages[0].content == agent_release.prompt_spec()['text']
    assert engine._build_context_messages('general', 'zh', reinforce=True) == []

    monkeypatch.setenv('DEEP_AGENT_RUNTIME', 'controlled')
    monkeypatch.delenv('DEEP_PROMPT_VERSION')
    messages = engine._build_context_messages('general', 'zh', repair_mode=True,
                                               repair_output_mode='LOCAL_PATCH')
    assert len(messages) == 1
    assert engine.LOCAL_PATCH_SYSTEM_PROTOCOL in messages[0].content
    assert engine.REPAIR_SYSTEM_PROTOCOL not in messages[0].content
