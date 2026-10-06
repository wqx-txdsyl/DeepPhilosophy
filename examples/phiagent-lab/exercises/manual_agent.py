"""Run: python -m exercises.manual_agent"""
import asyncio
import json
from phiagent_lab.model import MockModel
from phiagent_lab.library import execute_tool, tool_specs

async def run(question):
    model = MockModel()
    messages = [{'role': 'system', 'content': '查询教学材料后回答。'}, {'role': 'user', 'content': question}]
    for _ in range(4):
        reply = await model.decide(messages, tool_specs())
        calls = reply.get('tool_calls', [])
        if not calls:
            break
        messages.append(reply)
        for call in calls:
            function = call['function']
            try:
                result = execute_tool(function['name'], json.loads(function['arguments']))
            except (ValueError, TypeError):
                result = {'error': '参数或工具无效'}
            messages.append({'role': 'tool', 'tool_call_id': call['id'],
                             'content': json.dumps(result, ensure_ascii=False)})
    async for text in model.stream(messages):
        print(text, end='', flush=True)
    print()

if __name__ == '__main__':
    asyncio.run(run('自由与责任有什么关系？'))
