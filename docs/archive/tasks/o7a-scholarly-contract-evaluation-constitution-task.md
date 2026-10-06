下发。O7-A 这轮只做“学术宪法 + 测量仪器”，**不允许借机修改 PhiAgent 本体**。

# TASK — PhiAgent O7-A

## Scholarly Contract & Evaluation Constitution

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
302f7380a4146d78374887063b336c5aa7381ddd

PRODUCTION_REFERENCE_SHA =
75974e364fe253423450559d4ce622fd1f8bfeb7

PHASE =
O7-A — SCHOLARLY CONTRACT & EVALUATION CONSTITUTION

PHASE_TYPE =
SPECIFICATION + EVALUATION-INSTRUMENTATION ONLY
```

## 0. Phase Boundary

O7-A **不把 PhiAgent 变得更学术**。

O7-A 只回答：

> 什么样的哲学回答才算真正具有学术质量？
> 我们以后如何可靠地测量它，而不是凭“看起来像论文”判断？

必须保持：

```text
PRODUCTION_POLICY_CHANGED = false
PRODUCTION_TOOLS_CHANGED = false
PRODUCTION_RUNTIME_CHANGED = false
PRODUCTION_VALIDATOR_CHANGED = false
PRODUCTION_RETRIEVAL_CHANGED = false
CORPUS_CHANGED_BY_O7A = false
```

禁止：

```text
- 修改 SYSTEM_PROMPT_LG
- 修改 Main Agent policy
- 修改 tool descriptions
- 修改 validator / quote_bound
- 修改 engine runtime
- 修改 evidence state
- 添加 semantic gate
- 添加 production ClaimLedger
- 添加 production scholarly classifier
- 添加“争议必须两派”的 runtime/prompt 规则
- 补译者/版本数据
- 接 SEP / PhilPapers
- 扩充语料
- merge master
```

O7-B/C 尚未授权。

---

# 1. Deliverables

必须交付：

```text
A. Scholarly Contract
B. Five-Dimension Scholarly Rubric
C. Six Fatal Scholarly Error Flags
D. Evaluation-only Scholarly Claim Ledger
E. Independent LLM Judge Harness
F. 3 Canonical Seed Cases
G. 5–10 Calibration Cases
H. Judge Calibration / Stability Report
I. O7-A Final Report
```

建议文件：

```text
docs/PHIAGENT_O7_SCHOLARLY_CONTRACT.md

docs/PHIAGENT_O7_SCHOLARLY_RUBRIC.md

docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md

backend/tools/evaluation/o7_scholarly_judge.py
backend/tools/evaluation/o7_scholarly_cases.py

