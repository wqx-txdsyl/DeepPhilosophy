# PhiAgent O6-Q2 — Final Product Quality Closeout

> BASE_SHA: `943516d2e`（O6-Q1 报告 commit = Q2 代码基）
> CODE_SHA / QUALITY_GATE_SHA: `75974e364`（Q2 实现 commit，已 push；工作树 gate 期间无生产改动）
> HEAD_SHA = REMOTE_SHA = 本报告所在 commit（值见最终回执）
> Reviewer: GPT-5.6 Sol ｜ Live 模型: DeepSeek `deepseek-chat` @ api.deepseek.com（与 Q1 同集逐字节同配置，§22 零替换）
> 阶段定性: PRODUCT QUALITY CLOSEOUT ONLY（validator/quote_bound 零生产改动，T16 内容冻结断言通过）

---

## 0. 执行说明（与本任务书流程的偏差披露）

- Q2 原由子代理执行，**该代理在运行 20.7 分钟后因模型服务方配额错误 [1310]（限额 2026-09-09 重置）终止**；
  其遗留工作区改动经主线程复核后：`engine_langgraph.py` 铁律 17 重写**保留**（符合 §4），
  `final_validator.py` 改动**回退**（§18 validator 冻结 + T16；span 类型已由 issue code+message+locator
  机械区分，无需改 validator）。此后 Q2 全部工作由主线程直接执行。
- 用户 DeepSeek key 于 Q2 执行前验证可用（HTTP 200），同集/fresh 两轮 gate 使用同一 provider 连续完成。

## 1. FQ5 裁决（§1）

```
FQ5_IS_TRUE_FALSE_POSITIVE = false（TRUE POSITIVE，非 validator FP）
USER_REQUEST = 休谟 vs 康德「因果必然性」比较（Q1 fresh FQ5）
MAIN_AGENT_CANDIDATE = 在比较性说明中把"对自身表述的元说明"写成了带引号句子/引用块
OFFENDING_SPAN = 元说明句本身（"模型描述自身行为"的措辞被排成引用形态）
QUOTE_EXTRACTOR_CLASSIFICATION = blockquote/引号 → "以下措辞是原文"断言
VALIDATION_CODE = UNSUPPORTED_EXACT_QUOTE（match=NONE）
BEST_EVIDENCE = 无（该句本就不是检索来源措辞）
WHY_VALIDATOR_REJECTED = 句法上确实把非证据措辞呈现为 source-wording 断言——
  即使模型主观意图是元说明，Q1 同族判例（9 例多轮失败中 5 例同形态）与
  确定性解析器的行为一致且正确。
```
→ 不 STOP，按 policy 路径收敛（铁律 17「修复说明写成普通正文」+ 铁律 2「自己的解释/诚实声明
不进引用块」）。FQ5 原样保留在 Q2 观察（Q2 同集语料中该家族再出现于 F2 一处，见 §6）。

## 2. Q1 剩余失败语料冻结与 R 分类（§2，before-patch）

8 same-set 单轮 SAFE_REJECT（Q1 after 数据集）: A1 B2 B3 C1 D3 E2 H4 R4
9 多轮未发布轮次: M1-T1 M2-T2 M2-T3 M2-T5 M3-T1 M4-T2 M5-T2 M5-T3 M5-T4

每例带 FIRST_CODES / REPAIR_CODES / EVIDENCE_AVAILABLE / CITATION_METADATA / MATCH_METADATA /
FAILURE_CHANGED / SAME_ERROR_REPEATED 七字段审计（数据源: Q1 snapshot 逐 case trace），主因归类:

| 根因 | 计数（17 例） | 说明 |
|---|---|---|
| R1 final-draft quotation discipline | **5** | 元评论/修复说明被排成引用块或加引号（B3, D3, M1-T1, M2-T5, M4-T2）|
| R2 citation precision discipline | **4** | 标签超出现有元数据/凭记忆补章号（E2"费希特相关章节", H4"第125节", M2-T2, M5-T4）|
| R3 NEAR→exact confusion | **6** | 译文近似措辞静默升格逐字（B2, C1, R4, M3-T1, M5-T2, M5-T3×5）|
| R5 repair creates new span | **2** | 修复引入新失范（A1"说明"引用块, M2-T3 承诺句加引号）|
| R4/R6/R7/R8/R9/R10/R11 | 0 | 非主因（churn 加剧出现在失败轮：12–27 工具，属 R10 次要征兆）|

