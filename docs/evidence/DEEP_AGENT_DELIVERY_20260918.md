# 深哲通用智能体交付记录

本次只更新通用深哲。主模型固定为 DeepSeek V4.1 Flash，API 模型名 `deepseek-flash`。尼采保留原提示、模型参数、工具注册和前端响应路径。新增界面用 SVG 图标，不使用 emoji。

产品代码提交：`0c18f0735`（`feat: 完善深哲通用智能体推理交付与流式研究界面`）。后续证据文档补充不改变这份产品配置。

后续完整性修复与当前测试入口见[通用推理材料完整性修复](DEEP_CONTEXT_INTEGRITY_20260918.md)：修复工具产物及长问题被静默截断的问题，并将旧阶段源码冻结与当前行为回归明确分开。以下为首轮交付记录，数字保留当时口径。

再后续已补充[研究准入与网页正文读取](DEEP_RESEARCH_WEB_DELIVERY_20260918.md)，当前默认回归为 1357 项通过、15 项历史快照跳过；模型解释和篇幅遵从仍有未通过项，未将这些工程结果当作整体质量验收。

## 当前交付状态

代码和本地可运行版本已经具备完整的研究与对话链路。真实难题中仍出现判准过宽、改变比较条件、把较弱理由扩成较强结论的错误，**不宣称思考质量已经通过验收**。模型、推理强度和提示策略的实验记录见 [思考质量评估](DEEP_REASONING_EVALUATION_20260918.md)。技术检查与哲学论证判断分开记录，成功返回正文不等于论证正确。

本轮没有修改平台 `app/public/`、章节数据、Cloudflare Workers 或尼采人格库。线上 8011 服务和 `backend/static/` 尚未切换；本地验证使用 8012 后端与 5202 前端。原有用户改动及未跟踪文件保留。

最后补测的 Flash/max、65536 总输出预算覆盖两道已知难题，分别用时 136.082、202.272 秒，均完整返回且未截断。保持题设条件等方面有局部进步，仍出现未被理由支持的普遍判准或两难；不足以替换当前默认配置。它与旧阶段提示词不同，不将差异全部归因于预算。此次结果也不改变“整体思考质量尚未验收”的状态。

## 实现范围

