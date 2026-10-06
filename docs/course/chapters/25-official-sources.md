# 第 25 章：资料、版本与后续系统学习

## 25.1 语言主线

- [Python 官方教程](https://docs.python.org/zh-cn/3/tutorial/)：你已有编程基础，适合按模块查语法和标准库。
- [Python asyncio](https://docs.python.org/zh-cn/3/library/asyncio.html)：事件循环、任务、取消与并发工具。
- [Python sqlite3](https://docs.python.org/zh-cn/3/library/sqlite3.html)：连接、事务与参数化查询。
- [MDN JavaScript 学习区](https://developer.mozilla.org/zh-CN/docs/Learn_web_development/Core/Scripting)：语言与浏览器交互。
- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)：闭包、对象、模块等系统查阅。

语言学习下一步：Python 的迭代协议、上下文管理器、装饰器、数据模型、类型检查与打包；JS 的原型、this、事件传播、微任务、内存与性能；再学习 TypeScript，把接口契约前移到编译阶段。无需在做第一个可运行项目之前掌握全部高级特性。

## 25.2 Web 与框架

- [FastAPI 用户指南](https://fastapi.tiangolo.com/zh/tutorial/)：路由、校验、依赖、认证与部署。
- [FastAPI 测试](https://fastapi.tiangolo.com/tutorial/testing/)：TestClient 与接口验证。
- [React 官方中文文档](https://zh-hans.react.dev/learn)：状态、组件、Effect 和复杂交互。
- [MDN Streams](https://developer.mozilla.org/en-US/docs/Web/API/Streams_API/Using_readable_streams)：读取与处理流。
- [Vite 官方文档](https://vite.dev/guide/)：开发服务器、环境变量和生产构建。

继续学习数据库索引与执行计划、事务隔离、HTTP 缓存、浏览器安全、可访问性和生产监控。框架可以替换，这些基础长期有效。

## 25.3 智能体与协议

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)：图与工具循环。
- [LangGraph Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)：不同流模式与版本格式。
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)：checkpoint 与恢复。
- [DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)：供应商工具协议。
- [DeepSeek 思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)：额外字段与历史传递条件。
- [MCP 官方入口](https://modelcontextprotocol.io/docs/getting-started/intro)：外部能力接入。

写作时已核对主要框架与流式接口文档；没有把当前供应商模型名当作永久保证。使用真实模式前核对账户可用模型、限制和价格。示例不会自动升级依赖，版本固定是为了复现实验，不代表永远推荐该版本。

## 25.4 本课程覆盖与不覆盖

覆盖：从现有编程基础迁移语言、理解全栈链路、实现 Agent 核心、学习完整产品的模块与复刻方法、构造评测并定位改进。

不宣称：一本教材等于全部 Python 或全部前端知识；离线演示等于真实模型质量；代码运行等于完整生产安全；读完便自动达到现有 PhiAgent 的全部效果。

最终能力来自完成复刻矩阵和毕业项目。如果某一项依赖的数据、账号或部署资源尚未准备，就明确列为未完成。真实工程的专业性也体现在能够准确说明系统边界。

<!-- NAV -->

[课程目录](../README.md) · [上一章](24-debugging-and-self-check.md) · [下一章](26-python-architecture.md)
