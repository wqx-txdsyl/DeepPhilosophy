# LIVE RUN 2 落盘核验与 run1 口径对照

核验日期：2026-10-02。核验范围是采集完整性、来源访问层级和比较条件，**不包含逐题哲学质量评分**。原始题目轨迹未改动；汇总文档只更正摘要口径、补充核验说明，全部最终回答仍保持原文。

## 完整性结论

- 70 份题目 JSON：65 COMPLETED，5 个 K 组 SKIPPED_NOT_READY，题号/题目/追问序列与 prompts.jsonl 一致。
- 目录另有 `_RUN_META.json` 和 `_PREFLIGHT.json`，共 72 个 JSON；全部可解析。
- 77 轮全部 DONE、finish_reason=stop；没有流错误、空回答、token 拼接与 done.content 不一致，或工具宣告/返回数量缺口。
- 1218 条工具返回全部为可解析 JSON；77 轮最终回答全文都存在于汇总文档。
- 修正摘要后的 run2 文档共 1,873,344 字符；回答原文 174,334 字符。字符包含 Markdown、英文、URL 等，不能当作中文汉字数或 token 用量。
- 逐文件 SHA-256、原始统计和检查结果在 [LIVE_RUN2_EXECUTION_AUDIT.json](/Users/sen/DeepPhilosophy/docs/evidence/phiagent_benchmark_v0_1/LIVE_RUN2_EXECUTION_AUDIT.json)。

上述信息支持“采集完整、可进入内容评审”。元数据写入了结束时间，但本目录没有保存包含退出状态的终端日志；exit 0 / ALL DONE / 尾部 httpcore2 噪音的时间关系以提供的执行报告为据，不能从轨迹文件独立重建。没有发现落盘受损，不把清理异常算作回答流错误。

## 可复算的比较

| 指标 | run1 | run2 |
|---|---:|---:|
| 完成题 / 协议跳过 | 65 / 5 | 65 / 5 |
| 对话轮数 | 77 | 77 |
| 元数据批次墙钟 | 31分58秒 | 46分01秒 |
| 逐题耗时合计 | 62.9分钟 | 92.8分钟 |
| 工具调用 | 1033 | 1218 |
| 回答字符数 | 160472 | 174334 |
| 首 token 中位数（采集口径） | 3.9秒 | 11.0秒 |
| 学术工具严格 success / 总调用 | 0 / 82 | 123 / 157 |
| 学术工具 partial / error | 0 / 82 | 24 / 10 |
| 网页正文读取成功 / 尝试 | 80 / 123 | 137 / 198 |
| search_books / get_chapter | 397 / 217 | 403 / 217 |
| SP 字符数（记录的 git 版本） | 23 | 642 |

run1 有一份先行题目比主批次元数据开始时间早 19 秒；从最早保存的 runner.started 到 finished 是 32分17秒。两种计时口径都不能把 62.9 分钟作为 run1 墙钟。run2 的批次耗时比 run1 更长，不能声称它用 46 分钟比原来“62.9 分钟”更快。首 token 指 token/answer_preview 首到，不是思考流首包，也不是用户第一次看到任何输出的时刻。

两轮 git 版本分别为 `575955a1ef7b35aae1d611b44ba712ac27e77a21`、`ea2c286bf70083c01972e5fe127761da94d298e6`。backend 的差异限于 engine_langgraph.py 的 SP 与 deep_bare_agent.py 的模块说明；核心 bare 循环未改变。**SP 和学术环境同时变化**，加上模型随机性、日期和外部来源差异，本次可做现象对比与缺陷评审，不能识别 SP 的单独因果效果。run2 的元数据只保存未提交条目数量 48，没有路径清单或工作区源码哈希，不能独立验证“全部只改文档/数据”的声明。

## 修正的两项具体计数

- J01/J02 各 4 轮，J03/J04/J05 各 3 轮，J 组共 17 轮，即 5 次初问加 12 次追问。不是 5 题都各有 3 次追问。
- A01 总共 21 次工具：search_books 5、websearch **14**、get_chapter 1、verify_quote 1；14 次联网是 11 success、3 error。run1 A01 没有 websearch；“这一次开始联网”已得到轨迹支持，不能据此承诺此类问题以后都必定选择合适渠道。

## 学术渠道恢复的实际边界

82 次 search_scholarship 为 48 success、24 partial、10 error；75 次 get_scholarly_source 均记录 success。

这 75 次读取涉及 73 个不同 source_record_id，其中 **74 次返回非空 abstract.text**、1 次仅书目信息。工具访问字段对应 74 ABSTRACT_AVAILABLE、1 METADATA_ONLY；72 次明确填写返回证据等级为 ABSTRACT_AVAILABLE，另外 3 次未填写该字段。**没有论文全文证据返回。** 123 次 success 不是 123 篇论文，也不代表论文全文可达性通过。还需在内容评审中检查摘要能支持哪些具体断言、有没有把摘要/题名当作全文。

`scholarly_cache.json` 从备份恢复解决了这次运行的环境阻塞，但 `_load_cache()` 目前仍不防 JSON 根值 null，故障仍可能复发。本轮用了显式 TRUSTED_PROXY；本次核验不修改生产网络模式，也不把这次 preflight 推广为所有部署环境均已恢复。

## 采集协议与端到端验收边界

1. 进程内直调与生产路由委托的核心引擎相同，但跳过 HTTP、认证、SSE 心跳/代理和前端。零流错误不能证明手机网络、聊天列表、复制和引用跳转正常。
2. runner 的 DONE 分支只 return 出事件处理函数，外层 async for 没有 break。本次历史 bare 版本在 DONE 后自然结束，所以结果未因后处理污染；以后引擎增加后处理时，这份 runner 不能保证“done 即停”。
3. 思维文本拼接与工具完整返回保留，但工具结果缺 call_id/decision_group_id；provider reasoning 缺分段 ID/时间戳。不能精准重建并行工具与各思考段的穿插，也不能称为无损 SSE 回放。不要给历史轨迹补造这些字段。
4. J 组显式 history 传递已核对；未传 conversation_id 不等于请求记忆已隔离。runner 没有安装独立记忆 ContextVar，本核验也没有证明发生过实际污染。
5. 77 轮 token_usage 全为空，不输出 token 成本推断。5 个 K 题仍未实际测试，不把占位记录算作故障/注入防护验证通过。

## 内容评审的入口

冻结状态 [RUBRIC_STATUS.json](/Users/sen/DeepPhilosophy/docs/evidence/RUBRIC_STATUS.json) 指定 v1.2 为操作规范冻结，自动评分器未通过校准。后续可按其量尺独立逐题评审，并对严重错误和高分样本人工复核；不能直接把未经复核的自动分数当作质量提升结论。

优先检查 run1 已确认薄弱的 A01、E01、F01/F02、G01、I04、M01 以及 J 组修正能力：是否维持题设与固定条件、有没有概念偷换/过强结论、证据是否真正进入论证、是否如实区分摘要和全文。这里没有新增质量分，也没有重跑智能体或调用评审模型。
