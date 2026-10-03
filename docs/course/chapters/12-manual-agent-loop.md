# 第 12 章：不用框架，亲手写出 Agent 的核心

## 12.1 工具循环的最小定义

你提供消息和工具定义；模型返回普通回答或工具调用；程序验证并执行工具；工具结果进入消息历史；再次调用模型；满足终止条件时返回。这个循环使模型可以根据新观察调整行动。

固定顺序的搜索工作流与模型自主选择工具的 Agent 都有用途。不要把每次函数调用都称作智能体，也不要假设自主程度越高越好。

## 12.2 一份能运行的手写循环

完整脚本，保存为项目根目录 `manual_agent.py`：

```python
import asyncio
import json
from phiagent_lab.model import MockModel
from phiagent_lab.library import execute_tool, tool_specs

async def run(question):
    model = MockModel()
    messages = [{"role": "system", "content": "查询教学材料后回答。"},
                {"role": "user", "content": question}]
    for _ in range(4):
        reply = await model.decide(messages, tool_specs())
        calls = reply.get("tool_calls", [])
        if not calls:
            break
        messages.append(reply)
        for call in calls:
            function = call["function"]
            try:
                args = json.loads(function["arguments"])
                result = execute_tool(function["name"], args)
            except (ValueError, TypeError):
                result = {"error": "参数或工具无效"}
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(result, ensure_ascii=False)})
    async for text in model.stream(messages):
        print(text, end="", flush=True)
    print()

asyncio.run(run("自由与责任有什么关系？"))
```

运行 `python manual_agent.py`。它刻意省略数据库和 HTTP，让你只关注决策、执行、观察三个动作。

## 12.3 白名单比动态执行重要

工具注册表把字符串名称映射到你审核过的函数。绝不能使用 `eval(model_output)` 执行模型给出的 Python。参数也必须校验，特别是文件路径、SQL、URL、数量和写操作目标。

库里的 Pydantic 参数模型会拒绝额外字段和错误类型。未知工具返回结构化错误，让模型知道执行失败；它不能凭借“我已经查到了”把失败变成成功事实。

## 12.4 完整的执行契约

每个工具声明：名称、参数 schema、返回结构、是否只读、是否可重试、超时、最大结果大小和权限需求。生成图片、发送邮件和搜索书籍不能使用同一重试策略。

只读工具相同参数可以在同一轮复用成功结果；生成类或有副作用的工具不能凭字符串相同就重放。失败结果也不该永久缓存，否则恢复后的服务仍永远失败。

## 12.5 终止条件

模型表示不再需要工具是正常结束；总时长、工具次数和图步数是硬上限。证据不足时允许诚实结束，而不是永远搜索。上限触发后可以用已有材料作有限回答，但不能宣称已经完成未执行的核验。

工具调用数与模型轮数不同。一轮模型可以发出多个调用，因此只限制轮数未必控制住成本。课程既限制轮数，也限制每轮调用数量；完整系统还需要每用户与全局预算。

## 12.6 练习

给手写循环增加 elapsed_ms、工具次数、错误次数。然后写一个总是要求继续搜索的假模型，验证一定结束。再写一个返回错误 JSON 的假模型，验证不会进入任意执行。

最后用纸画出 messages 在三轮中的内容。每一个工具调用都必须找到对应 tool 消息，调用 id 要相同。这一步做懂了，LangGraph 才是可理解的工程工具。

<!-- NAV -->

[课程目录](../README.md) · [上一章](11-prompts-and-context.md) · [下一章](13-langgraph-state.md)
