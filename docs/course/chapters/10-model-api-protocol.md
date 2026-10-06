# 第 10 章：把大模型当成一个有不确定输出的依赖

## 10.1 四种消息角色

system 给出运行规则，user 表达本轮需求，assistant 是模型输出，tool 是程序执行工具后回传的结果。模型 API 通常没有自动读取你磁盘上历史的能力，你要显式构造上下文。

模型输出的 tool_calls 只是调用请求：包含工具名、参数和调用 id。服务器执行后必须用匹配的 tool_call_id 回传结果。漏一项、顺序错乱或参数不是合法 JSON，可能让下一次模型请求失败。

## 10.2 明确适配器接口

课程定义两个方法：`decide(messages, tools)` 返回是否调用工具；`stream(messages)` 产生最终回答的文本增量。MockModel 与 HttpModel 实现相同接口，外层图不需要知道它们的内部细节。

这是依赖倒置的具体应用：引擎依赖你自己的接口，而不是到处直接拼某供应商 HTTP 请求。以后迁移模型，只需改适配器和对应契约测试。

## 10.3 请求与响应生命周期

HTTP 客户端设置连接超时和读取超时；检查状态；验证响应结构；提取消息；处理流结束标记。429、认证失败、上下文超限不是同一种错误。

实验使用较小 max_tokens 和有限工具轮数控制学习成本。max_tokens 的确切含义与供应商有关；中文字符数不能直接视作 token 数。完整系统应记录供应商返回的 usage，并按实际输入、输出、缓存计价规则计算成本。

## 10.4 接入真实模型

在启动服务的同一个终端设置变量：

```bash
export PHI_MODE=real
export PHI_API_BASE=https://api.deepseek.com
export PHI_MODEL=你账户当前可用且支持工具调用的模型ID
read -s PHI_API_KEY
export PHI_API_KEY
python -m uvicorn phiagent_lab.app:app --host 127.0.0.1 --port 8021
```

`read -s` 在常见交互 shell 中隐藏输入；不要把密钥写入前端、源码或提交历史。课程没有读取你现有项目的密钥，也没有替你发付费请求。Windows 可以通过当前 PowerShell 进程的环境变量设置，避免把密钥写入脚本。

PHI_API_BASE 是不含 `/chat/completions` 的基础地址；有些兼容服务要求末尾 `/v1`。更换供应商必须查其文档，兼容协议不保证所有字段都一样。

课程适配器针对 DeepSeek 显式关闭 thinking 模式；其他供应商默认按普通聊天模式处理。思考模式可能要求保留额外历史字段，不能删字段后仍声称兼容。具体以[供应商协议](https://api-docs.deepseek.com/guides/thinking_mode/)为准。

## 10.5 区分三类测试

Mock 测试证明你自己的流程；协议替身测试证明请求与解析符合预期；真实模型测试观察供应商实际行为和回答质量。三者都需要，但不能相互冒充。

最终输出正在流式生成时，网络失败会留下半截回答。只有成功结束标记和业务校验均通过才标记完成。不要把“收到过 token”记成成功。

## 10.6 练习

增加一个 FakeHTTPTransport，模拟 401、429、200 但缺少 choices、半截流、finish_reason=length。对应测试应证明这些情况不会保存为成功答案。

给适配器增加模型名、协议版本、请求耗时、usage 返回结构。真实模型模式首次验收只用一条短问题，先看工具参数和协议成功，再做质量评测。

<!-- NAV -->

[课程目录](../README.md) · [上一章](09-react-workspace.md) · [下一章](11-prompts-and-context.md)
