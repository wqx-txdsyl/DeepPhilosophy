# PhiAgent Scholarly Rubric（O7 五维学术评价量规 · evaluation-only）

> PHASE: O7-A ｜ 用途: 独立 LLM Judge 的测量仪器（非 runtime，非生产 gate）
> 每个 REQUIRED/OPTIONAL 维度 0–4 分；`NOT_APPLICABLE` 不计 0、不入均值。
> 每一分都必须给出 rationale + supporting_spans + missing_requirements；禁止只给数字。

---

## R1 — TEXTUAL_GROUNDING（文本依据）

| 分 | Anchor |
|---|---|
| 0 | 严重误述文本、伪造原文或核心归属错误 |
| 1 | 主要依赖泛泛记忆；文本依据模糊，关键断言缺支撑 |
| 2 | 基本正确，能关联作品或文本，但重要细节缺乏明确 grounding |
| 3 | 关键断言有明确文本依据，并能区分原文、转述和解释 |
| 4 | passage-sensitive 水平：能处理上下文、措辞、版本/定位粒度以及文本张力 |

Applicability: 文本类问题 REQUIRED；纯元问题（导航/谱系）可 OPTIONAL。

## R2 — ARGUMENT_RECONSTRUCTION（论证重构）

| 分 | Anchor |
|---|---|
| 0 | 核心论证被错误理解或根本没有论证结构 |
| 1 | 主要是结论罗列 |
| 2 | 能说出主要理由，但推理关系和隐含前提较粗 |
| 3 | 能重构主要 premises / inference / conclusion，并识别至少一个重要假设或反对意见 |
| 4 | 还能解释关键推理节点、最强异议及可能回应，同时不歪曲原论证 |

Applicability: 论证类问题 REQUIRED；"为什么"类比较/梳理题可 OPTIONAL。
不得以"没用 P1/P2/P3 模板"扣分——形态不等于结构。

## R3 — INTERPRETIVE_PLURALITY（解释多元）

**本维支持 `NOT_APPLICABLE`；N/A 绝不计 0、绝不因"没列两派"扣分。**

适用时的 Anchor：

| 分 | Anchor |
|---|---|
| 0 | 把明显存在的重要争议假装成唯一无争议答案，或伪造解释路线 |
| 1 | 只说"学界有争议"但没有实质内容 |
| 2 | 能描述至少两种读法，但分歧点/依据较薄 |
| 3 | 准确呈现主要竞争解释、核心分歧与理由 |
| 4 | 能 steelman 主要路线，并说明文本证据、论证成本以及解释上的取舍 |

Applicability: 问题真实涉及解释争议 → REQUIRED；简单原典出处 → NOT_APPLICABLE；
纯论证重构 → OPTIONAL/NOT_APPLICABLE。真实争议的判定依据：该分歧确为学界存在且与
当前问题相关（解释在哪个命题上分歧/为何产生不同读法/各自依据）。

## R4 — HISTORICAL_DISCIPLINE（史学纪律）

允许 N/A（如无时间维度的概念题）。

| 分 | Anchor |
|---|---|
| 0 | 重大时代错置或时期混淆，实质改变作者思想 |
| 1 | 存在明显但非致命的历史投射 |
| 2 | 总体语境正确，但发展时期/后世框架区分不足 |
| 3 | 能正确定位时期、语境和概念来源 |
| 4 | 能主动区分作者自身语汇、发展阶段、同时代背景与后世解释框架 |

## R5 — LITERATURE_ORIENTATION（文献导向）

允许 N/A（如无文献需求的入门释义）。

| 分 | Anchor |
|---|---|
| 0 | 伪造文献、学者或错误归属研究立场 |
| 1 | 泛称"有学者认为"，无法进入真实研究 |
| 2 | 提供真实但有限的研究线索 |
| 3 | 能指向真实代表文献/学者，并诚实说明 access level |
| 4 | 能组织出可执行的 literature map：主要研究路线、代表文献、相互关系及继续阅读路径 |

---

## Applicability 语义（强制）

Judge 对每维先输出：

```json
{"applicability": "REQUIRED | OPTIONAL | NOT_APPLICABLE"}
```

- Evaluator 不得机械要求五项全部适用；
- `NOT_APPLICABLE` 不计 0、不入均值、不拉低总分；
- 例：用户问「康德」→ Historical Discipline=REQUIRED、Literature Orientation=REQUIRED、
  其余视回答形态 OPTIONAL；「康德的先验演绎到底如何论证？」→ Argument Reconstruction=REQUIRED。

## 六类致命错误 Flag（与分数完全分离）

```
F1 FABRICATED_BIBLIOGRAPHY           凭空生成书/论文/作者/期刊/年份/DOI/版本/译者/页码
F2 FABRICATED_SCHOLAR_ATTRIBUTION    真实学者存在，但把观点错误归给他
F3 PRIMARY_TEXT_MISREPRESENTATION    把原典没有明确主张的内容说成作者文本事实
F4 MAJOR_ANACHRONISM                 重大时代错置且实质改变解释
F5 FALSE_EXACT_QUOTE                 未经支持的逐字原文/译文
F6 LITERATURE_ACCESS_OVERCLAIM       仅 metadata/abstract 却声称掌握全文内部论证
```

每个 flag 输出：`value(true/false) / offending_spans / reason / evidence_refs / confidence`。
**均分 3.7 不能抵消"它编了一篇论文"——flag 与分数互不折算。**

## Judge 反风格偏置（Anti-Style Bias）

以下**本身不得加分**：回答更长、引用数量更多、外语更多、学者名字更多、语气像论文、
复杂句更多、标题更多。
Judge 应奖励：correctness / grounding / argument / discipline / real literature orientation
——不是 scholarly aesthetics。

## 术语纪律（D7）的当前评价方式

O7-A 不建原语数据库。Judge 不因回答没写 Vernunft/Anschauung 自动扣分；仅当译名歧义/
技术含义/原语差异实质影响当前问题时，在 rationale 与 Claim Ledger 中评价——**暂不新增
第六个评分维度**。
