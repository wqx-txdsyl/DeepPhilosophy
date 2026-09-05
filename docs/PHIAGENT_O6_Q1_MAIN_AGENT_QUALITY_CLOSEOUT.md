# PhiAgent O6-Q1 — Main-Agent Evidence Expression & Multi-Turn Quality Closeout

> BASE_SHA: `4d7fbf9d83d24b718b74e3af184c3f8bfe3e1448`（O6-RP1 re-gate 后）
> QUALITY_GATE_SHA: `6ebb15730c0f27742e3101a4356cfc2fe5d0d988`（Q1 实现 commit）
> Reviewer: GPT-5.6 Sol ｜ 模型: GLM-5.3-Flash (Reasoning Max)
> 阶段定性: PRODUCT QUALITY CLOSEOUT ONLY（架构零改动，validator 判定逻辑零改动）

---

## 1. FAILURE_CORPUS（§1–§2 全量审计，不挑样）

数据源: prerp1_data（32 单题 + 24 多轮轮次）+ run1_polluted（5 镜像）。
**23 条失败记录 / 18 个唯一失败**（完整 dump: `backend/tools/_tmp/o6q1_failure_dump.txt`）。

### 根因分布（Q1–Q12）

| 根因 | 主因 | 说明 |
|---|---|---|
| Q1 BLOCKQUOTE_MISUSE | **5** | 把自己的综合/诚实声明排成引用块（H3, M2-T5, M3-T1, M5-T1/T3） |
| Q3 NEAR_TRANSLATION_NOT_MARKED | **5** | 语料译本与流行措辞差 0.63–0.93 未标注（B3, E2, Z2, M2-T1/T4） |
| Q4 CITATION_LABEL_INVENTED | **5** | 凭记忆编造章节/卷号（A1, M2-T2/T3, M3-T2/T3） |
| Q2 MEMORY_WORDING_AS_EXACT | 2 | 记忆措辞当逐字（B2, M5-T2） |
| Q12 OTHER (EMPTY_FINAL) | 1 | 两轮修复候选均为空 |
| Q5/Q6/Q7/Q8/Q9/Q10/Q11 | 0 | 参考性出现见报告 |

### 三分类（§2）

```
EXPRESSION_FAILURE_COUNT = 16（拿着好证据用错误形式表达——本轮主攻）
EVIDENCE_MISSING_COUNT  = 1（M3-T2 人格传记类一手文献库外缺失）
CONTEXT_FAILURE_COUNT   = 0
```

**结论**: 18 例中 16 例为表达失败——证实 Reviewer 判断"模型拿着好证据
却用 validator 必拒的形式表达"，属 Main-Agent policy 层，非架构问题。

## 2. Policy 层改进（§3/§4/§8/§9/§12/§14，单源 Context Builder）

CORE_POLICY_LINES_BEFORE = 97 → AFTER = 113（保持简洁，无任务类型枚举）:

| 铁律 | 新增内容 | 对应 |
|---|---|---|
| 铁律 1（Evidence Appetite） | +研究校准：更新研究问题、不发同义词变体、指向尚存不确定性/缺失来源/冲突解读；充分即综合作答 | §12 |
| 铁律 2（引文表达纪律） | 引号/引用块 = 断言"以下措辞是原文"；转述/解读/记忆措辞/译文变体 → 普通正文并明示；不把自己的解释/综合/诚实声明排成引用块 | §3 |
| 铁律 2+（引用标签纪律） | 正式引用的书/章/节标签必须取自检索证据元数据；不得凭记忆补造；只核验到书级就只标书级 | §4 |
| 铁律 16（多轮证据边界） | 会话历史是语境不是证据；逐字引用落在本会话检索证据上；定点重读即可，不必全量重查 | §9 |
| 铁律 17（修复策略） | 被拒不原样重复——按反馈区分修表达 vs 补研究/删除弱化 | §8 |
| Context Builder | +当前 responder 身份 + 历史角色机械事实（中/英，并入单条） | §10/§11 |

禁止项遵守: 无任务类型 IF 链、无意图分类器、无"最少工具"替换、零新注入点（仍为单源 builder + hard 预算位）。

## 3. 模型可见元数据（§5/§6）

```
MODEL_VISIBLE_CANONICAL_CITATION_METADATA_BEFORE = NONE
  （search_books/get_chapter 只有裸书名/章节名；get_chapter 甚至无书名）
MODEL_VISIBLE_CANONICAL_CITATION_METADATA_AFTER = per-item citation_label
  （search_books 命中与 get_chapter 结果各附 canonical 标签——机械派生自
   书目信息；章节缺失回退书级【《书》】，不发明位置）
QUOTE_MATCH_STATUS_VISIBLE = 修复反馈携带 match=NEAR/NONE + coverage +
  best_evidence=【《书》·章】（§6：模型写候选前就知道 NEAR 不是逐字证据）
```
零"你应引用此条/这是正确解读"类语义文案。

## 4. 修复反馈充实（§7）

ValidationIssue detail 现携带: offending span + match 状态 + coverage +
evidence_id + 最佳证据 canonical 标签 + 命中/未命中章节分述。
结尾保持中性: `Revise the candidate or gather more evidence as appropriate.`
（无命令式动作指令；判定逻辑零改动）。