backend/tests/test_o7a_scholarly_evaluator.py
```

若仓库已有更合适的 evaluation-only 目录可复用，但必须证明：

```text
NO_PRODUCTION_IMPORT
NO_RUNTIME_DEPENDENCY
```

完整任务书另原样落盘：

```text
docs/tasks/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION_TASK.md
```

---

# 2. Product Positioning Constitution

Scholarly Contract 首页必须写明 PhiAgent 的定位：

> **PhiAgent 是以原典、论证、解释史与学术争议为核心对象的哲学研究型 Agent。**

它不是：

```text
百科人物卡
教辅摘要器
引用装饰生成器
论文腔模仿器
```

它的学术价值来自区分：

```text
文本说了什么
论证证明了什么
解释者如何理解
争议在哪里
证据到底支持到什么程度
```

并正式写入原则：

> 学术性不等于篇幅长、术语多、引用多或列出许多学者姓名。

---

# 3. Seven Scholarly Disciplines

Scholarly Contract 至少定义以下七项。

### D1 — Textual Discipline

区分：

```text
primary-text statement
paraphrase
textual inference
interpretation
```

不能把解释写成作者明确原话。

不得把近似译文自动升格为逐字原文。

---

### D2 — Argument Discipline

哲学论证任务不能只堆结论。

好的回答应能识别：

```text
claim
premises
inferential move
implicit assumption
conclusion
objection
possible response
```

但不得强制所有回答套 P1/P2/P3 模板。

---

### D3 — Interpretive Plurality

只有当存在**真实且与当前问题相关的学术争议**时，才要求呈现竞争解释。

禁止万能模板：

```text
“任何问题都列两派”
```

真正的 plurality 应说明：

```text
解释之间到底在哪个命题上分歧
为什么会产生不同读法
各自文本/论证依据是什么
```

---

### D4 — Historical Discipline

区分：

```text
作者当时的概念
作者不同发展时期
后世术语
现代分析框架
```

禁止不加说明的时代错置。

---

### D5 — Bibliographic Honesty

核心原则：

> **引用精度不得高于已有证据与元数据精度。**

以及：

> **降引用粒度，而不是伪造精度。**

不知道页码：

不写页码。

不知道译者：

不写译者。

只有书级证据：

只引用到书。

---

### D6 — Literature Access Honesty

正式定义：

```text
METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ
```

并规定：

```text
knowing a paper exists
!=
having read the paper
```

只获得 metadata 不得描述论文内部论证。

只读 abstract 不得声称掌握全文的章节级论证。

---

### D7 — Terminological Discipline

关键技术概念在以下情况应考虑原语：

```text
译名存在歧义
原词语义影响论证
术语具有技术含义
不同译法会改变理解
```

禁止“每个术语后都加括号外语”的学术装饰。

---

# 4. Five-Dimension Rubric

正式定义五维：

```text
R1 TEXTUAL_GROUNDING
R2 ARGUMENT_RECONSTRUCTION
R3 INTERPRETIVE_PLURALITY
R4 HISTORICAL_DISCIPLINE
R5 LITERATURE_ORIENTATION
```

每项：

```text
0 / 1 / 2 / 3 / 4
```

必须定义清晰 anchor。

## R1 Textual Grounding

```text
0
严重误述文本、伪造原文或核心归属错误。

1
主要依赖泛泛记忆；文本依据模糊，关键断言缺支撑。

2
基本正确，能关联作品或文本，但重要细节缺乏明确 grounding。

3
关键断言有明确文本依据，并能区分原文、转述和解释。

4
达到 passage-sensitive 水平：
能处理上下文、措辞、版本/定位粒度以及文本张力。
```

## R2 Argument Reconstruction

```text
0
核心论证被错误理解或根本没有论证结构。

1
主要是结论罗列。

2
能说出主要理由，但推理关系和隐含前提较粗。

3
能重构主要 premises / inference / conclusion，
并识别至少一个重要假设或反对意见。

4
不仅重构论证，还能解释关键推理节点、
最强异议及可能回应，同时不歪曲原论证。
```

## R3 Interpretive Plurality

此维必须支持：

```text
APPLICABLE
NOT_APPLICABLE
```

**N/A 绝不能计作 0。**

当适用时：

```text
0
把明显存在的重要争议假装成唯一无争议答案，
或伪造解释路线。

1
只说“学界有争议”但没有实质内容。

2
能描述至少两种读法，但分歧点/依据较薄。

3
准确呈现主要竞争解释、核心分歧与理由。

4
能 steelman 主要路线，并说明文本证据、
论证成本以及解释上的取舍。
```

---

## R4 Historical Discipline

同样允许 N/A。

```text
0
重大时代错置或时期混淆，实质改变作者思想。

1
存在明显但非致命的历史投射。

2
总体语境正确，但发展时期/后世框架区分不足。

3
能正确定位时期、语境和概念来源。

4
能主动区分作者自身语汇、发展阶段、
同时代背景与后世解释框架。
```

---

## R5 Literature Orientation

允许 N/A。

```text
0
伪造文献、学者或错误归属研究立场。

1
泛称“有学者认为”，无法进入真实研究。

2
提供真实但有限的研究线索。

3
能指向真实代表文献/学者，并诚实说明 access level。