三分类: EXPRESSION = 16 / EVIDENCE_MISSING = 0 / CONTEXT = 0（多轮证据**轮内重读可达**，见 §5）。

## 3. Q2 Policy 改动（§4/§5/§6/§13，唯一生产 diff = SYSTEM_PROMPT_LG）

CORE_POLICY_LINES: 113 → **119**（≤120 ✓；POLICY_RULES_DEDUPED = 铁律 17 重写合并旧 17+§5 保留语义，
铁律 2 自检行合并 §6+§8，铁律 1 校准行合并 §13——零新增任务类型枚举、零 IF 链）。

| 铁律 | Q1 → Q2 | 对应 |
|---|---|---|
| 17 修复策略 | "不原样重复；按反馈修表达/补研究" → **修复合同**: 逐条读机械反馈定位每个被打回 span；已成立部分保持不动；只修失败处；重要且证据可补才研究；提交前自查 span 全消除；**修复说明写成普通正文** | §4/§5/§9 |
| 2 引文纪律 | + **落笔前自检**: 每处引号/引用块/正式标注须有本会话证据支撑；精确引文非必要宁用准确散文，不补造引证精度 | §6/§8 |
| 1 研究校准 | + 不依赖逐字核验且已有知识可可靠作答时即综合作答，不为显得充分而持续加检 | §13 |

无 Python 化语义动作（`if issue == NEAR: rewrite_quote()` 类不存在）；Runtime 语义 gate 零新增。

## 4. 模型可见元数据审计（§7/§8/§9——audit 结论: 零代码改动）

- 命名一致性: search_books / get_chapter 每命中项统一 `citation_label`（Q1 已闭环），get_chapter 带
  `book_title`；无 chapter_name/canonical_chapter/label 混名问题。
- citation_granularity: 由 citation_label 形态机械可见（含"·章"=章级；无"·"=书级）；不新增长字段。
- 修复反馈字段（Q1 冻结集原样）: issue code / locator(=候选内片段) / match=NEAR|NONE / coverage /
  evidence_id / best_evidence=【《书》·章】；UNVERIFIED_CITATION 另列同书已检索章节名。
- 零发明: `_cite_label` 无章回退书级、空书名返回空串；检索层无节/格言号合成路径（T4 通过）。
- 结论: 元数据层 Q2 缺的不是信息而是**收敛使用**——policy 已补（§3）。

## 5. 多轮证据持久化审计（§10/§11——结论: 不实现 carry-forward）

Q1 snapshot 24 轮逐轮 tool 序列审计: 24/24 轮证据按需**轮内重读**（失败轮均 ≥5 次
get_chapter/get_book_detail）；分类 = REHYDRATED（定点重读）/ NOT_RELEVANT（解释轮）；**LOST = 0**。
stream_agent 无 evidence 参数（T10 断言锁定无跨调用证据合并）→ §11 ConversationEvidenceContext
**不实现**（无真实丢失；避免新增治理子系统）。HISTORY_IS_NOT_EVIDENCE 与 AGENT_SWITCH_ISOLATION
保持（T9/T11 测试通过）。

## 6. Same-Set Live A/B（§24/§25，单次不挑样，同一 O6 数据集: 32 单轮 + 5 会话 24 轮）

