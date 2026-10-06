# 联网与学术检索修复验收

日期：2026-09-28。已更新本机 LaunchAgent 托管的后端及 `agent.deepphilosophy.top` 的智能体前端。未修改极简 SP、主模型或主 agent 的研究预算；未扩充书库。

## 最终实现

1. `websearch` 优先使用已有官方 DeepSeek API 凭据，访问 Anthropic 兼容 Messages 接口的原生 Web Search。只取实际 `web_search_tool_result` 记录与 citation 摘录，不把模型生成的回答或“我查到了”当作搜索结果。服务端搜索会产生额外模型 token 用量，返回 usage 供检查。
2. 凭据只用于配置明确指向的官方 DeepSeek 服务；若主模型配置为其他供应商，不把它的密钥发给 DeepSeek。认证请求拒绝重定向。
3. 保留无需新账号的 Bing/百科兜底，补齐请求头、结果链接解析及来源状态；不将首页、验证码页或完全无查询词匹配的结果当作成功。百科兜底标记为 encyclopedia_only。
4. 学术长查询改为发现候选而非要求标题重复问题的大部分关键词；两词查询仍须匹配两词，避免 free will 混入 free software / Williams。结果附 query_match，仅表示词面候选，不代表论文质量或足以回答问题。
5. 记录每个学术来源的调用、原始命中数、过滤和改写情况；同一次检索遭遇限流/鉴权拒绝时，不再对该来源重复改写重试，保留 Retry-After。
6. 更新缓存键以避开旧空结果；失败不作为成功缓存复用，正常空结果最多缓存60秒，正常命中最多600秒。缓存响应明确标注。
7. 工具事件和界面区分 success、empty、partial、error；历史“success”事件若实际包含空结果或来源错误，也可从完整 JSON 重判。仅有已截断文字的历史记录不能恢复未知事实。

## 协议依据

- [DeepSeek 官方 Claude Code 集成说明](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code/)明确支持原生 Web Search，并说明额外 token 用量。
- [官方 Harness 适配器](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/web/web-search-deepseek/src/provider.ts)使用 Messages 接口及 `web_search_20250305`。

主对话继续使用现有 Chat Completions 链路；只为搜索工具单独使用 Messages 协议。未切换主智能体编排。之前仅沿着旧网页抓取通道排查，遗漏了这个可复用的原生能力，本轮已纠正。

## 真实工具复测

使用后台启动配置，在独立进程调用最终工具代码；隔离检索缓存并关闭学术发现持久写入，避免污染书库。不是一轮完整哲学回答测评。

|查询/动作|结果|
|---|---|
|联网：冯苇杭|DeepSeek 服务端返回7条记录，其中包括“冯苇杭的新片场空间”；结果并非全部相关，需要智能体继续核查|
|联网：Immanuel Kant|DeepSeek 服务端返回10条记录，包括人物及学术出版页面|
|联网：教育部 严禁教师 违规收受 礼品礼金|DeepSeek 服务端返回10条，包含教育部、中国政府网的相关文件|
|读取上一步实际返回的教育部链接|WEB_PASSAGE_READ，取得1542字符页面正文，包含文件标题及教监〔2014〕4号；没有把搜索摘要冒称网页全文|
|学术：gift giving reciprocity obligation in hierarchical relationships ethics|8条候选，其中3条摘要可读；本次没有provider_errors|
|学术：gift reciprocity|4条候选，其中2条摘要可读；OpenAlex HTTP429，其他来源保留，状态partial，保留Retry-After|
|读取真实返回的可读学术记录|ABSTRACT_AVAILABLE，取得1299字符摘要；未宣称已读论文全文|

原始归一化工具回执见 `search_tool_repair_20260928/`。没有存入密钥、认证头、模型内部思考或加密网页载荷。

## 验证与部署

- 本轮相关后端测试：157 passed，2 skipped（可选联网测试）。涵盖原生结果解析、拒绝“只有模型文字”的伪搜索、凭据目标、失败兜底、相关性、空结果、限流不重复调用、阅读传输及裸 agent 回归。
- 旧编排兼容测试单独使用 `DEEP_AGENT_RUNTIME=controlled`：154 passed，2 skipped。默认裸模式下运行这些旧夹具会因其假模型不具备 model_name 失败；未恢复任何旧预算来迎合夹具。
- `agent-app` 的 `npm test` 和 `npm run build` 通过；构建仍有原有大 chunk 提醒。
- 新构建资源以追加方式同步到 backend/static，保留旧哈希资源，最后替换 index.html；后端 LaunchAgent 已重启，`/api/health` 返回 healthy。
- 公开站点主脚本 `/assets/index-BNbjk9Ru.js` HTTP200，包含“部分来源失败”；Cloudflare 可能改写 index.html，因此不以整页字节一致作为验收条件。

## 剩余限制

OpenAlex 公共配额仍可能限流；这属于外部服务条件，本轮不能保证其永远成功。系统会暴露降级而不是用空列表冒充无相关文献。学术候选召回改善不等于语义相关性或学术质量已全部验收；仍需读摘要/原文。免费网页兜底也非稳定性保证，主路径已改为实测成功的 DeepSeek 原生搜索。
