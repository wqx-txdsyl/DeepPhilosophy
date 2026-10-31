# PhiAgent 模型选择

2026-10-31 · v0.1.8。设置新增“模型”，可选 DeepSeek 与 ChatGPT。ChatGPT 固定调用用户指定的 `gpt-6.1-terra`，使用 Responses API；DeepSeek 保持原服务与默认模型。对话提示词仍为 v0.1.7，哲学家人格和 Project 下线状态不改。

选择保存在当前设备，下次发送时冻结到请求的 `model_provider`。同一会话可连续切换，历史回复使用各自回执中的模型记录，不能按当前设置重标。正在生成的请求保持原选择。退出登录恢复 DeepSeek，ChatGPT 服务端要求登录；密钥仅在服务端读取，不发送到浏览器，未知服务 ID 拒绝而非回退。

服务入口：`GET /api/agent/models` 返回可用状态与公开模型信息；`POST /api/agent/stream_lg` 接收 `deepseek|openai`。ContextVar 在实际 SSE 消费任务中设置并在结束/取消时复位，工具工作线程继承它；范围检查、该轮工具中的生成调用和追问生成跟随该请求。独立后台任务仍使用系统默认服务，不把设备偏好变成全站配置。实验 controlled 运行模式暂不开放 ChatGPT。

OpenAI 主模型保留加密推理项供当前工具回合续接，`store=False`，只把公开文本交给界面。列表形式的 Responses 文本、工具调用及中断状态均已适配；隐藏推理和工具参数不冒充正文。每次调用使用独立 HTTP 客户端，关闭上一轮不会关闭下一轮的连接；连接错误只在同一服务内按 SDK 重试，错误不自动改用 DeepSeek。未调用主模型的确认/范围提示不标为 ChatGPT 生成。

会话标题栏改为粘在视口顶部、使用当前主题的不透明背景，仍占原布局位置；桌面与 390px 窄屏均检查。

验证：真实 Terra/DeepSeek 回复、同会话 Terra→DeepSeek→Terra、生成中切换、Terra 工具往返、康德人格、范围判断、设置和历史刷新恢复、登录边界及标题栏滚动。验收身份与持久化为独立合成数据，未读取真实账户。详见[验收记录](../evidence/model-selection-2026-10-31/README.md)。这不是新增哲学质量跑分。

官方接口与模型参考：[GPT-6.1 Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra)、[推理与工具续接](https://developers.openai.com/api/docs/guides/reasoning)。