| 指标 | Q1 after (943516d2e) | **Q2 (75974e364)** | 目标 | 判定 |
|---|---|---|---|---|
| SAME_SET_SINGLE | 24/32 = 75% | **22/32 = 68.75%** | ≥26/32 | ✗ |
| SAFE_REJECT（单轮） | 8 | 10 | — | — |
| SAME_SET_MULTI | 15/24 = 62.5% | **19/24 = 79.2%** | ≥20/24 | ✗（差 1 轮）|
| REPAIR_SUCCESS（单轮口径） | 15/23 = 65.2% | **15/25 = 60.0%** | ≥70% | ✗ |
| REPAIR_EXHAUSTION（单轮口径） | 8/23 = 34.8% | **10/25 = 40.0%** | ≤20% | ✗ |
| REPAIR_SUCCESS（单+多轮合并） | 24/41 = 58.5% | **29/44 = 65.9%** | 参考 | ↑ |
| REPAIR_EXHAUSTION（合并） | 17/41 = 41.5% | **15/44 = 34.1%** | 参考 | ↑ |
| FIRST_PASS_PUBLICATION（单轮零修复即发布） | — | 7 | 参考 | — |
| ENGINE_FAIL | 0 | 0 | 0 | ✓ |

分会话: M1 3/5（Q1 4/5）｜ **M2 5/5（Q1 2/5）** ｜ M3 4/5（Q1 4/5）｜ **M4 4/4（Q1 3/4）** ｜ M5 3/5（Q1 2/5）

逐 case 变化: 固化 4（D3, E2, R4, B2 → PUBLISHED）；新增 6（A3, F2, F3, G1, G3, R1 → SAFE_REJECT）；
持续失败 4（A1, B3, C1, H4）。多轮: M2-T2/T3/T5、M3-T1、M4-T2、M5-T2/T4 全部转 PUBLISHED；
新失败 M1-T1/T2、M3-T4、M5-T1/T3。

### Q2 失败画像（10 单轮 + 5 多轮，verbatim codes 已存档）

| 族 | 计数 | 案例 |
|---|---|---|
| R3 NEAR→exact（译文近似当逐字） | **7** | A3(道德经开篇), F2(尼采文集·125 ×4), F3(庄周梦蝶), G1(康德·导言 ×3), R1(论语·先进 0.9 覆盖标点级), M5-T3 ×2 |
| R1 元评论进引用块/引号 | **3** | F2("一处顺带的事实（检索交叉印证…）"成引用块), B3, M1-T1/T2 |
| R2 标签超元数据/占位符 | **3** | **G3【《精神现象学》·章节】字面占位标签**, M3-T4, M5-T1 ×3 |
| R5 修复制造新 span | 1 | M1-T2 |
| 持续失败（Q1 同在） | 4 | A1, B3, C1, H4 |

**根因解读（如实）**: ①R3 已超过 R1 成为第一失败族——policy 对"近似措辞必须降级为转述或明示"的
遵从率未提升，且 0.9x 覆盖的标点级偏差（R1 论语 case）说明模型仍未"从检索结果逐字复制"；②G3 的
字面占位标签【…·章节】是**新退化形态**：模型为满足"标签取自元数据"纪律而填充了占位词——纪律的
字面遵从压倒了语义；③修复收敛方向多轮明显改善（M2 全绿、合并修复成功 58.5%→65.9%），单轮
first-pass 却更不稳——**修复合同改善了"被打回后的行为"，但 first-draft 引文表达纪律仍是短板**。

## 7. Fresh Anti-Overfit Gate（§26）

状态: 运行中（8 新鲜单题 Q2F1–Q2F8 + 2 会话 Q2M1/Q2M2 ×4 轮 = 16 答案轮；与 O6 数据集/Q1 fresh/
prompt 示例/单测零重叠；id 前缀 Q2F/Q2M）。结果落地后填写:

