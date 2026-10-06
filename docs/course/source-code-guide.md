# 核心代码导读：你应当能解释每一条边界

这篇配合 `examples/phiagent-lab/phiagent_lab/` 使用。建议第 13 章后逐个文件读，不要一开始就把全部实现粘进编辑器。

## 1. library.py：从确定性函数开始

PASSAGES 是三个教学概述的内存字典。id 是引用与查找身份，title 用于展示，text 是工具实际返回的内容。材料明确不是真实哲学家原文，避免把演示输出当作研究资料。

SearchArgs 和 ReadArgs 是输入契约。`extra="forbid"` 拒绝工具未声明的参数，`strict=True` 避免将字符串悄悄转换为数字。query 最长 200、limit 最大 5 都属于执行约束，模型即使请求更多也不能绕过。

search_library 把查询提取为词项，对中文长字符串进一步产生相邻二字片段。遍历每个材料，计算命中词项长度总和，再按得分和 id 排序。它故意简单：你可以预测结果并测试它。后续要替换成真实检索时，只需保持返回契约。

REGISTRY 保存 schema、function、description。tool_specs 把 schema 转为模型可见 JSON 定义；execute_tool 按白名单查函数，验证参数，用 `**parsed.model_dump()` 展开为关键字参数调用。

你应能解释：模型看到 description 与 JSON schema，程序实际执行 function；两者在一个注册项中关联，但并不是同一件事。

## 2. model.py：一个稳定接口，两种实现

MockModel 检查本轮是否已经收到 tool result。尚未执行时选择搜索，搜索有候选时读取第一项，之后允许回答。它是固定脚本，不会像真实模型一样根据复杂语义自主计划。

`current_turn` 找最后一条 user 消息，避免把之前一轮工具结果当成本轮已读材料。完整系统要支持更复杂的中间消息和跨轮证据，但这个边界先让你理解“每轮事实”。

HttpModel 从环境读取配置，绝不把密钥放入前端。client 使用异步上下文管理器关闭连接。decide 发非流式工具决策请求；stream 消费上游 data 行，只输出 content 增量，检查异常结束。

provider_options 处理供应商差异：课程选择 DeepSeek 普通非思考模式。若要支持别的模式，你必须保留其要求的字段并更新协议测试。接口兼容不是“名字差不多就能工作”。

## 3. engine.py：状态机的所有部分

State 中 messages 采用追加 reducer，evidence 默认覆盖，rounds 默认覆盖。tools 节点先复制旧证据字典再加入新内容，避免无意原地修改共享状态。

decide 先发出状态事件，检查轮数，再调用模型。若有工具调用，把 assistant tool_calls 消息加入状态，交给 tools；没有工具时设置 ready。课程不使用决策阶段的自然语言作为最终答案，因为最终生成要采用独立流式过程。

tools 节点逐项执行调用。参数 JSON 解析和 Pydantic 校验都可能失败；失败以 tool 消息回传，而不是假装没调用。只有 read_passage 成功结果才进入 evidence，搜索摘要不进入已读全文集合。

answer 节点重新构造最终 system 规则，保留历史与本轮工具结果。每个文本增量同时积累在 parts 并通过 writer 发送。流完成后合并文本、检查引用，再发内部 answer 事件。HTTP 层保存完成后才对外发 done。

这一设计将“模型生成完”“引用基础检查通过”“数据库保存完”三个时间点分开。你可以清楚地决定在哪一步失败、前端应该怎样显示。

## 4. store.py：一对消息作为事务单位

Store 保存数据库路径，不长期共享同一个 sqlite3 connection。每次 with connect 建立事务上下文。save_turn 用 executemany 写入同一轮两条消息，保证失败时不会只保存一半。

history 使用倒序 LIMIT 取最新记录，再 reversed 恢复时间顺序。不同调用传不同 limit：模型上下文 12 条，网页历史最多 200 条。这是教学简化，不是无限历史或分页 API。

当历史超过上下文容量，完整产品需要摘要与 token 预算。摘要保留重要指代和承诺，但直接引语仍应从证据库重新读取。

## 5. app.py：协议与领域逻辑分离

ChatRequest 验证 UUID、长度和非空白。create_app 让测试注入 model 与 db_path。lifespan 在应用启动时创建 Store 与 graph，避免 import 时即连真实服务。

chat 接口为本次调用生成 request_id，并在进程内登记活动会话。events 是异步生成器：先发 start，然后加载历史、运行图、转发事件、保存最终答案、发 done。

异常时发 error，日志只记录请求编号与错误类型；取消重新抛出；finally 解除活动标记。StreamingResponse 消费生成器并把每个 JSON 事件包装为 SSE 帧。

进程内 active 不是分布式锁；UUID 不是权限；接口没有生产登录。这些限制都写在课程中，后续复刻要有对应升级和测试。

## 6. sse.mjs 与两个界面

sse.mjs 只解析网络协议，不管理 UI。这样原生 JS 和 React 可以共用。解析器维护 buffer，找到完整空行分隔后才解析 JSON；TextDecoder 负责字节边界。

原生 app.js 直接创建 DOM，用 textContent 防止把模型输出解释成 HTML。controller 限制同一页面并发请求，localStorage 记住会话 id，boot 从服务器取历史。

React main.jsx 用 state 描述消息，用 ref 保存请求资源。change 先检查当前请求仍是同一 controller，再按 message id 更新。它还不是完整多会话工作区；第 27 章提供进一步的 reducer 实验。

## 7. 一次请求的纸上追踪

问题“自由与责任有什么关系？”经过以下关键数据：

1. POST 带 conversation_id 与 message。
2. state 包含 system、历史、当前 user，rounds=0。
3. mock 决策返回 search_library(query=问题)。
4. 工具结果包含 demo-freedom 的候选摘要。
5. mock 决策返回 read_passage(passage_id=demo-freedom)。
6. 读取结果进入 evidence，前端收到 source。
7. mock 结束检索，answer 输出分块文本。
8. 引用检查确认 demo-freedom 来自本轮 evidence。
9. 数据库原子保存 user 与 assistant。
10. 前端收到 done，用最终文本替换暂显内容。

现在把第 5 步改成不存在的 id，手动追踪每一步会变成什么。这比仅运行十次正常例子更能检验你是否理解系统。