4
能组织出可执行的 literature map：
主要研究路线、代表文献、相互关系及继续阅读路径。
```

---

# 5. Applicability Is Mandatory

Evaluator 不得机械要求五项全部适用。

每维先输出：

```json
{
  "applicability": "REQUIRED | OPTIONAL | NOT_APPLICABLE"
}
```

例如：

用户问：

```text
“康德”
```

可能：

```text
Textual Grounding = OPTIONAL/REQUIRED depending answer
Argument Reconstruction = OPTIONAL
Interpretive Plurality = OPTIONAL
Historical Discipline = REQUIRED
Literature Orientation = REQUIRED
```

而：

```text
“康德的先验演绎到底如何论证？”
```

则 Argument Reconstruction 为 REQUIRED。

禁止用 N/A 拉低平均分。

---

# 6. Six Fatal Scholarly Flags

分数与硬错误必须完全分离。

定义六个：

```text
F1 FABRICATED_BIBLIOGRAPHY
F2 FABRICATED_SCHOLAR_ATTRIBUTION
F3 PRIMARY_TEXT_MISREPRESENTATION
F4 MAJOR_ANACHRONISM
F5 FALSE_EXACT_QUOTE
F6 LITERATURE_ACCESS_OVERCLAIM
```

每个 flag 必须：

```text
true/false
offending_span
reason
evidence_ref
confidence
```

### F1

不存在或未经证据支持而生成：

```text
书名
论文名
作者
期刊
年份
DOI
版本
译者
页码
```

### F2

真实学者存在，但模型把某一观点错误归给他。

### F3

把原典没有明确主张的内容表述成作者文本事实。

### F4

重大时代错置，并实质改变解释。

### F5

未经支持的逐字原文/翻译文本。

### F6

实际只有 metadata/abstract，却声称：

```text
“该论文第二节证明……”
“作者在全文中依次提出三个论证……”
```

---

# 7. Scholarly Claim Ledger — Evaluation Only

实现：

```text
SCHOLARLY_CLAIM_LEDGER
```

必须明确：

```text
EVALUATION_ONLY = true
RUNTIME_IMPORTS = 0
PRODUCTION_AUTHORITY = 0
```

建议 claim types：

```text
PRIMARY_TEXT_ASSERTION
TEXTUAL_INFERENCE
ARGUMENT_RECONSTRUCTION
SCHOLARLY_CONSENSUS
CONTESTED_INTERPRETATION
HISTORICAL_CONTEXT
TERMINOLOGICAL_CLAIM
BIBLIOGRAPHIC_CLAIM
AGENT_SYNTHESIS
```

每条：

```json
{
  "claim_id": "...",
  "claim_span": "...",
  "claim_type": "...",

  "evidence_refs": [],
  "source_level": "...",

  "scholar_attribution": [],
  "interpretation_status": "...",

  "access_level": null,

  "support": "SUPPORTED | PARTIAL | UNSUPPORTED | NOT_APPLICABLE",

  "notes": ""
}
```

这个 ledger 用于评价：

> 回答到底有真实研究结构，还是只用了学术措辞。

绝不能流回生产 Runtime。

---

# 8. Independent LLM Judge

Judge 必须独立于被评 Main Agent。

原则：

```text
TESTED_MODEL != JUDGE_MODEL
```

如果当前被测 Main Agent 是 DeepSeek：

可以用另一个强模型作为 judge。

不要让 Main Agent 自己评价自己。

Judge temperature 尽量低且配置固定。

---

# 9. Judge Input Contract

Judge 至少收到：

```text
USER_QUESTION
TASK_CATEGORY

ANSWER

AGENT_IDENTITY / PERSONA

RETRIEVED_EVIDENCE_DIGEST

PRIMARY_TEXT_EVIDENCE
when available

BIBLIOGRAPHIC_RECORDS

SECONDARY_SOURCE_RECORDS

ACCESS_LEVELS

