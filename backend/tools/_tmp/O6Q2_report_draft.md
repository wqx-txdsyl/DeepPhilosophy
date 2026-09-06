# PhiAgent O6-Q2 — Final Product Quality Closeout（draft, 静态部分）

> BASE_SHA: `943516d2e`（Q1 报告 commit = Q2 代码基）
> CODE_SHA/QUALITY_GATE_SHA: `75974e364` ｜ 模型: DeepSeek deepseek-chat（与 Q1 同集一致, §22 零配置改动）
> Reviewer: GPT-5.6 Sol ｜ 阶段: PRODUCT QUALITY CLOSEOUT（validator/quote_bound 零改动）

## 1. FQ5 裁决（§1）

FQ5_IS_TRUE_FALSE_POSITIVE = **false**（TRUE POSITIVE）——裁决依据（Q1 §8 记录 + 本次复核）:
- USER_REQUEST= 休谟vs康德因果比较; MAIN_AGENT_CANDIDATE= 模型在最终回答中把"对自身表述的说明/转述"写成带引号或引用块的句子;
- QUOTE_EXTRACTOR_CLASSIFICATION= blockquote/引号 → 视为"以下措辞是原文"断言;
- VALIDATION_CODE= UNSUPPORTED_EXACT_QUOTE（match=NONE）;
- 判定: 候选的句法确实把非检索来源的措辞呈现为引用——即使模型主观意图是元说明, 句法上仍是 source-wording 断言（Q1 报告的"模型自我说明句"判例同族, 9 例多轮失败中 5 例为此形态）;
- 非 validator FP → 不 STOP; Q2 按 policy 路径收敛（铁律 17: 修复说明写普通正文; 铁律 2 引文表达纪律覆盖"自己的解释/诚实声明不进引用块"）。
- FQ5 原样保留在 Q2 同集/回归观察。

## 2. Q1 剩余失败语料冻结与 R 分类（§2, before-patch, Q1 after 数据集）

8 same-set 单轮 SAFE_REJECT: A1 B2 B3 C1 D3 E2 H4 R4
9 多轮未发布轮次: M1-T1 M2-T2 M2-T3 M2-T5 M3-T1 M4-T2 M5-T2 M5-T3 M5-T4

| CASE | 首次校验 codes | 修复后仍有 | 失败形态主因 |
|---|---|---|---|
| A1 | NEAR×2 | +meta说明引用块 | R5: 修复引入新 span（"以上引文我直接…逐字核录"说明排成引用块）|
| B2 | NEAR×3+UEQ×2 | 同族 | R3: 译文/记忆措辞静默升格逐字（权力意志三句）|
| B3 | UEQ×1 | 同 | R1: 检索说明元评论排成引用块 |
| C1 | NEAR×4+UEQ×2 | 同族 | R3: 沉思录译文变体当逐字 + 引用块未命中 |
| D3 | UEQ×1 | 同 | R1: 记忆措辞行内引号未披露（27 工具后仍失范, 兼 R10 性 churn）|
| E2 | UNVERIFIED_CITATION | 同 | R2: 编造"费希特相关章节"式章级标签 |
| H4 | UNVERIFIED_CITATION | 同 | R2: 只核验到书级却标"第125节"（§8 精确陷阱原型例）|
| R4 | NEAR+UEQ | 同族 | R3/R1: 论语近似当逐字 + 指令性文本泄漏进回答 |
| M1-T1 | UEQ | 同 | R1/R5: "本轮引用纪律说明"元评论成引用块 |
| M2-T2 | UNVERIFIED_CITATION | 同 | R2: 卷次合集里章级标签不在证据元数据 |
| M2-T3 | NEAR+UEQ | 同 | R5: 修复承诺句（"本轮我已把引号内…改为第47章逐字核验"）加引号 |
| M2-T5 | NEAR×3+UEQ | 同 | R1: 自述定义句加引号当原文 + NEAR 未收敛 |
| M3-T1 | NEAR | 同 | R3: 恶魔喻译文近似当逐字 |
| M4-T2 | NEAR+UEQ | 同 | R1: "此为我对篇内编排的综合理解（属分析性判断…）"被打引号 |
| M5-T2 | NEAR×3+UEQ | 同 | R3: 贡斯当译文近似当逐字 ×4 |
| M5-T3 | NEAR×5 | 同 | R3: 社会契约论译文近似当逐字 ×5, 修复零收敛 |
| M5-T4 | UC×2+NEAR+UEQ | 同 | R2/R3: 章级标签超出已核验粒度 |

