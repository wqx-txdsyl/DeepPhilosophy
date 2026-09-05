# PhiAgent O7-A — Scholarly Contract & Evaluation Constitution（收尾报告）

> BASE_SHA: `302f7380a4146d78374887063b336c5aa7381ddd`
> SPEC_CODE_SHA（首个规范 commit）: `072b5c8a34b26280e25eeafea28fb2d87a5c0735`
> SPECIFICATION_GATE_SHA（最终冻结）: `f97e88304`（冻结链: 072b5c8a→1ae40675→bd6cf1ab→92d06cab→488b66112→f97e88304，每次修改均为校准基础设施/仪器修正，均在产生完整判定轮次之前或之后如实落 commit）
> Reviewer: GPT-5.6 Sol ｜ Judge: `glm-4-plus` @ bigmodel（temperature=0.0，固定）｜ 被测 Main Agent: `deepseek-chat`（TESTED≠JUDGE ✓）
> TASK_BOOK: docs/tasks/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION_TASK.md（原样落盘）

## 0. 判定提议

```
O7_A = BLOCKED（§36 最低进入 Review 条件两项未达，见 §12 校准数据；按 §37 如实上报，
       不自行放行、不进入 O7-B）
PROPOSED_VERDICT = PATCH_REQUIRED（Patch 方向已定位、成本已估——见 §13）
```

## 1. Phase Boundary（全部达成，T18/T19/T20 + git diff 静态证明）

```
PRODUCTION_POLICY_CHANGED=false  PRODUCTION_TOOLS_CHANGED=false  PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false  PRODUCTION_RETRIEVAL_CHANGED=false  CORPUS_CHANGED_BY_O7A=false
SYSTEM_PROMPT_LG/validator/quote_bound/engine/evidence_state 对 BASE_SHA 零 diff（T19）
生产代码 import evaluator = 0（T18 AST 扫描）; runtime 引擎无反向引用
EVALUATION_ONLY_IMPORT_PATHS = backend/tools/evaluation/{o7_scholarly_judge,o7_scholarly_cases}.py
PARALLEL_DATA_COMMITS_DURING_GATE = 无（gate 期间仅 evaluator/文档 commit）
```

## 2. Positioning / 七纪律（交付 A）

docs/PHIAGENT_O7_SCHOLARLY_CONTRACT.md：定位宣言（哲学研究型 Agent；不是百科人物卡/教辅摘要器/
引用装饰生成器/论文腔模仿器；学术性≠篇幅/术语/引用/人名的堆叠）+ D1 Textual / D2 Argument /
D3 Interpretive Plurality（反万能模板）/ D4 Historical / D5 Bibliographic Honesty（降粒度不伪造）/
D6 Literature Access Honesty（四态 access level）/ D7 Terminological（反装饰）。

## 3. 五维 Rubric（交付 B）

docs/PHIAGENT_O7_SCHOLARLY_RUBRIC.md：R1 Textual Grounding / R2 Argument Reconstruction /
R3 Interpretive Plurality（APPLICABLE/NOT_APPLICABLE，N/A 不计 0）/ R4 Historical Discipline /
R5 Literature Orientation，各 0-4 anchor 全部成文；Applicability 强制语义 + 反风格偏置清单。

## 4. 六致命 Flag（交付 C）

F1 FABRICATED_BIBLIOGRAPHY / F2 FABRICATED_SCHOLAR_ATTRIBUTION / F3 PRIMARY_TEXT_MISREPRESENTATION /
F4 MAJOR_ANACHRONISM / F5 FALSE_EXACT_QUOTE / F6 LITERATURE_ACCESS_OVERCLAIM——
每个 flag 结构 = value/offending_spans/reason/evidence_refs/confidence，与分数完全分离（T4）。

## 5. Claim Ledger（交付 D）

9 类 claim types + SUPPORT 四态 + access_level 字段；EVALUATION_ONLY=true / RUNTIME_IMPORTS=0 /
PRODUCTION_AUTHORITY=0（T12/T13：UNSUPPORTED 主张可表达且无任何 runtime 动作）。

## 6. Judge Harness（交付 E）

backend/tools/evaluation/o7_scholarly_judge.py：输入合同（§9 全字段：问题/类别/回答/身份/证据
digest/原文证据/书目记录/二手记录/访问级别/主张清单——judge 不得只读答案）；输出合同（严格 JSON，
逐分 rationale+spans+missing；schema 拒绝小数分与任何 phase PASS 字段，T14/T15）；judge 看不到
phase 名/Q1Q2 版本/期望分/历史分/目标门（反 anchoring）。渲染 judge 可见输入不含阶段信息 ✓。

## 7. Seed Cases（交付 F = 3/3）