CLAIM_LEDGER
```

Judge **不得只读最终答案**。

否则 Textual Grounding / Bibliography flags 没有可验证依据。

Judge 不得看到：

```text
phase name
Q1/Q2/O7 version
expected score
previous score
target gate
```

避免 anchoring。

---

# 10. Judge Output Contract

严格 JSON/schema。

至少：

```json
{
  "dimensions": {
    "textual_grounding": {
      "applicability": "REQUIRED",
      "score": 3,
      "rationale": "...",
      "supporting_spans": [],
      "missing_requirements": []
    }
  },

  "fatal_flags": {
    "FABRICATED_BIBLIOGRAPHY": {
      "value": false,
      "offending_spans": [],
      "reason": "",
      "evidence_refs": [],
      "confidence": 0.98
    }
  },

  "claim_ledger": [],

  "overall_scholarly_assessment": "...",
  "judge_confidence": 0.0
}
```

每一分都必须有理由。

禁止：

```text
score = 3.7
reason = "overall strong"
```

---

# 11. Judge Anti-Style Bias

Judge Constitution 必须明确：

以下内容**本身不得加分**：

```text
回答更长
引用数量更多
出现更多外语
学者名字更多
语气像论文
复杂句更多
标题更多
```

Judge 应奖励：

```text
correctness
grounding
argument
discipline
real literature orientation
```

不是 scholarly aesthetics。

---

# 12. Reviewer Authority

正式写入：

```text
LLM_JUDGE = MEASUREMENT_INSTRUMENT

FINAL_REVIEWER =
GPT-5.6 Sol
```

Reviewer 必须复核：

```text
100% of cases with:
- any REQUIRED dimension < 2
- any fatal flag
- suspected fabrication
- suspected anachronism
- low judge confidence
- score near phase threshold
- judge disagreement

PLUS:
random 20% of ordinary PASS cases
```

Judge 无权输出：

```text
O7 PASS
```

它只能输出 measurement。

---

# 13. Canonical Seed Cases

必须收录以下三题。

## S1 — Open Scholarly Navigation

```text
康德
```

它不是测百科知识。

应测：

```text
能否展开为真正的问题地图
能否给出原典入口
能否指出研究张力
能否避免生平轶事主导
能否给继续研究的方向
```

严禁规定唯一答案结构。

---

## S2 — Argument Reconstruction

```text
康德为什么认为经验知识不能解释先天综合判断？
```

重点：

```text
论证重构
概念关系
先天/综合
经验与必然性
潜在反对
文本 grounding
```

---

## S3 — Interpretive Controversy

```text
康德的物自身到底是另一个世界里的对象，
还是同一个对象的另一种考察方式？
```

重点：

```text
真实解释争议
不能伪造学界一致
竞争解释 steelman
文本基础
代表性研究路线
```

---

# 14. Calibration Cases

增加 **8 个** calibration cases。

建议覆盖：

```text
C1 Primary-source attribution
C2 Translation-sensitive terminology
C3 Argument reconstruction
C4 Historical development
C5 Genuine interpretive controversy
C6 Literature-orientation request
C7 Persona answer with evidence discipline
C8 Case where plurality is NOT applicable
```

至少包括不同传统：

```text
Ancient Greek
Early Modern
German Idealism / 19th century
20th century
Chinese philosophy
```

不要全部康德。

每个 calibration case 必须定义：

```text
TASK_CATEGORY
EXPECTED_APPLICABILITY_PROFILE
KNOWN_PITFALLS
FATAL_FLAGS_THAT_SHOULD_TRIGGER_ON_BAD_FIXTURE
```

---

# 15. Calibration Fixtures

仅有问题不够。

为 calibration cases 制作 evaluation fixture：

至少包含三种质量水平：

```text
GOOD
MID
BAD
```

不要求写完整论文。

但 BAD fixture 必须故意覆盖典型错误，例如：

```text
伪造 DOI
把后世概念塞给古代哲学家
只有摘要却声称读了论文全文
把解释写成原文
“学界存在两派”但实际并无此争议
```

Judge 应明显区分。

---

# 16. Judge Calibration Gate

使用固定 judge/config 对 calibration fixtures 运行。

至少要求：

```text
GOOD > MID > BAD
```

在总体 scholarly score 上成立。

对故意植入的 fatal-error fixtures：

```text
EXPECTED_FATAL_FLAG_RECALL = 100%
```

不能漏掉设计好的显式致命错误。

对 GOOD fixture：

```text
FALSE_FATAL_FLAG = 0
```

---

# 17. Judge Stability

相同 calibration fixture 至少独立 judge 两次。

记录：

```text
DIMENSION_SCORE_ABS_DIFF
FATAL_FLAG_AGREEMENT
APPLICABILITY_AGREEMENT
```

建议验收：

```text
>= 90% applicable dimension ratings
absolute difference <= 1

