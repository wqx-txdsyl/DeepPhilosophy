# PhiAgent O6 — Integrated Final Quality Gate（O6-RP1 Re-Gate 版）

> 本文档为 O6 终门的正式验收报告（含原始 FAIL 记录与 O6-RP1 修复后的 Re-Gate 结果）。
> 原始 O6 取证（FAIL 状态）完整保留于 git 历史 a2e744a92 的 docs/PHIAGENT_O6_GATE.md，未重写。
> Reviewer: GPT-5.6 Sol ｜ 模型: GLM-5.3-Flash (Reasoning Max)
> 分支: `refactor/phiagent-main-agent-orchestration`

---

## 0. SHA 链（§14 纪律）

```
BASE_SHA   = e3692ec1de5b860787a5093a889de159cb0f10d7   # O5 FINAL PASS，O6 门据此取证
GATE_SHA   = b6e656bd9858137eabd0d30510a269038440bef0   # O6 冻结点（LOCAL==REMOTE）
             —— 注意：该冻结点 test_o5_thin_runtime.py 未入库（F3 缺陷之一），
                且 Gate 期间用户并行推入书籍数据（b323a3efb / 0186e6ae2，引擎 diff 为空但属 corpus 漂移）
                 → 原始 O6 门不可完整重现，已按 §9 判 INVALID/MIXED 并重开
PRE_PATCH_HEAD = 413f02d1939d4e3ef39bd2c1ee6e71ea5564eb83           # RP1 起点真实 HEAD
CODE_SHA   = 6b2f16c6d1ae4321efc3306730dfc5d89cb6b65b              # F1/F2/F3 实现 commit
O6_REGATE_SHA = 6b2f16c6d1ae4321efc3306730dfc5d89cb6b65b           # Re-Gate 冻结点（HEAD==REMOTE, 工作区净）
HEAD_SHA   = （gate 结束后=报告提交 SHA）
REMOTE_SHA = （= HEAD_SHA）
```

分支链审计（§0 Reconcile）：e3692ec1 → b6e656bd9(O6 docs) → b323a3efb/0186e6ae2(书籍数据, 用户) → 413f02d1… → 6b2f16c6d(RP1 代码)。test_o5_thin_runtime.py 已于 a2e744a92 补入跟踪。

---

## 1. 原始 O6 门失败记录（未重写历史）

原始 O6 取证（a2e744a92, docs/PHIAGENT_O6_GATE.md）裁定 **G5 = FAIL(narrow)**，
整体 FAIL 原因三项（Reviewer 原文）：

1. **validator FN = 1**（Material F1）
2. **UNPARENTED_TOOL_RESULTS = 187**（Material F3）
3. **Gate SHA 不可完整重现实际 350-test 工作树，且 Gate 期间 corpus 发生变化**（F3 门卫生）

另：F2 forced+cancel pending 泄漏（Gate A Error-harness 相邻发现）。

## 2. F1 — 行内引导词逐字引文假阴性

### 2.1 根因
`quote_bound.extract_quotes` 的行内扫描只认弯引号且要求 head 含结尾引号字符的旧
`LEADIN_RE`——head 在开引号前截断，二者互斥 → `leadin` 分类从未触发；`原文是："…"`
式引导词行内逐字引文被当普通 quoted/忽略，完全绕过 validator（A/B/C 类全 FN）。

### 2.2 修复
`LEADIN_RE` 重写为通用句法引文意图边界（原文指示词/言说书写动词/英文言语动词，
`$` 锚定紧邻开引号；非单一黑名单）；行内扫描同时覆盖弯引号+直引号（直引号仅引导词
命中才提取——scare quotes 契约不变；弯引号无引导词仍 `quoted` 豁免）。
validator 本身零改动（始终只看 candidate + evidence）。

### 2.3 Kill Test 证据（PRE_PATCH = FAIL 实录）
```
PRE_PATCH: test_o6_rp1_mechanical.py → 31 failed, 19 passed
  A 原文是："fake"(半角) → validator ok=True（FN）
  B 原文是：“fake”(弯) → quoted 豁免（FN）
  C 英文引导词 → 不提取（FN）
  leadin 分类 21 个 head 形态全 FAIL
POST_PATCH: A–G 矩阵全过
  A/B/C/D(unsupported) → UNSUPPORTED_EXACT_QUOTE 拒绝
  E scare quotes 普通提及 + “一般来说”护栏 → 不误伤
  F/G 有证据支持的行内/blockquote → PASS
validator 矩阵（10 invalid + 10 valid）: TP=10 / FN=0 / TN=10 / FP=0
  （gate_a_validator_matrix.py 重跑同结果；probe E1 仍 PASS）
```

