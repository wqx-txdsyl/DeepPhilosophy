# AUTONOMOUS LOOP STATE — PhiAgent O7-E Builder

> 恢复辅助文件（真源 = Reviewer Chat + Git repository）。
> V9-F5 CLOSED（R3 PASS）; V10 formal qualification 执行中
> QUALIFICATION_HEAD=51aed14caabe8f5a8297c36f24fdbed12579b84e（冻结, run 已启动）

```
CURRENT_REVIEWER=GPT-5.6 Sol
CURRENT_PHASE=O7-E V12（DeepSeek V4.1 Flash 基座迁移+requalification）——V12_AUTHORIZED=true 已收到, 等待 Reviewer 下发正式 V12 任务书
CURRENT_REVIEW_STATUS=V11_REVIEW=FAIL_CONFIRMED → V11_FORMAL_QUALIFICATION=FAIL_FROZEN（DELIVERY/SCHOLARLY 双 FAIL_FROZEN, 永久保留; Reviewer 精确修正: V11-05 另残留 2 个 NEAR_QUOTE_NOT_MARKED）; V10 状态不变; 不开 V11 patch 不重跑
BASE_SHA=75e5bcea6497b36695015d389dc2d578d722d9f9（V10 授权基线 = V9-F5-R3 ARCHIVE）
QUALIFICATION_HEAD=51aed14caabe8f5a8297c36f24fdbed12579b84e（manifest+provenance 冻结, docs-only）
NEXT_ACTION=收到 V12 任务书后执行: deepseek-v4-flash → deepseek-flash 迁移 + alias-equivalence check + 兼容回归 + fresh qualification; 禁止针对 V11-02/04/05 写 case-specific 修复; 禁止趁机重构; V12 PASS → O7-E CLOSED → O8
F1_FACTS=根因 CONFIRMED: 触发文本=斯密「中国地震」段落（81 字, answer 本体+replay window 均含; answer 单独探测即 400/1301）; coding-plan 等价端点 trivial 探测 200 但 answer 探测同 400/1301 → 平台级过滤; 4 条恢复路径全部违反冻结或不可行; 39 票 13 case 原样; V10_QUALIFICATION_SUMMARY/FINAL_GATE 原文件未动; 证据=V10_F1_JUDGE_FAILURE_EVIDENCE.json + V10_F1_RECOVERY_ATTEMPT_LOG.json
V10_VERDICT=DELIVERY_GATE=PASS（14/14 发布, repair 7/7 收敛, TERMINAL_PENDING=0, ABORTS=0, 引文/引号零违例, LP_ANCHOR=1.0, COVERAGE=1.0）; SCHOLARLY: applicable_mean=3.646, textual=4.0, argument=3.667, interpretive=3.571, historical=3.385(<3.40), literature=4.0; MEDIAN_LT_2=0; FATAL 全零; 语义守恒 PASS 全零; judge 57 呼叫 39 有效票（13/14 case）; V10-14=bigmodel 1301
V10_MANIFEST=docs/evidence/V10_FRESH_QUALIFICATION_MANIFEST.json（14 case: 恩培多克勒/塞克斯都/库萨/斯宾诺莎V/维柯/谢林/戴维森/威廉斯/洪堡/郭象/记忆哲学争论/伊本·西那/西田（降级）/斯密引文）
V10_FRESHNESS=193 prior questions, max_sim<=0.2386 < 0.45, PREVIOUSLY_CONSUMED=0
V10_RUN_CMD=SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_production_calibration.py V10_QUAL - docs/evidence/V10_FRESH_QUALIFICATION_MANIFEST.json
V10_RUN_OUT=backend/tools/_tmp/o7e_calib_V10_QUAL.json（增量写入, 断点续跑）
V10_JUDGE_CMD=python -c "import ...; judge_candidate('V10_QUAL', runs_path='backend/tools/_tmp/o7e_calib_V10_QUAL.json', out_tag='V10_QUAL_JUDGE', manifest_path='docs/evidence/V10_FRESH_QUALIFICATION_MANIFEST.json')"
FREEZE_RULE=QUALIFICATION_HEAD 后禁止一切 production code diff; 案例表现差不许换/删/重跑; judge 缺票 EVALUATION_INVALID=true → STOP
PRODUCTION_MODEL=deepseek-v4-flash（经 CC 注入; api 冒烟 200; scholarly TRUSTED_PROXY 双 provider 可达）
FINAL_GATE_BLOB=22ea181ce652276234f59a96d2b5c5f1a66ef2d8（冻结, 复验过）
IAB_INPUT_BROKEN_NOTE=内置浏览器 trusted input 失效; 绕过: 分块 execCommand insertText + 合成 PointerEvent/MouseEvent click（data-testid=send-button, label 'Send prompt'）
STASH_WARNING=仓库有陈年 stash@{0}（master 时代 WIP）; git pathspec 相对 cwd——务必先 cd 仓库根再操作（2026-09-11 曾因 cwd 在 backend/ 误弹 stash, 已 reset --hard 恢复）
```

## O7-E 终点政策与 V12 路线（2026-09-12 Reviewer 会话确认）

```
O7_E_FINALIZATION_POLICY=V11=旧基座最后一次 formal qualification（baseline）; V12=小型 DeepSeek V4.1 Flash 基座迁移+requalification; V12 PASS → O7-E CLOSED → O8; 用户主动扩 scope 撤销了"无 V12"冻结
V10_F1_REVIEW=PASS / V10_F1_CLOSED=true（root cause CONFIRMED_WITH_DIAGNOSTIC_REPRODUCTION; MEASUREMENT_NOT_RECOVERABLE 分支正确）
V10_FORMAL_STATUS=DELIVERY=PASS_CONFIRMED / SCHOLARLY=NOT_ESTABLISHED / FORMAL_QUALIFICATION=MEASUREMENT_INVALID_NOT_RECOVERABLE（永久保留; 13-case partial mean 不作为正式 FAIL）
V11_DELIVERED=完整有效测量（11/11 判定 33/33 票零失败, EVALUATION_INVALID=false, 守恒 PASS）; frozen gate=DELIVERY_GATE_NOT_MET: FAILED_GATES=[FINAL_PUBLICATION_RATE(0.786<0.90), HISTORICAL_DISCIPLINE_REQUIRED_MEAN_MIN(3.091<3.40), INTERPRETIVE_PLURALITY_REQUIRED_MEAN_MIN(2.857<3.00), REQUIRED_DIMENSION_MEDIAN_LT_2(=4)]; 3 例未发布=UNSUPPORTED_EXACT_QUOTE 干净拒绝（诚实性合同生效）; V11 回执已发, Reviewer 深度审查中
V12_PLAN=deepseek-v4-flash → deepseek-flash（DeepSeek V4.1 Flash, 2026-09-10 发布, 旧 id 官方临时路由到新模型）; 范围=model config/env/provider adapter（仅确有兼容问题）/provenance/qualification evidence; alias-equivalence check; 冻结 Main Agent 架构/prompt constitution/retrieval corpus/validator/Local Patch/judge/final gate/tool contracts; 禁止趁机重构
IAB_NOTE=Reviewer 会话中用户可随时插话（2026-09-12 用户两问: O7 收尾疑问→终点政策; V12 换基座→已批准）; 回执裁定可能被用户消息延迟, 轮询时区分「回执后第一条回复」是否为对用户插话的解答
```

## 会话定位规则（跨 session 恢复用）

1. ChatGPT 侧边栏 Recents 最新「V7 F2 审查结论」= 当前 Reviewer 会话。
2. 永远在**最新** Reviewer 会话提交回执; 不回封存旧会话。