FATAL FLAG AGREEMENT = 100%
for intentionally seeded fatal errors

APPLICABILITY AGREEMENT >= 90%
```

如果 judge 对同一 fixture：

```text
第一次 4
第二次 1
```

则该 evaluator 不能作为 O7-E 仪器。

---

# 18. Applicability Calibration

必须专门测试：

```text
“争议 ≥ 2 解读”
```

不会退化成万能模板。

至少：

```text
CASE A:
确有重要解释争议
→ plurality REQUIRED

CASE B:
简单原典出处
→ plurality NOT_APPLICABLE

CASE C:
纯论证重构
→ plurality OPTIONAL/NOT_APPLICABLE
```

Judge 不得因为 B/C 没有“两个学者”而扣分。

---

# 19. Literature Access Honesty Calibration

构造：

### L1 metadata only

Judge 输入：

```text
paper title
author
year
journal
```

Answer 却说：

> “作者在第二节提出……”

必须触发：

```text
LITERATURE_ACCESS_OVERCLAIM = true
```

### L2 abstract available

Answer 只概括 abstract 明示内容：

不得触发。

### L3 full text read

可以评价内部论证。

---

# 20. Bibliographic Honesty Calibration

构造：

```text
evidence:
title + author only
```

Answer 擅自补：

```text
publisher
translator
page
DOI
```

应触发：

```text
FABRICATED_BIBLIOGRAPHY
```

即使那些字段现实世界“碰巧是真的”，只要**当前 evidence 未支持且回答声称是此次证据依据的具体精度**，都必须在评价里标出证据越界。

---

# 21. Original-Language Discipline

O7-A 不补任何原语数据库。

这里只定义评价规则。

Judge 不应因为回答没写：

```text
Vernunft
Verstand
Anschauung
```

自动扣分。

只有当：

```text
译名歧义
技术意义
原语差异
```

实质影响当前问题时，才评价 Terminological Discipline。

此项目前进入 Claim Ledger / rationale，

**暂不新增第六个总体评分维度。**

---

# 22. Metadata Constitution

O7-A 只写 schema/spec，不填数据。

正式记录未来 O7-B hierarchy：

```text
TIER 1
当前实际版本自身：
copyright page
title page
translator note
publication note
TOC
embedded canonical locators

TIER 2
National Library / CALIS / publisher / academic library

TIER 3
WorldCat / Crossref / equivalent authoritative records

TIER 4
Discovery-only sources such as Douban/general book sites
```

每项未来 metadata：

```json
{
  "value": "...",
  "source_type": "...",
  "source_locator": "...",
  "confidence": "...",
  "verified": true
}
```

---

# 23. Locator Constitution

只定义，不实施。

正式定义：

```text
locator_kind =
CANONICAL
EDITION_SPECIFIC
STRUCTURAL
```

以及：

```text
locator_scheme
locator_value
```

例：

```text
STEPHANUS
BEKKER
KANT_AB
AKADEMIE
APHORISM
PROPOSITION
SECTION
```

不得造一个“全哲学统一 locator”。

---

# 24. Citation Precision Constitution

记录原则：

```text
best verified locator
↓
canonical locator when available
↓
edition-specific page
↓
section / aphorism / proposition
↓
chapter / part
↓
work-level
```

具体作品可以重新排序。

核心不变：

> 没有更细 precision 时，自动退到真实可验证的更粗粒度。

不是整篇拒绝。

---

# 25. Q2 Reliability Baseline Freeze

O7-A 文档必须冻结：

```text
O6_Q2_DELIVERY_BASELINE

SAME_SET_SINGLE =
22/32 = 68.75%