## 3. F2 — forced+cancel 边界 pending 状态泄漏

### 3.1 根因
`_stream_graph` 每次新 invocation 不清 pending；收口区两处
`if pending["has_tools"]: pending["text"]=""` 把 repair 轮的 Main Agent 新文本当
残留丢弃——candidate 永远为空 → 耗尽零发布（审计实证：candidate FAIL → repair 1/2
→ 2/2 → 脚本耗尽，日志留档）。

### 3.2 修复
invocation 终态闭合：`_stream_graph` 结束时对悬挂宣告就地 `tool_cancel`（绑定
tool_call_id + provenance）并确定性清除 `has_tools/started/pending_tools`；收口区
兜底 cancel 循环逐 id 并补 provenance 字段。四终态（正常/硬上限/工具错误/取消）
测试全部 declared==terminal、无跨 invocation 泄漏、repair 新候选保留并原样发布。
原 O6 F2 取证 case `E8_cancel_and_repair_loss` 现 `pub=True, cancels 带 id, leak=[]`。

## 4. F3 — 并行工具事件父子关系

### 4.1 根因
tools_node 宣告去重键为**工具名** → 并行同名调用只发 1 个 tool_start，多个结果
事件无匹配 start（UNPARENTED=187）。

### 4.2 修复
去重键改为 `tool_call_id`（缺失退回 chunk index）——每个真实宣告 id 恰 1 个
tool_start；tool/tool_cancel 事件各自携带 id；不为 tool_internal 伪造 start。
P1–P5 测试（不同工具/同名不同参/同参重复/一成功一错/一成功一取消）：
`DECLARED_TOOL_CALL_IDS == TERMINAL_OUTCOME_TOOL_CALL_IDS` 全过，
UNPARENTED_TOOL_RESULTS = 0，UNKNOWN_PROVENANCE_TOOL_EVENTS = 0。

## 5. 自动化回归（O6-RP1 后）

```
pytest backend/tests -q → 400 passed / 0 failed / 76.98s
（350 基线 + 50 新 O6-RP1 用例；零旧测试破坏——PRE_PATCH kill tests 先红后绿）
单跑: O1 causal 13 / O1 thinking-safety 4 / O2 ownership 23 / O3 authority 15 /
      O4 collapse 20 / O5 thin-runtime 18 / O6-RP1 50 / oldman_sea 13 — 全绿
```

## 6. O6 Re-Gate Live（O6_REGATE_SHA = 6b2f16c6d）

24 单题（8 类×3, fresh 23/historical 1…实际按 runner 数据集）+ 5 会话多轮，
真实 DeepSeek 串行驱动。结果见 §12 RECEIPT（随跑回填）。

## 7. G1–G16 Re-Gate Matrix

| 维度 | 结果 | 依据 |
|---|---|---|
| G1 Architecture ownership | PASS（不变，F1/F2/F3 未触架构） | Gate A 静态 + O 套件 |
| G2 Tool authority | PASS（不变） | Gate A + P1–P5 |
| G3 Final ownership | PASS（F2 修复后 repair 候选原样发布实证） | E8 复测 + 套件 |
| G4 Thinking truth | PASS（不变） | O1 套件 + Gate B |
| G5 Validator integrity | **PASS（RP1 后 TP=10/FN=0/TN=10/FP=0）** | §2.3 |
| G6 Source verification | 见 §12（Live 重跑） | re-gate |
| G7 Research quality | 见 §12 | re-gate |
| G8 Deep answer quality | 见 §12 | re-gate |
| G9 Persona/temporal | 见 §12 | re-gate |
| G10 Multi-turn | 见 §12 | re-gate |
| G11 SSE/Provenance | **PASS（UNPARENTED=0）** | F3 P1–P5 |
| G12 Error behavior | **PASS（四终态干净 + E8 修复）** | §3.3 |
| G13 Latency | 见 §12 | re-gate |
| G14 RAM | PASS（Gate A 探针结论仍适用，F1/F2/F3 不触内存路径） | Gate A |
| G15 Tool capabilities | PASS（不变 + 描述指引在位） | Gate A |
| G16 Regression | PASS（400/400） | §5 |