**R1-R11 计数（before patch, 每 case 一个主因）**: R1(final-draft引文纪律/元评论引号)=5, R2(引用精度/标签超粒度)=4, R3(NEAR→exact)=6, R5(修复制造新span)=2, R4/R6/R7/R8/R9/R10/R11=0。
（R7/R8/R9/R10 非主因; 但 churn 加剧: 失败轮均 12–27 工具, 属修复轮反复检索。）

## 3. Policy diff（Q2, 113→119 行 ≤120; POLICY_RULES_DEDUPED= 铁律17 重写合并了旧17+§5 保留语义, 铁律2 自检行合并 §6+§8, 铁律1 校准行合并 §13）

| 铁律 | before (Q1) | after (Q2) | 对应 |
|---|---|---|---|
| 17 修复策略 | 不原样重复；按反馈修表达/补研究/删除 | **修复合同**: 逐条读机械反馈定位每个被打回 span; 已成立部分保持不动; 只修失败处; 主张重要且证据可补才研究; 提交前自查 span 全消除; 修复说明写普通正文 | §4/§5/§9 |
| 2 引文纪律尾 | （标签纪律, 书级回退） | +落笔前自检: 引号/引用块/正式标注须有本会话证据支撑; 精确引文非必要宁用准确散文 | §6/§8 |
| 1 研究校准尾 | 充分即综合作答 | +不依赖逐字核验且已有知识可可靠作答即综合作答, 不为显得充分而持续加检 | §13 |

CORE_POLICY_LINES: 113 → 119（≤120 ✓; 无新任务类型枚举/无 IF 链; 无 Python 化语义动作）。

## 4. 模型可见元数据（§7/§8/§9 audit 结论）

- 工具结果命名一致性: search_books/get_chapter 每命中项统一 `citation_label`（canonical 形态【《书》·章】/书级【《书》】）; get_chapter 另带 book_title/chapter title 字段, 名称一致, 无需再归一（Q1 已闭环, Q2 保持）。
- citation_granularity: 由 citation_label 形态机械可见（含"·章"=章级; 无"·"=书级）; 不新增长字段（避免模型侧二义）。
- 修复反馈字段（Q1 冻结集, Q2 零改动）: issue code / locator(=候选内原文片段, 反馈内可检索) / match=NEAR/NONE / coverage / evidence_id / best_evidence=【《书》·章】; UNVERIFIED_CITATION 另列同书已检索章节名。
- NEAR 契约: 反馈 match=NEAR + "approximation note" 语义 + 铁律2"近似措辞不得当作逐字原文呈现"。
- 零发明: _cite_label 无章回退书级、空书名返回空串; 检索层无节/格言号合成路径。
- 结论: 元数据层无需 Q2 改动; Q2 缺的是对既有机械信息的"收敛使用"——policy 已补。

## 5. 多轮证据持久化审计（§10/§11, Q1 snapshot 24 轮）

逐轮 tool 序列显示: 24/24 轮证据按需**轮内重读**（失败轮均 ≥5 次 get_chapter/get_book_detail）;
TURN_N 与 TURN_N+1 模型可见证据 = 轮内检索池（无跨轮合并——stream_agent 无 evidence 参数）;
分类: REHYDRATED（定点重读, 需逐字时）= 失败轮与成功轮均发生; NOT_RELEVANT = 解释轮;
**LOST = 0** → §11: 不实现 ConversationEvidenceContext（无真实丢失; 避免新增治理子系统; 铁律16 边界 + 定点重读政策已覆盖）。
HISTORY_IS_NOT_EVIDENCE: 保持（Q1 T9 + Q2 T9 测试）; AGENT_SWITCH_ISOLATION: 保持（身份显式, 人格/历史 ≠ 证据）。

## 6. 质量完整性（§28 预计, 同集/fresh 数据落地后填实）

## 7. 同集 Live A/B（§24, QUALITY_GATE_SHA=75974e364, 单次不挑样）

| 指标 | Q1 after (943516d2e) | Q2 (75974e364) | 目标 |
|---|---|---|---|
| SAME_SET_SINGLE | 24/32 | _/32 | ≥26/32 |
| SAME_SET_MULTI | 15/24 | _/24 | ≥20/24 |
| REPAIR_SUCCESS | 15/23 | _/_ | ≥70% |
| REPAIR_EXHAUSTION | 8/23 | _/_ | ≤20% |
| FIRST_PASS / R1 / R2 | | | |

## 8. Fresh Anti-Overfit（§26, 全新集: 8 单题 + 2 会话×4=8 轮, 共 16 答案轮; 与 O6/Q1/prompt/单测零重叠）

| 指标 | 值 |
|---|---|
| FRESH_TOTAL_TURNS | 16 |
| FRESH_PUBLISHED | _ |
| FRESH_PUBLICATION_RATE | _（目标 ≥75%）|

## 9. 结论与回执（数据落地后填写）

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