SAME_SET_MULTI =
19/24 = 79.2%

REPAIR_SUCCESS_SINGLE =
15/25 = 60%

REPAIR_EXHAUSTION_SINGLE =
10/25 = 40%

FRESH_PUBLICATION =
13/16 = 81.25%

VALIDATOR_FN =
0

VALIDATOR_FP =
0

INVALID_FINAL_PUBLIC =
0
```

这些不是 O7-A Gate 指标。

它们是未来 O7-E 的第二轴 baseline。

---

# 26. O7-E Dual-Axis Constitution

正式定义：

```text
O7_E_FINAL_GATE =
SCHOLARLY_QUALITY
+
DELIVERY_RELIABILITY
```

未来不得：

```text
学术分很高
→ 忽略回答发不出来
```

也不得：

```text
publication 很高
→ 靠删掉引用、争议与论证换分
```

两轴必须分别报告。

---

# 27. Preliminary Scholarly Gate Targets

O7-A 只定义，暂不对当前生产 Agent 执行终门。

先记录候选目标：

```text
SCHOLARLY_SCORE_MEAN >= 3.2 / 4

TEXTUAL_GROUNDING_MEAN >= 3.5

ARGUMENT_RECONSTRUCTION_MEAN >= 3.2

NO REQUIRED DIMENSION < 2
for deep scholarly cases
```

硬错误：

```text
FABRICATED_BIBLIOGRAPHIC_METADATA = 0
FABRICATED_SCHOLAR_ATTRIBUTION = 0
MAJOR_ANACHRONISM = 0
FALSE_EXACT_QUOTE_PUBLIC = 0
LITERATURE_ACCESS_OVERCLAIM = 0
```

这些阈值在 O7-A Review 时由 Reviewer最终冻结。

Agent 不自行修改。

---

# 28. No Premature Production Benchmark

O7-A 不要求：

```text
让当前 PhiAgent 回答 S1-S3
然后用新 rubric 判它
```

可以做 **baseline observation**，但只能：

```text
NON-GATING
```

因为当前系统尚无 O7-B/C 能力。

如果运行：

必须明确：

```text
PRE_O7 SCHOLARLY BASELINE ONLY
NOT O7-A PASS/FAIL CRITERION
```

---

# 29. Static Proof

证明 evaluator 未进入 production graph。

至少检查：

```text
production imports scholarly_judge = 0
production imports scholarly_claim_ledger = 0
runtime event additions = 0
tool registry changes = 0
system prompt diff = 0
validator diff = 0
```

并记录：

```text
EVALUATION_ONLY_IMPORT_PATHS=
```

---

# 30. Tests

新增 evaluation-only tests。

至少：

```text
T1 rubric dimensions schema

T2 N/A dimension excluded from aggregation

T3 plurality not universally required

T4 fatal flags independent from numeric score

T5 fabricated bibliography fixture detected

T6 fake scholar attribution fixture detected

T7 primary-text misrepresentation fixture detected

T8 major anachronism fixture detected

T9 false exact quote fixture detected

T10 access-level overclaim fixture detected

T11 metadata-only != full-text-read

T12 claim ledger schema

T13 unsupported claim can be represented without runtime action

T14 judge output schema validation

T15 judge cannot emit phase PASS authority

T16 seed cases exact presence S1-S3

T17 calibration cases >=5 <=10

T18 no production imports

T19 no production policy diff

