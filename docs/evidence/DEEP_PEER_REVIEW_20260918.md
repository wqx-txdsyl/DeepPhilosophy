# 独立审校实验与可复用评测入口

**结果仍不足以通过通用思考质量验收；没有将任何审校方案接入默认对话。** 主模型继续使用用户指定的 DeepSeek V4.1 Flash（`deepseek-flash`），生产服务和尼采路径不变。

## 实际模型实验

使用已消费的新题集中的 `fresh_02`（公共活动室偏爱亲属）和 `fresh_06`（给定四段实名评论文章）。这些是 DEV 复查，不是新 holdout，也不是 B 站博主的官方题库。审校只收到原问题与候选公开正文，没有人工评分、正确答案或私有推理。每条路径每题只采样一次；审校意见只被视为可能有错的建议。

| 路径 | 实际请求 | 完整交付 | 观察结果 |
| --- | --- | --- | --- |
| Flash 审校，再由 Flash 修订 | 2 次审校 + 2 次修订 | 4/4 | 修正了一处本人优先权到亲属优先权的跳跃；遗漏姓氏规则公平性的无据推断和文章中发言者到被指控者的主体转移。 |
| DeepSeek V4 Pro 审校，再由 Flash 修订 | 2 次审校 + 2 次修订 | 4/4 | 有局部修改，但同样遗漏关键错误；对“他人”的一项狭义解释也有争议，未证明该路径更可靠。 |
| 既有 Agnes 配置，仅审校，8192 预算 | 2 次审校 | 1/2 | 活动室题发现局部问题，遗漏核心推断；文章题 `length` 且公开正文为空。 |
| Agnes 文章题，仅将预算改为 16384 | 1 次审校 | 0/1 | 83.490 秒后仍 `length`、公开正文为空。无输出不能判定它能否识别语义错误。 |

合计 11 次实际请求，SDK 重试均为 0；没有失败后自动换题、继续加预算或挑选有利重跑。Flash/Pro 比较的审校预算均为 high、16384，修订始终由 Flash 完成。Agnes 复用既有 `agnes-2.5-pro` 接口，不添加未经验证的推理参数；最后一次只调整输出预算。不同供应商的预算和延迟不能直接当作能力排名。

[公开结果与可核查元数据](DEEP_PEER_REVIEW_20260918.json)保存两道题、原候选、审校公开意见、Flash 修订、请求消息哈希、耗时和 token 计数。原始本地报告路径与文件哈希也在其中；不包含密钥、供应商私有推理或完整请求日志。此前的 [六题首测评审](DEEP_FRESH_EVAL_20260918_REVIEW.md) 仍为 3 PASS、3 PARTIAL，其冻结标准未改。

## 评测入口

新增 `backend/deep_peer_review.py` 和 `backend/tools/review_deep_candidate.py`，只用于离线评测公开候选，**没有被聊天引擎导入**。默认关闭，不替换主模型，不自动修改答案，不把空问题列表或有效 JSON 当作语义通过。入口的通用审校提示与上面的实验提示不同，尚无新供应商的实际效果结论。

它只发送显式提供的原问题、候选和来源片段；来源仅接受 `id/kind/title/url/scope/text` 文本字段。超出输入限额会拒绝，不默默截断。最多一条请求，120 秒总超时、16384 输出预算；不自动重试、不跟随重定向、不读取环境代理。取消会终止活动请求。仅接受完整 `stop` 回复，每项问题必须逐字定位到候选中的真实连续原句，最多两项。

返回的 `ADVISORY_ONLY` 只代表审校结果完整且格式、引文定位有效。推断是否正确仍需对照原问题和真实来源检查。截断、坏 JSON、虚构引文、超时和接口错误均单独记录，不冒充“未发现问题”。

如需测试其他 OpenAI Chat Completions 兼容审校接口，在本机根目录 `.env` 中配置以下字段；不要把密钥发到对话或提交仓库。环境变量优先于 `.env`：

```dotenv
DEEP_REVIEW_ENABLED=true
DEEP_REVIEW_BASE_URL=https://provider.example/v1
DEEP_REVIEW_MODEL=reviewer-model-id
DEEP_REVIEW_API_KEY=configure-locally
# 可选；仅当供应商要求时改为 max_completion_tokens
DEEP_REVIEW_TOKEN_PARAMETER=max_tokens
```

示例地址和模型是占位值。`DEEP_REVIEW_BASE_URL` 后会追加 `/chat/completions`；需 HTTPS，本机 loopback 可用 HTTP。配置不自动启用生产审校。只检查配置、不联网：

```sh
.venv/bin/python backend/tools/review_deep_candidate.py --check-config
```

输入 JSON：

```json
{
  "question": "原始问题",
  "candidate": "准备评审的完整公开回答",
  "evidence": [{"id": "read-1", "scope": "read_excerpt", "text": "确实读取的来源片段"}]
}
```

执行一次评测：

```sh
.venv/bin/python backend/tools/review_deep_candidate.py \
  --input backend/tools/_tmp/review-input.json \
  --output backend/tools/_tmp/review-result-001.json
```

输出目录须已存在；输出文件必须是新文件，防止覆盖旧结果。报告会保存发送的公开材料及结果，请按输入内容的保密要求管理。退出码 0 表示完整的咨询性审校，**不代表答案正确**；1 为接口或审校交付失败，2 为禁用、无效输入、配置或输出路径问题，130 为手动取消。

## 验证与当前阻碍

22 项离线测试通过，覆盖默认禁用不联网、显式来源范围、精确引文、非法结构、输出体积上限、超时、取消、错误内容不泄露、禁止自动重试及禁止覆盖旧报告，以及实际回环请求绕过环境代理。当前本机审校字段未配置，`--check-config` 返回 `disabled`，没有为这个新入口发起实际请求。

工程入口已经可以用于下一项独立审校验证，但这不能补足尚未通过的思考质量。已测的主模型参数、同模型自审、结构化工具检查、Flash/Pro 审校未稳定解决上述关键错误；Agnes 的第二题也未能交付可评审的公开内容。后续需要一条有实际效果证据的改进路径，不能以工程检查全绿或换用更容易的题目替代它。