```
FRESH_TOTAL_TURNS = 16
FRESH_PUBLISHED = 13
FRESH_PUBLICATION_RATE = 81.25%（目标 ≥75% ✓）
PROVIDER_ERROR = 无（整轮零基础设施中断）

逐 case: 单轮 Q2F1 拒（NEAR·庄子濠梁译文近似当逐字）/ Q2F2-F3 发布（修复后收敛）/
Q2F4 拒（UNSUPPORTED_EXACT_QUOTE ×2·奥卡姆剃刀记忆措辞）/ Q2F5-F8 发布（其中 F5/F7 单次修复即收敛）；
会话 Q2M1 3/4（T1 UNVERIFIED_CITATION·eudaimonia 标签超元数据）/ Q2M2 4/4 全绿
（nietzsche→general 切换 + 续谈，T11/T9 行为实测通过）。
fresh 修复: 单轮 attempted 8 / success 6 / exhausted 2（25%）。
要点: 81.25% 的 fresh 发布率高于同集（68.75%）——policy 改动无过拟合迹象;
两例拒绝均为真阳性（记忆措辞/译文近似），零完整性违规。
```

## 8. 质量完整性与机械指标（§28/§29/§30/§31）

```
VALIDATOR_TP=10 FN=0 TN=10 FP=0（T16 矩阵复跑 + final_validator/quote_bound 对 943516d2e 零 diff）
UNVERIFIED_QUOTE_PUBLIC_RATE = 0 ｜ UNVERIFIED_CITATION_PUBLIC_RATE = 0
STITCHED_QUOTE_PUBLIC_RATE = 0 ｜ INVALID_FINAL_PUBLIC = 0
quote_bound(发布答案聚合): Q1 18 引用(17 exact/1 memory) → Q2 11 引用(10 exact/1 near/0 memory)
UNPARENTED_TOOL_RESULTS = 0 ｜ RUNTIME_THINKING_EVENTS = 0 ｜ OWNERSHIP_FINGERPRINT = 0 case
UNKNOWN_EVENT_TYPES = 0 ｜ ARCHITECTURE_REGRESSION = 0（T15 单一 owner 通过）
AVG_TOOLS 16.53→16.16 ｜ MEDIAN 20→18 ｜ P95 26→25 ｜ SEARCH_CALLS 276→248 ｜ READ 218→237
HARD_CEILING_HITS 13→11/32 ｜ ZERO_TOOL_CASES 1（且发布）｜ DUPLICATE_VISIBLE 10→7
DURATION P50 104.6→122.0s ｜ P95 211.6→173.2s
SEARCH_CHURN_CASE_RATE = 0（同义词变体连发 0 case，§14 保持）
```

## 9. 测试与回归（§32）

```
FULL: pytest backend/tests -q → 443 passed / 0 failed（基线 423 + Q2 新增 20）
O6-Q2 新增 backend/tests/test_o6_q2_quality_closeout.py T1–T16 全绿
  （T1 反馈全定位 / T2 粒度可区分 / T3 NEAR≠EXACT / T4 零发明 / T5 反馈中性 / T6 修复合同 /
    T7 保留有效内容 / T8 落笔前自检 / T9 历史≠证据 / T10 定点重读+无跨调用合并 / T11 切换隔离 /
    T12 简单题不强制研究 / T13 Appetite 保留 / T14 非运行时清单 / T15 单一 owner / T16 冻结）
O1 causal / O1 thinking safety / O2 ownership / O3 authority / O4 collapse / O5 thin runtime /
O6-RP1 mechanical / O6-Q1 均含于 443 全绿；regression_oldman_sea 含于全量。
```

## 10. 结论与判定提议（§33）

产品门 4 项全部未达（single 68.75%<80、multi 79.2%<80（差 1 轮）、repair 60%<70、exhaustion 40%>20），
但: 完整性硬门全零、架构零回归、validator 冻结、多轮 62.5%→79.2% 显著改善、合并修复收敛
58.5%→65.9%、多轮 3/5 会话创 Q1 以来最好成绩。

```
PROPOSED_VERDICT = NOT_READY（按 §33 如实上报；不自动开始 Q3——Q2 之后走向由 Reviewer 裁定，
  包括: 是否将剩余缺口转入 O7 学术性主轴的 first-draft 引文表达纪律（R3 族）治理，
  或再迭代一轮 Q2 级 policy 收敛）
LIMITING_FACTOR_CANDIDATE = first-draft 引文表达纪律（R3 NEAR→exact 已取代 R1 成第一失败族）
```

---
## 10. O7 方向共识纪要（与 Reviewer 三轮设计基调讨论）

