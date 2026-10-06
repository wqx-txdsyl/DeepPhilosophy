# 亲手复刻并改进 PhiAgent：从 C++ / Java 到全栈智能体工程

> 为你定制：会 C++、Java，Python 有基础但不熟练，JavaScript 零基础。
> 编写日期：2026-09-23。目标是掌握完整系统的设计、实现、调试和评测能力。

这套课程的终点是能够独立复刻现有 PhiAgent 的产品能力，并通过对照实验改进它。前半部分使用小而完整的 PhiAgent Lab 练习；后半部分以真实仓库为教材，逐项重建完整产品。Lab 是脚手架，不能把它的演示通过当成已经一比一复刻。

你已经会两门编程语言，不必重新背“什么是变量”。真正需要建立的是新运行时的心智模型：Python 的对象与异步、浏览器的事件循环、HTTP 的请求边界、React 的状态、模型调用的不确定性、证据与生成之间的区别。

阅读不会自动转化为编程熟练度。本教程把每章的完成定义为：能解释、能运行、能独立修改、能定位失败。你可以边学边让我讲解；每次提供章节、你的代码和实际报错，我就能针对你卡住的环节继续教学。

## 交付内容与阅读方式

- `chapters/`：主课程，按顺序阅读。
- [完整教程.md](complete-course.md)：同一套内容合并成的一份长 Markdown，适合连续阅读、搜索和标注。
- [project/](../../examples/phiagent-lab/README.md)：独立可运行的实验项目；不依赖生产书库、生产用户或真实 API 密钥。
- `examples/phiagent-lab/exercises/`：可运行的语言与架构练习。
- [第一课：亲手增加一个工具](first-tool.md)：可以立即动手的一堂实践课。
- [核心代码导读](source-code-guide.md)：逐文件解释实验项目。
- [学习计划与任务卡](learning-plan.md)：按你的已有知识调整学习顺序。
- [练习参考解答](exercise-solutions.md)：解题思路和验收办法；先做再看。
- [能力对照与毕业验收](graduation-checklist.md)：真实 PhiAgent 的能力、代码入口、复刻作业和验收标准。
- [源码工具清单](source-tools.md)：从当前源码静态提取的工具注册清单；不是在线服务的运行时启用清单。
- [验证记录](validation-record.md)：这次实际执行过的检查，以及没有验证的部分。

## 三个学习阶段

| 阶段 | 交付物 | 完成意味着什么 |
|---|---|---|
| A：掌握基础链路 | Python 工具、HTTP API、原生 JS 聊天界面、LangGraph 流程 | 能从输入到输出逐层追踪一次请求 |
| B：复刻完整产品 | React 工作区、真实书库、引用、人格、记忆、研究、多用户服务 | 能按能力矩阵逐项替换和验收 |
| C：证明改进 | 冻结评测集、基线报告、改进实验与回归报告 | 能用质量、速度、成本数据说明优劣 |

“一比一”优先指用户可见行为、数据兼容与错误语义。没必要复刻所有历史文件命名和旧补丁；但如果要求页面像素相同或 API 完全兼容，需要把截图基线和协议快照也纳入验收。书库、人格式样本、外部服务账号与部署资源需要另外准备，代码不能凭空生成这些资产。

## 使用节奏

一次学习可以这样安排：20 分钟阅读，40 分钟手写，20 分钟制造并修复错误，10 分钟写自己的解释。用累计有效学习时数衡量，比承诺几天“精通”可靠。先做每章的小实验，再做里程碑；卡住时回到上一层验证输入输出。

你第一天的任务：读第 00、01 章，运行离线项目，然后在不看答案的情况下给搜索工具增加一个输入约束，并写一个失败用例。不是先把全部依赖和架构名词背下来。

## 课程目录

<!-- TOC -->

1. [第 00 章：建立学习地图，把环境变成可检查的东西](chapters/00-learning-map-and-environment.md)
2. [第 01 章：从 C++ / Java 迁移到 Python](chapters/01-python-migration.md)
3. [第 02 章：把 Python 脚本写成可维护程序](chapters/02-python-engineering.md)
4. [第 03 章：async / await，真正理解服务为什么会卡住](chapters/03-async-and-lifecycle.md)
5. [第 04 章：从 Java Controller 到 FastAPI 后端](chapters/04-http-and-fastapi.md)
6. [第 05 章：数据库、事务与对话记忆](chapters/05-sql-and-conversations.md)
7. [第 06 章：JavaScript 从零学，但利用你的 Java / C++ 基础](chapters/06-javascript-migration.md)
8. [第 07 章：让 JavaScript 有一个可以操作的界面](chapters/07-html-and-css.md)
9. [第 08 章：Promise、fetch 和不会丢字的流式聊天](chapters/08-promises-fetch-and-streaming.md)
10. [第 09 章：从操作 DOM 到 React 状态驱动](chapters/09-react-workspace.md)
11. [第 10 章：把大模型当成一个有不确定输出的依赖](chapters/10-model-api-protocol.md)
12. [第 11 章：提示词工程，学习如何写可验证的行为要求](chapters/11-prompts-and-context.md)
13. [第 12 章：不用框架，亲手写出 Agent 的核心](chapters/12-manual-agent-loop.md)
14. [第 13 章：用 LangGraph 表达状态、分支和循环](chapters/13-langgraph-state.md)
15. [第 14 章：从关键词搜索到可评测的 RAG](chapters/14-rag-retrieval.md)
16. [第 15 章：让回答可核查，而不只是附几个链接](chapters/15-citations-and-verification.md)
17. [第 16 章：接入真实书库，理解内容工程](chapters/16-library-data-pipeline.md)
18. [第 17 章：哲学家人格、长期记忆与有状态对话](chapters/17-persona-and-memory.md)
19. [第 18 章：研究型 Agent，怎样查到足够而不是无止境搜索](chapters/18-research-workflows.md)
20. [第 19 章：MCP、网络检索、上传文件与图表能力](chapters/19-mcp-and-files.md)
21. [第 20 章：从本地实验到真实多用户服务](chapters/20-authentication.md)
22. [第 21 章：证明系统可靠，证明回答更好](chapters/21-testing-and-observability.md)
23. [第 22 章：按现有 PhiAgent 的完整能力施工](chapters/22-implementation-order.md)
24. [第 23 章：优化架构之前，先确定你要改善什么](chapters/23-evidence-and-comparison.md)
25. [第 24 章：卡住时按哪条路径排查](chapters/24-debugging-and-self-check.md)
26. [第 25 章：资料、版本与后续系统学习](chapters/25-official-sources.md)
27. [第 26 章：Python 进阶补课——类、装饰器、协议和上下文管理器](chapters/26-python-architecture.md)
28. [第 27 章：用纯函数解决前端竞态，再引入 TypeScript](chapters/27-javascript-typescript.md)
29. [第 28 章：亲手实现一个超出聊天的功能——哲学观点比较](chapters/28-requirements-to-features.md)
30. [第 29 章：毕业项目——完整复刻、迁移与改进](chapters/29-graduation-project.md)

## 官方资料如何使用

正文是可以独立跟做的主线；官方文档用于查精确语法和版本差异。来源集中列在第 25 章，并在相关章节直接链接。样例依赖版本记录在 `examples/phiagent-lab/requirements.txt`；使用最新库时，先阅读升级说明再修改锁定版本。

## 代码约定

标注“完整脚本”的代码可以直接保存运行；标注“局部片段”需要放进指定文件；标注“设计草图”的部分表达接口和约束，不冒充可直接运行的成品。所有运行命令会注明工作目录。生产仓库的阅读任务默认只读，不要求修改已有可运行系统。
