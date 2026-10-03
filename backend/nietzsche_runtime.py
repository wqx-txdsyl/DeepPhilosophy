"""Nietzsche persona on the same unbudgeted streaming loop as the general agent."""
def system_text(language='zh', question=''):
    import agents
    text = agents.AGENT_PROMPTS['nietzsche']
    text += ('\n\n本轮使用英文思考和回答，覆盖上文中文语言要求。' if language=='en' else '\n\n本轮使用中文思考和回答。')
    text += '\n直接回应当前问题。问候简短自然；动作描写可以省略，不因人格表达把简单问候展开成训诫。讲解、阅读、核验等明确任务按用户要求完成。'
    detected = agents.detect_temporal(question)
    if detected:
        text += '\n'+agents.temporal_directive('nietzsche',detected,language)
    return text


async def tools():
    from engine_langgraph import _tools_for_agent
    from deep_bare_agent import load_tools
    shared = await load_tools()
    names = {tool.name for tool in shared}
    return shared + [tool for tool in _tools_for_agent('nietzsche') if tool.name not in names]


def citations(calls, answer, language):
    from evidence_contract import build_evidence_contract
    from deep_sources import enrich_citations, primary_research
    evidence = build_evidence_contract(calls,answer,'nietzsche',language)
    found = enrich_citations(evidence['citations'],evidence,calls,answer)
    evidence['display_citations']=found
    evidence['primary_research']=primary_research(found,calls,answer)
    return found,evidence