> DESIGN CONSENSUS ONLY ｜ NO O7 IMPLEMENTATION ｜ NO PRODUCTION CHANGE ｜ NO GATE EFFECT

定位: O7 = Scholarly Research Agent（哲学研究型 Agent——研究对象是原典/论证/解释史/学术争议;
默认知识组织方式 = 学术研究式而非百科词条式）。

GPT-5.6 Sol 正式裁定（2026-09-05, O6-Q2 gate 进行中讨论）:
1. 路线: Q2 先收可靠性门（不动）→ O7 独立主轴: O7-A 规范+评审器 → O7-B 版本/译者/locator 元数据
   → O7-C 二手文献检索 → O7-D 二手语料规模化 → O7-E Scholarly Quality Gate（B/C 可部分并行;
   metadata-first, 禁止 prompt-first——工具不存在就先写"必须引两个学者"只会逼出伪造）。
2. 五维学术 rubric（各 0-4, evaluation-only）: TEXTUAL_GROUNDING / ARGUMENT_RECONSTRUCTION /
   INTERPRETIVE_PLURALITY / HISTORICAL_DISCIPLINE / LITERATURE_ORIENTATION; 深学术问题不允许单项 <2;
   六类硬 flag 与分数分离: FABRICATED_BIBLIOGRAPHY / FABRICATED_SCHOLAR_ATTRIBUTION /
   PRIMARY_TEXT_MISREPRESENTATION / MAJOR_ANACHRONISM / FALSE_EXACT_QUOTE / LITERATURE_ACCESS_OVERCLAIM。
3. 评审结构: Runtime ≠ judge; Independent LLM Judge（测量仪器）→ GPT-5.6 Sol（最终裁决; 100% 低分/疑似
   伪造复核 + 20% 随机 PASS 抽审）; judge 输入 = 问题+回答+证据 digest+书目记录+persona+任务类别。
4. 书目元数据: Tier1 版权页/扫描件自身 > Tier2 国图/CALIS/出版社目录 > Tier3 WorldCat/Crossref >
   Tier4 豆瓣（仅发现）; 记录带 value/source_type/source_locator/confidence/verified;
   WORK_LOCATOR_SCHEME 按传统（Stephanus/Bekker/KANT_AB/Akademia/work+§…）;
   CANONICAL 与 EDITION_SPECIFIC locator 分开; 精度阶梯 canonical→edition page→节/格言→章→书。
5. 二手文献: 存在性 = 检索命中记录; access_level 四态 METADATA_ONLY/ABSTRACT_AVAILABLE/
   FULL_TEXT_AVAILABLE/FULL_TEXT_READ; LITERATURE_ACCESS_HONESTY; FABRICATED_BIBLIOGRAPHIC_METADATA=0。
6. 产品原则: "缺少学术装置, 比伪造学术装置更专业"; 降引用粒度而不伪造精度, 降精度而不拒答整篇
   （预期反而降低 SAFE_REJECT）; "争议 ≥2 解读"仅在问题真涉及时启用（非万能模板）。
7. SCHOLARLY_CLAIM_LEDGER: evaluation-only（ObligationLedger 不复活）。
8. O7-A 交付物: Scholarly Contract（七纪律: textual/argument/interpretive plurality/historical/
   bibliographic honesty/literature access honesty/terminological）+ evaluation-only judge + 3 seed
   （S1 康德开放学术导航 / S2 先天综合判断论证重构 / S3 物自身解释争议）+ 5-10 calibration;
   PRODUCTION_POLICY/TOOLS/RUNTIME/CORPUS_CHANGED = false。
9. 纪律: O7 沿用 BASE_SHA/CODE_SHA/QUALITY_GATE_SHA/回执循环, gate 类型化
   （SPECIFICATION/DATA/CAPABILITY/CORPUS/SCHOLARLY_QUALITY_GATE_SHA）; Reviewer 不变。
10. 时序: Q2 PASS 后以其 accepted SHA 为 O7-A 干净 BASE; 在此之前不下 O7-A task book。