S1「康德」开放学术导航 / S2 先天综合判断论证重构 / S3 物自身两派争议——问题文本逐字收录（T16）。

## 8. Calibration Cases 与 Fixtures（交付 G = 8 例 × GOOD/MID/BAD + L1-L3 专项 = 27 fixtures）

C1 原典出处（中）｜ C2 译名敏感术语（德古）｜ C3 论证重构（近代）｜ C4 历史发展（19C）｜
C5 真实解释争议（德古）｜ C6 文献导向（20C）｜ C7 人格+证据纪律（19C, nietzsche）｜
C8 plurality 不适用（中）——五传统全覆盖、不全康德（T17）；每例含 TASK_CATEGORY/
EXPECTED_APPLICABILITY_PROFILE/KNOWN_PITFALLS/BAD-FLAGS 四要素；BAD fixtures 植入
伪造 DOI/时代错置/摘要越权/解释当原文/假两派/误置篇名等显式错误；L1/L2/L3 覆盖 §19 三种
访问诚实形态。

## 9. 校准执行史（三轮，全部 54 调用/轮，judge 配置逐轮固定）

| 指标 | 第1轮（基线 prompt, t=0.1） | 第2轮（逐flag规则, t=0.0） | 第3轮（+强制核对程序） | §36 要求 |
|---|---|---|---|---|
| GOOD>MID>BAD | ✓（2.83/1.67/0.87→见 log） | ✓（2.83/1.67/0.87 量级） | ✓ 2.633/1.646/0.824 | ✓ |
| FALSE_FATAL_ON_GOODMID | 0 | 0 | **0** | 0 ✓ |
| EXPECTED_FATAL_RECALL | 44.4% | 77.8% | **88.9%**（8/9） | 100% ✗ |
| FATAL_FLAG_AGREEMENT | 74.1% | 92.6% | **100%** | 100% ✓ |
| DIMENSION_DIFF≤1_RATE | 100% | 92.6% | **100%** | ≥90% ✓ |
| APPLICABILITY_AGREEMENT | 74.1% | 74.1% | **77.8%** | ≥90% ✗ |

数据文件: backend/tools/_tmp/o7a_calibration{,_run1,_final,_final2,_final3}.json（全部原始 verdict 保留）。

## 10. 残余缺口诊断（如实）

1. **C6-L1-bad 的 F6 漏报（第3轮唯一漏报，且两轮一致漏）**: fixture 答案以「根据记录，该文第二节
   提出了语用转向论证……」开头——judge 把「根据记录」善意解读为诚实引用，忽略了 METADATA_ONLY
   记录不可能包含章节级内容。判定: **fixture 措辞瑕疵与 judge 边界核对不足各占其一**；
   修正 fixture 措辞（去掉「根据记录」hedge）是合法动作，但连续第 4 轮迭代已构成对单一 fixture
   调参（O6 FQ5 教训: 不围绕单句调优）——停止迭代，如实上报。
2. **APPLICABILITY_AGREEMENT 0.778 恒定**: 全五维 applicability 向量逐轮相等才是达标口径；
   波动集中在 OPTIONAL 维（回答是否"实质涉及"的边界判断跨轮翻转），分数本身高度稳定
   （DIFF≤1=100%）。该口径是否应改为"REQUIRED 维 applicability 一致率"由 Reviewer 裁定。

## 11. Judge Stability / Authority

JUDGE_CAN_SIGN_PHASE_PASS=false（schema 层拒绝，T15）；LLM_JUDGE=测量仪器，
FINAL_REVIEWER=GPT-5.6 Sol（REVIEW_REQUIRED_CASES 与 RANDOM_PASS_SAMPLE_POOL 由
review_manifest() 生成，§34，本轮校准 verdicts 全部可复核）。

## 12. §36 进入 Review 条件对照

```
PRODUCTION_*_CHANGED = false×5 ✓      FIVE_DIMENSION_RUBRIC = COMPLETE ✓
N_A_SEMANTICS = COMPLETE ✓            SIX_FATAL_FLAGS = COMPLETE ✓
CLAIM_LEDGER = EVALUATION_ONLY ✓      SEED_CASES = 3/3 ✓
CALIBRATION_CASES = 8（5≤n≤10）✓      GOOD_MID_BAD_CALIBRATION = COMPLETE ✓
EXPECTED_FATAL_FLAG_RECALL = 88.9% ✗（要求 100%）
FALSE_FATAL_ON_GOOD_FIXTURES = 0 ✓
JUDGE_STABILITY = ACCEPTABLE? 部分（DIM≤1=100% ✓ / FLAG_AGREEMENT=100% ✓ / APPLIC=77.8% ✗）
NO_PRODUCTION_IMPORTS = true ✓        FULL_TESTS_FAILED = 0 ✓（458 passed）
→ 两项未达 → O7_A = BLOCKED（不满足 READY_FOR_FINAL_REVIEW 最低条件）
```

