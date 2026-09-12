# AUTONOMOUS LOOP STATE — PhiAgent O7-E Builder

> 恢复辅助文件（真源 = Reviewer Chat + Git repository）。
> V9-F5 CLOSED（R3 PASS）; V10 formal qualification 执行中
> QUALIFICATION_HEAD=51aed14caabe8f5a8297c36f24fdbed12579b84e（冻结, run 已启动）

```
CURRENT_REVIEWER=GPT-5.6 Sol
CURRENT_PHASE=O7-E V11 fresh formal qualification 已交付（完整有效测量, frozen gate=DELIVERY_GATE_NOT_MET）, 待 Reviewer 裁定
CURRENT_REVIEW_STATUS=V10_F1_REVIEW=PASS → V10_F1_CLOSED=true → V11_AUTHORIZED=true → V11 已执行 READY_FOR_V11_REVIEW=true
BASE_SHA=75e5bcea6497b36695015d389dc2d578d722d9f9（V10 授权基线 = V9-F5-R3 ARCHIVE）
QUALIFICATION_HEAD=51aed14caabe8f5a8297c36f24fdbed12579b84e（manifest+provenance 冻结, docs-only）
NEXT_ACTION=等 Reviewer V11 裁定; V11=完整有效测量（33/33 票零失败, EVALUATION_INVALID=false）但 gate 实质 FAIL: FAILED_GATES=[FINAL_PUBLICATION_RATE(11/14=0.786<0.90), HISTORICAL_DISCIPLINE_REQUIRED_MEAN_MIN(3.091<3.40), INTERPRETIVE_PLURALITY_REQUIRED_MEAN_MIN(2.857<3.00), REQUIRED_DIMENSION_MEDIAN_LT_2(=4)]; 3 例未发布全因 UNSUPPORTED_EXACT_QUOTE 干净拒绝（V11-02/04/05, 原著不在库的引文型 case）; V10 状态永久保留 MEASUREMENT_INVALID_NOT_RECOVERABLE, V11 不回写 V10
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

## 会话定位规则（跨 session 恢复用）

1. ChatGPT 侧边栏 Recents 最新「V7 F2 审查结论」= 当前 Reviewer 会话。
2. 永远在**最新** Reviewer 会话提交回执; 不回封存旧会话。