- 通用回答取消默认的固定标题、编号和哲学家罗列；主推理默认 `high`、输出预算 16384，辅助论证检查采用 `low`、16384 预算。辅助结果只算中间材料，不以格式正确冒充逻辑成立。辅助预算曾设为 8192，实际请求在 7830 个推理 token 后才开始 JSON，导致截断，因而增加正文余量；供应商的 `max_tokens` 同时约束推理与正文，详见 [官方参数说明](https://api-docs.deepseek.com/api/create-chat-completion/)。
- 公开研究说明可以增量更新；供应商私有推理不进入界面、事件记录或会话历史。正文按完成且通过引用校验的段落发布，最终 `done.content` 是持久化真源。
- 同名并行工具按调用 ID 独立完成；空结果、失败、预算阻止、复用、取消分别显示。去重在占用预算前完成，实际读取保留少量有界补读名额。
- 工具分析的空 JSON、截断输出和已知失败占位不再报成功。有状态工具的本地记忆在成功且请求仍有效时提交；取消或超时后的后台线程不能补写旧结果。
- 原典检索按实际章节定位，读取支持焦点及窗口；语义候选明确未读。来源卡片仅保留被正文引用或明确使用的材料，区分原文片段、摘要和搜索片段。正式出处与逐字引文绑定校验。
- 停止与断线保留已经接收的内容；输出截断最多补全一次。尚无正文时从头作答，有正文时才续写，恢复过程保留本轮工具结果。
- 新通用附件接口支持文本、图片及常见文档，20 MB 上限；失败可重试或移除，转换不阻塞事件循环。实际文档转换依赖已写入锁文件。图片识别限定于可见内容。
- 前端支持附件预览、来源抽屉、继续探索和立即发送下一轮；可选追问不阻塞下一轮。用户明确不要追问时不生成替代模板。

通用工具隔离由 `deep_context`、`deep_agent_tools` 与专用结果门禁实现；共享函数里的新增分支须有通用请求作用域才生效。旧人格调用保留其默认行为，相关隔离已有离线回归。

## 验证及边界

完整后端测试（没有排除历史检查）：

```sh
cd backend
../.venv/bin/python -m pytest tests -q -p no:cacheprovider
```

2026-09-18 完整运行结果：1216 passed，13 failed，106.05 秒。原始日志：`backend/tools/_tmp/deep_delivery_full_20260918.log`。13 个失败均来自 O7 历史阶段的 `git diff` 源码冻结断言，不是运行行为断言；其中部分在本轮修改前的 HEAD 已失败。没有删除这些门禁或将完整套件标为通过。

补齐后续回归并且仅排除上述 13 项后：**1233 passed，13 deselected，100.70 秒**。日志 `backend/tools/_tmp/deep_delivery_current_20260918.log`，完整命令参数 `backend/tools/_tmp/deep_delivery_current_args.json`。这不是完整套件全绿。排除项为：

```text
test_o7a_scholarly_evaluator.py::test_t19_no_production_diff_vs_base
test_o7a_scholarly_evaluator.py::test_r15_no_production_imports_and_diff
test_o7a_scholarly_evaluator.py::test_t21_no_production_imports_and_diff
test_o7b_bibliographic_metadata.py::test_r17_production_frozen[backend/final_validator.py]
test_o7b_bibliographic_metadata.py::test_r17_production_frozen[backend/agent_runtime.py]
test_o7b_bibliographic_metadata.py::test_r17_routes_within_rp1_scope
test_o7b_bibliographic_metadata.py::test_t17_production_frozen_rp2
test_o7c_scholarly_retrieval.py::test_c29_primary_retrieval_unchanged
test_o7c_scholarly_retrieval.py::test_t21_production_frozen
test_o7d_scholarly_corpus.py::test_d25_d26_primary_and_o7b_unchanged
test_o7d_scholarly_corpus.py::test_d30_production_frozen
test_o7d_scholarly_corpus.py::test_r19_production_frozen_rp1
test_o7e_repair_compat.py::test_r10_validator_semantics_unchanged
```

最终前端 `npm test` 包括既有 22 项会话检查、O9 研究检查、19 项通用流式/续问状态检查、8 项实际 JSX 来源渲染检查，全部通过；`npm run build` 成功。构建保留既有 Mermaid 大分块提示。浏览器验证使用真实模型与本地接口，实际查看了附件处理、取消和刷新持久化、并行工具、章节来源链接及抽屉键盘焦点；离线状态测试覆盖迟到事件与下一轮请求的隔离，并以真实会话存储覆盖较早附件移出最近 20 条历史、继续探索、刷新和连续 12 次续问，避免上下文递归膨胀。最后辅助预算变更后的针对性测试为 116 passed。

最新浏览器原典请求读取《论语·学而篇》，完成检索及章节读取，正文只有一个正式出处，来源面板也只有同一出处；抽屉标记“已读取原文片段”，并链接到正确章节。验证中发现“不加延伸建议”未被识别，已补充这一表达的回归。随后浏览器实际经历开发服务断开、刷新保留错误、点击“继续回答”，正确恢复为不超过 120 字的一段可证伪解释，没有标题、列表或延伸建议。截图和运行日志位于 `/tmp/phiagent-ui-20260917/`，它们是本机验证产物，不作为仓库资源。

仍需注意的实际限制：

- 难题论证仍存在错误，尤其是反例是否真正保持题设条件，以及结尾能否由前文推出。现有机械校验主要保证交付、工具和来源事实，不能证明哲学推理正确。
- 会话与附件背景在当前浏览器保存。本轮没有接入跨设备会话同步，也没有将既有未跟踪的认证/历史草案混入交付。
- 取消可阻止迟到的本地记忆提交，无法撤回已提交给外部服务的图像生成请求。
- 图片识别沿用已有辅助服务；固定 Flash 指主对话模型，不代表所有外部工具都由同一模型执行。

## 本地验证与后续发布

本地从仓库根目录启动后端：

```sh
cd backend
../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8012
```

另一个终端启动前端：

```sh
cd agent-app
AGENT_API_TARGET=http://127.0.0.1:8012 npm run dev -- --host 127.0.0.1 --port 5202
```

配置沿用根目录 `.env`，不复制或提交密钥。可选通用参数：`DEEP_AGENT_REASONING_EFFORT=high`、`DEEP_AGENT_MAX_TOKENS=16384`；不设置时即使用这些默认值。尼采不读取这两个通用参数。

正式发布方式仍遵循 [部署说明](../DEPLOYMENT.md)：构建通用前端到 `backend/static/`，再重启已有 launchd 后端。发布前保留上一版静态目录与源代码提交；回滚时恢复对应静态产物和源代码，再重启同一后端。本轮未执行这两个线上切换步骤。