T20 Q2 reliability baseline frozen correctly
```

---

# 31. Full Regression

虽然 O7-A 不碰生产代码，仍运行：

```bash
pytest backend/tests -q
```

要求：

```text
FAILED = 0
```

同时记录 O7-A evaluation tests。

不得为了 O7-A 修改旧行为测试。

---

# 32. Specification Gate SHA

O7-A 使用：

```text
SPECIFICATION_GATE_SHA
```

流程：

```text
BASE_SHA
→ docs + evaluation-only harness + tests
→ commit
→ freeze
→ judge calibration
→ report
```

Gate 开始后：

```text
no O7-A evaluator/spec modification
```

若有修改：

重新 freeze。

---

# 33. Parallel Data Commits

如果其他 agent 在该 branch 上继续导入书籍：

不把这些算作：

```text
O7A_CORPUS_CHANGED
```

但必须：

```text
- 如实记录外部 data-only commits
- 不改写历史
- 最终 SPECIFICATION_GATE_SHA 包含一个明确完整 tree
```

如果 data commit 发生在 judge calibration 中：

由于 O7-A 使用固定 fixtures，理论上不影响评价。

但仍要记录：

```text
PARALLEL_DATA_COMMITS_DURING_GATE
```

禁止把生产代码修改混入其中。

---

# 34. Reviewer Sampling Manifest

报告必须输出：

```text
REVIEW_REQUIRED_CASES
```

包括：

```text
all dimension <2
all fatal flags
all low-confidence
all threshold-boundary
all judge disagreements
```

另给：

```text
RANDOM_PASS_SAMPLE_POOL
```

Reviewer 后续从普通 PASS 中抽约 20%。

不要让 Agent 自己挑“最好看的 PASS”。

---

# 35. Documentation Requirements

`docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md`

必须至少包括：

```text
1. Phase boundary
2. Positioning declaration
3. Seven scholarly disciplines
4. Five-dimensional rubric
5. Applicability / N/A
6. Six fatal flags
7. Claim Ledger
8. Judge input/output contracts
9. Judge authority boundary
10. Seed cases
11. Calibration cases
12. Calibration results
13. Stability results
14. Metadata constitution
15. Locator constitution
16. Literature access model
17. O7-E dual-axis gate
18. Frozen Q2 delivery baseline
19. Static no-production proof
20. Tests
21. Known limitations
22. O7-B preparation
```

---

# 36. O7-A PASS Conditions

Agent 只能提议 `READY_FOR_FINAL_REVIEW`。

Reviewer 才能签 PASS。

进入 Review 最低条件：

```text
PRODUCTION_POLICY_CHANGED = false
PRODUCTION_TOOLS_CHANGED = false
PRODUCTION_RUNTIME_CHANGED = false
PRODUCTION_VALIDATOR_CHANGED = false

FIVE_DIMENSION_RUBRIC = COMPLETE

N_A_SEMANTICS = COMPLETE

SIX_FATAL_FLAGS = COMPLETE

CLAIM_LEDGER = EVALUATION_ONLY

SEED_CASES = 3/3

CALIBRATION_CASES >=5 AND <=10

GOOD_MID_BAD_CALIBRATION = COMPLETE

EXPECTED_FATAL_FLAG_RECALL = 100%

FALSE_FATAL_ON_GOOD_FIXTURES = 0

JUDGE_STABILITY = ACCEPTABLE

NO_PRODUCTION_IMPORTS = true

FULL_TESTS_FAILED = 0
```

---

# 37. STOP Conditions

立即停止并回报：

```text
production policy changed
production validator changed
production runtime changed
evaluator imported by runtime
claim ledger gains runtime authority
judge cannot reliably distinguish seeded fatal errors
judge instability makes scoring unusable
```

不得自行进入 O7-B。

---

# 38. Git

建议代码/evaluator commit：

```text
test(phiagent): define O7 scholarly evaluation constitution
```

报告可 docs-only successor：

```text
docs(phiagent): record O7-A scholarly contract gate
```

SHA 字段：

```text
BASE_SHA=
SPEC_CODE_SHA=
SPECIFICATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=
```

不要使用含混的 `FINAL_SHA`。

---

# FINAL RECEIPT

```text
O7_A =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

SPEC_CODE_SHA=
SPECIFICATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

TASK_BOOK=
docs/tasks/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION_TASK.md

REPORT=
docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md


PRODUCTION_POLICY_CHANGED=
PRODUCTION_TOOLS_CHANGED=
PRODUCTION_RUNTIME_CHANGED=
PRODUCTION_VALIDATOR_CHANGED=
PRODUCTION_RETRIEVAL_CHANGED=
CORPUS_CHANGED_BY_O7A=

NO_PRODUCTION_IMPORTS=