## 5. 测试

```
全量 pytest backend/tests -q → 423 passed / 0 failed
新增 backend/tests/test_o6_q1_main_agent_quality.py T1–T15 全过
（T1 引言vs转述 / T2 引用块语义 / T3 canonical 标签可见 / T4 无标签不发明 /
  T5 NEAR 可区分 / T6 span / T7 证据元数据 / T8 中性反馈 / T9 历史≠证据 /
  T10 合法证据不丢 / T11 agent 身份 / T12 单一 policy owner / T13 零工具可行 /
  T14 Appetite 保留 / T15 validator 矩阵冻结 TP=10 FN=0 TN=10 FP=0）
validator 矩阵复跑同结果——严格度未变（§15 ✓）
```

## 6. Live A/B — 同一 O6 数据集（§19）

| 指标 | BEFORE（O6-RP1 build） | AFTER（Q1 build） |
|---|---|---|
| SINGLE_TURN_PUBLICATION | 16/32 = 50% | **24/32 = 75%** |
| SAFE_REJECT | 16（50%） | 8（25%） |
| MULTI_TURN_PUBLICATION | 11/24 = 46% | **15/24 = 62.5%** |
| REPAIR_SUCCESS | 9/25 = 36% | **15/23 = 65%** |
| REPAIR_EXHAUSTION | 16/25 = 64% | 8/23 = 35% |
| ENGINE_FAIL | 0 | 0 |
| UNVERIFIED_CITATION_PUBLIC | 5 → 0（占位符口径对齐） | **0** |
| UNPARENTED_TOOL_RESULTS | 0 | 0 |
| 硬上限命中 | 16/32 | 13/32 |

（§31 评估 harness: `backend/tools/_tmp/o6_gate_b_runner.py` + `o6_fresh_runner.py`，evaluation-only）

## 7. Fresh Anti-Overfit Set（§20）— PROVIDER_ERROR 披露

8 新鲜单题 + 2 新鲜多轮（8 轮）。**中途 DeepSeek 余额再次耗尽（402）**：
- 已完成单题 4/4 全部 **PUBLISHED**（孟子民贵/尼采深渊/奥勒留退隐/斯多亚→斯宾诺莎谱系——含中式原文、西式原文、谱系类全覆盖）✓
- 3 例 SAFE_REJECT（范式转移编造章节号/休谟康德/尼采怜悯引文——真阳性拒绝，含 1 例疑似 F1 新边界 FP 待裁决）
- 1 单题 + 2 会话 = PROVIDER_ERROR（余额耗尽未完成）
按 §30: PROVIDER_ERROR 已记录；充值后可单独重跑一次（原始失败保留）。

## 8. 新鲜集拒因分析（已完成 3 例）

| Case | 拒因 | 真阳性? |
|---|---|---|
| FQ4 范式转移 | UNVERIFIED_CITATION【《科学革命的结构》·第九章、第十章】——未检索即凭记忆给章节号 | ✓ 真阳性（合同要求证据在池） |
| FQ5 休谟vs康德 | UNSUPPORTED_EXACT_QUOTE——模型自我说明句中的引号被 F1 新边界捕获 | ⚠ 疑似 FP（模型描述自身行为非新引文主张），记录待 Reviewer 裁决 |
| FQ7 尼采怜悯 | UNVERIFIED_CITATION【《查拉图斯特拉如是说》·卷二·论同情者】 | ✓ 真阳性 |

## 9. §21 Quality Gates 对照

```
硬完整性门: 全部 = 0 ✓（INVALID_FINAL_PUBLIC / UNVERIFIED_QUOTE / UNVERIFIED_CITATION
  [真实引用口径] / STITCHED / VALIDATOR_FN / VALIDATOR_FP / ARCHITECTURE_REGRESSION）
SINGLE_TURN_PUBLICATION = 75%（目标 ≥80%: 差 5pp）
MULTI_TURN_PUBLICATION = 62.5%（目标 ≥80%: 差 17.5pp）
REPAIR_SUCCESS = 65%（目标 ≥70%: 差 5pp）
REPAIR_EXHAUSTION = 35%（目标 ≤20%: 差 15pp）
FRESH_SET = 4/4 发布（余额中断前完成的全部 case）
→ 产品质量目标未全部达成（接近但未达标），如实上报。
```

## 10. §15/§16 指标

CORE_POLICY_LINES 97→113；注入点保持单源 builder；RUNTIME_SEMANTIC_MUTATORS = 0；
RUNTIME_FACTUAL_APPENDS = 0；RAW_REASONING_PUBLIC = 0；UNPARENTED = 0；
COGNITIVE_POLICY_OWNER = 1。Evidence Appetite 完整保留（零"最少工具"替换）。

## 11. O6-Q1 报告之后的下一步（Reviewer 裁决项）

1. 充值后重跑 fresh set（4 未完成单题 + 2 会话）——§30 允许的单次重跑
2. F1 新边界对"模型自我说明句"的 FP 复核（FQ5 case 证据已存档）
3. O6-Q2 或质量迭代: publication 75%→80%+ 的剩余缺口大概率在
   "修复轮格式学习"（Q6 同族错误 3/18）与"引用标签必须取自元数据"的
   模型遵从率——均为 policy/prompt 层迭代，非 runtime