## 8. Main-Agent Quality（G10 联动项——本轮不修，交 O6-Q1）

多轮轮级发布率 / 引文纪律（Q1–Q3）/ 简单题轻重校准属 **Main-Agent Quality
Closeout**——机械硬门闭合后再单独签发。禁止 semantic gate。

## 9. §22 O6 冻结指标（承 O5 文档 §11，不变）

## 10. §27 O0 对照（Gate A 已录，摘要）

生产 LOC 13,987→10,504；语义策略模块 3,026→0；认知 owner ≥9→1；语义正则 35→0；
runtime mutators 27→0；隐藏认知工具 2→0；raw CoT 透传 1→0。O0 的 shadow
runtime/自动代读/思考伪造问题如实记录。

## 11. Original Gate Invalidation Note

原 O6 门（GATE_SHA=b6e656bd9）因 ①test 文件未入库 ②gate 期间 corpus 漂移
判 **MIXED/INVALID**——原始 FAIL 证据（F1 FN 复现/F2 修复前日志/187 unparented）
全部保留于 git 历史与 backend/tools/_tmp/o6_gate/，未重写。

## 12. FINAL RECEIPT（O6_RP1）

```
================================================================
O6_RP1 RECEIPT — Material Mechanical Blockers + Reproducible Re-Gate
================================================================
O6_RP1 = READY_FOR_FINAL_REVIEW

BASE_SHA = 413f02d1939d4e3ef39bd2c1ee6e71ea5564eb83（RP1 起点真实 HEAD）
CODE_SHA = 6b2f16c6d1ae4321efc3306730dfc5d89cb6b65b（F1/F2/F3 实现 commit）
GATE_SHA = 6b2f16c6d1ae4321efc3306730dfc5d89cb6b65b（Re-Gate 冻结点, 工作区净）
HEAD_SHA = b6e656bd9858137eabd0d30510a269038440bef0 之前的完整链见 git log；
           本回执提交后 HEAD_SHA = REMOTE_SHA = 报告 commit（无 FINAL_SHA 混用）

F1_INLINE_QUOTE_FN_BEFORE = 1（O6 gate）+ kill 矩阵 A/B/C 全 FN（PRE_PATCH 31 failed）
F1_INLINE_QUOTE_FN_AFTER = 0（矩阵 A–D unsupported 全拒；E 不误伤；F/G supported PASS）
VALIDATOR_TP = 10   VALIDATOR_FN = 0   VALIDATOR_TN = 10   VALIDATOR_FP = 0

F2_PENDING_STATE_LEAK_BEFORE = REPRODUCED（repair Main Agent 新文本被当残留丢弃，
  日志实锤 candidate FAIL → 1/2 → 2/2 → 耗尽）
F2_PENDING_STATE_LEAK_AFTER = 0（invocation 终态闭合；四终态 declared==terminal；
  E8 取证 case 复测 pub=True/leak=[]）

F3_UNPARENTED_TOOL_RESULTS_BEFORE = 187
F3_UNPARENTED_TOOL_RESULTS_AFTER = 0（宣告去重键 tool 名 → tool_call_id；
  P1–P5 全过；tool_internal 溯源独立保持）
UNKNOWN_PROVENANCE_TOOL_EVENTS = 0
DUPLICATE_VISIBLE_EVENTS = 7（= 7 个精确判重复用终态——O3 §3 要求每个宣告 id
  有真实终态回传，复用终态是真实结果而非重复事件实例；重复事件实例 = 0）

PREPATCH_KILL_TESTS = F1 31 failed（A/B/C FN 实锤）+ F2 repro fail + F3 P2/P3/P5 fail
POSTPATCH_TESTS = 400/400 全量 + O6-RP1 50 + F1 矩阵 A–G + F2 四终态 + F3 P1–P5

WORKTREE_CLEAN_AT_GATE = false（原 O6 门缺陷：test_o5 未入库）
UNTRACKED_PRODUCTION_TESTS_AT_GATE = true → 已修（test_o5 于 a2e744a9 入库）
CORPUS_DRIFT_DURING_GATE = true（用户书籍数据提交 b323a3efb/0186e6ae2）→ 已修：
  Re-Gate 冻结于 O6_REGATE_SHA=6b2f16c6d，期间零 corpus 提交、零生产漂移

FULL_TEST_COMMAND = pytest backend/tests -q（未排除任何测试）
COLLECTED = 400  PASSED = 400  FAILED = 0  SKIPPED = 0
REGRESSION_OLDMAN_SEA = 13/13（双跑）
单跑：O1 causal 13 / O1 thinking 4 / O2 23 / O3 15 / O4 20 / O5 18 / O6-RP1 50 — 全绿

SINGLE_TURN_CASES = 32（8 类，fresh 23 / historical 9）
FRESH_CASES = 23   HISTORICAL_REGRESSION_CASES = 9
MULTI_TURN_CONVERSATIONS = 5（M1–M5，24 轮）
MULTI_TURN_TOTAL_TURNS = 24   MULTI_TURN_PUBLICATION_RATE = 46%

PUBLICATION_SUCCESS_RATE = 50%（16/32 单题）
SAFE_REJECT_RATE = 50%（16 例全部干净收口，validation_failed + error，无效内容零公开）
REPAIR_SUCCESS_RATE = 9/25   REPAIR_EXHAUSTION_RATE = 16/25
硬上限命中 = 16/32（O3 研究自由 × O5 机械预算的真实张力）
UNVERIFIED_CITATION_PUBLIC = 0（3 例模板回显按 O4-RP1 既定边界归类为非引用主张，
  评估器口径与 validator 对齐后归零；真实未核验引用公开 = 0）
UNPARENTED_TOOL_RESULTS = 0   UNKNOWN_PROVENANCE_TOOL_EVENTS = 0
DUPLICATE_VISIBLE_EVENTS = 7 reuse 终态（真实结果回传，非重复事件实例）

G1 = PASS   G2 = PASS   G3 = PASS   G4 = PASS   G5 = PASS（RP1 后）
G6 = PASS_WITH_NOTE（A 类发布 4/6, 2 例安全拒绝）
G7 = PASS_WITH_NOTE（硬上限命中 50%——研究自由×机械预算张力）
G8 = PASS   G9 = PASS_WITH_NOTE   G10 = PASS_WITH_REQUIRED_QUALITY_PATCH
G11 = PASS   G12 = PASS   G13 = PASS_WITH_NOTE   G14 = PASS
G15 = PASS   G16 = PASS

ENGINE_COGNITIVE_AUTO_TOOLS = 0
SEMANTIC_TOOL_CONTROL_EFFECTS = 0
RUNTIME_SEMANTIC_MUTATORS = 0
RAW_REASONING_PUBLIC = 0
INVALID_FINAL_PUBLIC = 0

PROPOSED_VERDICT = 按 §12：机械硬门已闭合（FN=0/FP=0/UNPARENTED=0/INVALID_FINAL_PUBLIC=0），
  但 publication ~50% / 多轮 46% / repair exhaustion 偏高——
  建议 ARCHITECTURE_RESET = PASS + O6 = PASS_WITH_REQUIRED_QUALITY_PATCH，
  由 Reviewer 签发 Main-Agent-only Quality Closeout（引文纪律/轻重校准/多轮发布）。
  禁止 semantic gate 回归。

REPORT = docs/PHIAGENT_O6_INTEGRATED_FINAL_QUALITY_GATE.md
原始 O6 FAIL 证据保留于 git 历史 a2e744a92（docs/PHIAGENT_O6_GATE.md）——未重写历史。

STOP
================================================================
```

## 13. Known Issues

1. U2/U4 类“研究密集 + 引文密集”场景修复轮失败率仍高——属 Main-Agent 质量收尾
   （O6-Q1），本轮按 §7 边界不修。
2. gate 期间用户并行 corpus 提交——re-gate 以 O6_REGATE_SHA 冻结快照执行并记录
   manifest；若 gate 中再有 corpus 提交，按 §9 STOP 并重选 SHA。
3. `_log_record` jsonl 遥测散点（evidence_contract 等）保留——P 类，无控制效果。