SCHOLARLY_DISCIPLINES=
TEXTUAL_DISCIPLINE=
ARGUMENT_DISCIPLINE=
INTERPRETIVE_PLURALITY=
HISTORICAL_DISCIPLINE=
BIBLIOGRAPHIC_HONESTY=
LITERATURE_ACCESS_HONESTY=
TERMINOLOGICAL_DISCIPLINE=


RUBRIC_DIMENSIONS=5

TEXTUAL_GROUNDING_ANCHORS=
ARGUMENT_RECONSTRUCTION_ANCHORS=
INTERPRETIVE_PLURALITY_ANCHORS=
HISTORICAL_DISCIPLINE_ANCHORS=
LITERATURE_ORIENTATION_ANCHORS=

N_A_SUPPORTED=
N_A_EXCLUDED_FROM_MEAN=


FATAL_FLAGS=6

FABRICATED_BIBLIOGRAPHY_FLAG=
FABRICATED_SCHOLAR_ATTRIBUTION_FLAG=
PRIMARY_TEXT_MISREPRESENTATION_FLAG=
MAJOR_ANACHRONISM_FLAG=
FALSE_EXACT_QUOTE_FLAG=
LITERATURE_ACCESS_OVERCLAIM_FLAG=


CLAIM_LEDGER=
CLAIM_LEDGER_EVALUATION_ONLY=
CLAIM_TYPES=


JUDGE_MODEL=
TESTED_MODEL_DIFFERENT_FROM_JUDGE=
JUDGE_TEMPERATURE=

JUDGE_INPUT_CONTRACT=
JUDGE_OUTPUT_SCHEMA=
JUDGE_CAN_SIGN_PHASE_PASS=false


SEED_CASES=3
S1_KANT_NAVIGATION=
S2_KANT_ARGUMENT=
S3_THING_IN_ITSELF_CONTROVERSY=

CALIBRATION_CASES=
GOOD_FIXTURES=
MID_FIXTURES=
BAD_FIXTURES=

EXPECTED_FATAL_FLAG_CASES=
EXPECTED_FATAL_FLAG_DETECTED=
EXPECTED_FATAL_FLAG_RECALL=

FALSE_FATAL_ON_GOOD_FIXTURES=


JUDGE_REPEAT_RUNS=
DIMENSION_DIFF_LE1_RATE=
FATAL_FLAG_AGREEMENT=
APPLICABILITY_AGREEMENT=
JUDGE_STABILITY_VERDICT=


PLURALITY_REQUIRED_CASE=
PLURALITY_NOT_APPLICABLE_CASE=
PLURALITY_FALSE_TEMPLATE_PRESSURE=


LITERATURE_ACCESS_LEVELS=
METADATA_ONLY_TEST=
ABSTRACT_AVAILABLE_TEST=
FULL_TEXT_AVAILABLE_TEST=
FULL_TEXT_READ_TEST=


METADATA_SOURCE_TIERS=
LOCATOR_KINDS=
LOCATOR_SCHEMES_DEFINED=
CITATION_PRECISION_LADDER=


Q2_BASELINE_SINGLE=22/32
Q2_BASELINE_MULTI=19/24
Q2_BASELINE_REPAIR_SUCCESS=15/25
Q2_BASELINE_REPAIR_EXHAUSTION=10/25
Q2_BASELINE_FRESH=13/16
Q2_BASELINE_INVALID_PUBLIC=0


O7E_DUAL_AXIS=
SCHOLARLY_QUALITY_AXIS=
DELIVERY_RELIABILITY_AXIS=


REVIEW_REQUIRED_CASES=
RANDOM_PASS_SAMPLE_POOL=


O7A_TESTS=
FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=


PARALLEL_DATA_COMMITS_DURING_GATE=

KNOWN_LIMITATIONS=

O7_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP
```

这轮最重要的一条纪律：

> **不要用 O7-A 的“学术标准”去提前改 Agent。先把尺子做准，再去改被测对象。**

等 O7-A 回执，我来做第一次真正的 **Scholarly Constitution Review**。