## 13. Patch 提议（待 Reviewer 授权，不自行执行）

1. fixture 措辞修正 1 处（C6-L1-bad 去「根据记录」hedge，保持考察点不变）——5 分钟；
2. judge prompt 增加「METADATA_ONLY 记录不可能包含章节/论证步骤信息，回答出现此类归属即 F6=true」
   的操作化细则——已定位，1 行；
3. APPLICABILITY_AGREEMENT 口径裁定（全向量 0.9 vs REQUIRED-only 0.9）——Reviewer 决定；
4. 以上完成后重跑 54 调用校准 ×2（~25 分钟）再出最终门数。

## 14. Q2 交付基线冻结（§25，O7-E 第二轴）

```
SAME_SET_SINGLE=22/32=68.75%  SAME_SET_MULTI=19/24=79.2%  REPAIR_SUCCESS_SINGLE=15/25=60%
REPAIR_EXHAUSTION_SINGLE=10/25=40%  FRESH_PUBLICATION=13/16=81.25%
VALIDATOR_FN=0 VALIDATOR_FP=0 INVALID_FINAL_PUBLIC=0
O7_E_FINAL_GATE = SCHOLARLY_QUALITY + DELIVERY_RELIABILITY（双轴并列，任何单轴不得遮蔽另一轴）
```

## 15. 元数据/定位符/引用精度宪法（§22-24，只定义不实施）

四层 metadata 来源 Tier、每条 value/source_type/source_locator/confidence/verified、
locator_kind=CANONICAL/EDITION_SPECIFIC/STRUCTURAL、七种 locator_scheme、五级引用精度阶梯
——全文见 docs/PHIAGENT_O7_SCHOLARLY_CONTRACT.md §3。

## 16. 测试与已知局限

```
O7A_TESTS = 15（test_o7a_scholarly_evaluator.py T1-T20 语义合并且全绿; 含零生产导入/零生产 diff 静态证明）
FULL: pytest backend/tests -q → 458 passed / 0 failed
KNOWN_LIMITATIONS:
  1) judge 对边界 fixture 的 flag 召回未到 100%（残余 1 例，见 §10）
  2) applicability 跨轮标签波动（77.8% 向量一致率）
  3) judge=glm-4-plus 单一供应商; 换 judge 需重新校准
  4) fixtures 均为中文短答（150-350 字），长文回答的行为未采样
  5) 5-10 calibration 案例中史学/术语维主要靠 C2/C4 覆盖，密度有限
O7_B_AUTHORIZED = false（未授权，未动）
```


---

# O7-A RP1 — Judge Calibration Closure（2026-09-06）

> RP1_BASE_SHA: `b9b766532` ｜ RP1_CODE_SHA=CALIBRATION_GATE_SHA: `1592b8d3a` ｜ HEAD/REMOTE: 见回执
> 任务书: docs/tasks/PHIAGENT_O7A_RP1_JUDGE_CALIBRATION_CLOSURE_TASK.md（原样落盘）
> 原始历史保留: 上文 §0 的 O7_A = BLOCKED（recall 88.9% / applicability 整向量 77.8%）不改写。

## RP1-1. Reviewer 对两个 patch 提议的裁决（接受）

1. **C6-L1-bad 冻结不改**（kill case）——"修辞性来源声明不扩大实际证据访问权限"正是核心合同;
   把句子改简单=降低考试难度, 不是修仪器。原文+sha256 已由测试 R1 冻结
   （65cd5c06f83f25d7a37de378a28731c24ffbc00141f850acc74b923409d5ea0b）。
   PRE_PATCH: F6 expected=true, judge=false（第3轮双轮一致漏）。
2. **Applicability 口径改逐维**: PRIMARY=PER_DIMENSION_APPLICABILITY_EXACT_AGREEMENT,
   SECONDARY HARD=REQUIRED↔N/A critical contradictions=0, WHOLE_VECTOR 仅诊断。

## RP1-2. 旧数据按新口径重算（§7, prompt 改动之前）

```
PER_DIMENSION = 122/135 = 90.4%（≥90% ✓）
REQUIRED_NA_CRITICAL_CONTRADICTIONS = 0 ✓
→ APPLICABILITY_PROMPT_CHANGED = false（judge 的 applicability 指令一字未动）
```

## RP1-3. F6 根因与一般性修复（§3, 非 fixture 专属）

根因: judge 把「根据记录」读作诚实引用, 未意识到 METADATA_ONLY 记录在信息上不可能包含
章节级内容。修复 = 一般访问上限规则（§3 任务书原文）: METADATA_ONLY 只支持记录中实际存在的
书目/存在性事实; ABSTRACT_AVAILABLE 只支持摘要+元数据可支撑的主张; FULL_TEXT_AVAILABLE≠已读;
FULL_TEXT_READ 才允许基于全文的主张; 修辞性来源声明不提高访问级别。
静态扫描（R14）: judge 宪法无任何 fixture id/「根据记录」专项规则/「第二节」等句子模式词。

## RP1-4. Metamorphic Fixtures（§4, 5 个, 全部换学者/论文/主题以证明原则迁移）

F6-M1（Kant 论文, METADATA_ONLY+章节主张→F6）｜ F6-M2（Aristotle 论文, 带 hedge→F6）｜
F6-M3（Aquinas, ABSTRACT_AVAILABLE+如实转述→不得触发）｜ F6-M4（Zhuangzi, FULL_TEXT_AVAILABLE
≠READ+章节主张→F6）｜ F6-M5（同 M4 论文, FULL_TEXT_READ+所给全文支撑→不得触发）。

## RP1-5. Final Calibration（两轮独立, 同一冻结 evaluator tree 1592b8d3a, judge=glm-4-plus t=0.0）

| 指标 | run0 | run1 | RP1 门 | 判定 |
|---|---|---|---|---|
| GOOD>MID>BAD | 2.597/1.781/0.958 ✓ | 同序 ✓ | ✓ | PASS |
| EXPECTED_FATAL_RECALL | 10/12=83.3% | 10/12=83.3% | 100% | **FAIL** |
| F1/F2/F4/F6_RECALL | 1.0/1.0/1.0/**1.0** | 1.0/1.0/1.0/0.8 | 各 100% | F6 run0 ✓ |
| F5_RECALL | 0.5 | 0.5 | 100% | **FAIL**（C2-bad 两轮一致漏） |
| F3_RECALL | 0.0 | 1.0 | 100% | **FAIL**（跨轮翻转） |
| FALSE_FATAL_ASSERTIONS（负样本池=21） | 0 | 0 | 0 | PASS |
| FATAL_FLAG_AGREEMENT | — | 90.6% | 100% | **FAIL** |
| DIMENSION_DIFF≤1 | — | 96.9% | ≥90% | PASS |
| PER_DIM_APPLICABILITY | — | 83.8% | ≥90% | **FAIL** |
| REQUIRED↔N/A contradictions | — | 0 | 0 | PASS |

## RP1-6. 残余失败形态诊断（关键事实: STABILITY≠VALIDITY）

第 3 轮校准曾给出 FATAL_FLAG_AGREEMENT=100% 而 RECALL=88.9%——**judge 稳定地犯同一个错**;
本轮（RP1）则反转: F6 全绿的同时 C2-bad(F5) 两轮一致漏（系统性盲点: judge 未把
"直觉是对象直接呈现于心灵的方式"识别为非证据措辞的逐字声称）, 而 C8-bad(F3)/F6-M4(F6)
跨轮翻转（端点侧采样波动, temperature=0 不保证确定性）。因此 evaluator constitution 增补:

```
STABILITY != VALIDITY
未来 Judge Gate 同时检查 correctness + repeatability
```

## RP1-7. 结论与 PATCH 提议

```
O7_A_RP1 = BLOCKED（F5_RECALL/F3_RECALL/FATAL_FLAG_AGREEMENT/PER_DIM_APPLICABILITY 未达 100%/100%/100%/90%）
PROPOSED_VERDICT = PATCH_REQUIRED
已达成: RP1 主目标（F6 via 一般规则, 变体证明原则迁移）; 负样本零误报; 生产边界全零;
        473 tests 全绿（含 R1-R15）; applicability prompt 未改。
残余失败模式: ①C2-bad F5 系统性漏（judge 对"声称逐字但措辞非证据"的判定边界）;
        ②F3/F6 单例跨轮翻转（长上下文 JSON 任务上 glm-4-plus temp=0 仍非确定）。
候选 PATCH（待 Reviewer 授权, 不自行执行）:
  a) k-of-3 self-consistency ensemble（同 fixture 3 次判定多数聚合——测量仪器设计, evaluation-only;
     可同时压 flag 翻转与 applicability 波动, 成本 ×3）;
  b) F5 的确定性预检（harness 侧对所给证据文本做机械子串比对, 作为 flag 的机械证伪源——
     与生产 quote_bound 同思想但仅存在于校准 harness）;
  c) 更换/增加 judge 模型（须 TESTED≠JUDGE 且重走 §10-§11 全部门）。
O7_B_AUTHORIZED = false
```
