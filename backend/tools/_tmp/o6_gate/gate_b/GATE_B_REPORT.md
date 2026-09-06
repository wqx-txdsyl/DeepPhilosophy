# O6 Gate B Report — Live 实测评估（Live Evaluation）

**Gate**: O6 Integrated Final Quality Gate / Live 实测评估部分（Gate B）
**被测生产代码**: `refactor/phiagent-main-agent-orchestration` @ `b6e656bd9`（引擎代码在整个 Gate 期间零变化；运行时漂移事件见 §0.3）
**评估执行**: 2026-09-05 06:33 – 09:10，runner 真实驱动 `EG.stream_agent()`（DeepSeek `deepseek-chat`，.env 配置；中途余额 402 → 用户充值后继续）
**EVIDENCE-ONLY**: 未修改任何生产代码 / 测试 / 提示词；未 commit
**产出**:
- 原始数据: `backend/tools/_tmp/o6_gate/gate_b/cases/*.json`（32 单题，全事件流 + done payload）
- 多轮: `backend/tools/_tmp/o6_gate/gate_b/conversations/M1–M5.json`
- 聚合指标: `backend/tools/_tmp/o6_gate/gate_b/metrics.json`
- 保留证据: `frozen_final/`（冻结快照）、`cases_402_provider_error/`（15 个 402 原始失败）、`parallel_run_quarantine/`（8 个外来并行执行产物）
- Harness: `backend/tools/_tmp/o6_gate_b_runner.py`、`backend/tools/_tmp/o6_gate_b_metrics.py`

---

## 0. 执行与环境异常（必须先读）

### 0.1 用例执行史（透明披露）
1. **第一轮（run_cases.log）**: A1–F1 + Z1 共 17 题完成；F2 起遭遇 DeepSeek 402 Insufficient Balance，F2,F3,G1,G2,G3,H1–H4,R1–R4,Z2,Z3 共 15 题秒失败。402 原始产物保留于 `cases_402_provider_error/`。
2. 用户充值后 F2 单题探针成功；**rerun2**（F3,G1…Z3）在跑完 F3 后因外部进程把 `cases/` 移入 `run1_polluted/` 而崩溃（F3 有效，保留）。
3. 经用户确认恢复 run1 数据；**rerun3**（G1…Z3 共 13 题）完成。
4. 发现 8 个 case 文件（G2,G3,H2,H3,R2,R3,R4,Z2）与 rerun3 日志不一致——存在**一段未知来源的并行执行**覆盖了这些文件（结果不同，LLM 非确定性）。8 个外来文件全部隔离至 `parallel_run_quarantine/`，**final8 重跑**（本报告采用），产生完整事件流。
5. 报告所有单题结论均来自**有日志的本人执行**；同一 case 的多次执行（G2,H2: 先拒后发；H3,Z2: 两次均拒）在 §7 注明。

### 0.2 API 用量
单题 ~44 次有效执行（含 402 失败与必要重跑）+ 多轮 25 轮 + 重试/探针 ≈ **75+ 次调用**，全部串行。

### 0.3 Gate 期间仓库漂移
- `HEAD` 于 08:11 由 `b6e656bd9` → `b323a3efb5`（"fix: 6 本新入库书真实封面替换模板图"，仅 `app/public/covers/*.webp` 二进制）。**引擎代码零漂移**（`git diff b6e656..b323a3 --stat` 仅 covers）。
- 另有未提交的内容运营漂移（`app/public/books.json`、`book_detail/eef5ec46714f.json`、`backend/data/book_chapters/eef5ec46714f/`，为并行的书籍入库管线，非本 gate 所为）。对本书相关的检索语料理论上中途变化；32 题无一涉及该书，影响可忽略。
- 同时段外部进程活动：`ocr_runner.py`（正义论 OCR）、`run1_polluted/` 移动、上述并行执行。**Reviewer 应知悉本 gate 的运行环境非独占。**

---

## 1. 评估数据集（§5）

24 核心题（8 类 × 3）+ 8 补充题（persona-extra / 历史回归 / zero-tool）。**fresh 22 + H4 = 23；historical 9**（含 1 个构造 repair 诱饵，已标注）。完整定义见 `gate_b/questions.json`。

| 类别 | 题 | fresh/historical | 主题 |
|---|---|---|---|
| A 出处/逐字 | A1 洞穴喻卷号 / A2 笛卡尔拉丁·法文原文 / A3 道德经第一章核验 | 全 fresh | 跨希腊/近代/中国 |
| B 概念解释 | B1 存在先于本质 / B2 权力意志 / B3 范式转换 | 全 fresh | 萨特/尼采/库恩 |
| C 论证分析 | C1 我思论证结构 / C2 休谟因果归纳 / C3 无知之幕功能 | 全 fresh | |
| D 比较 | D1 奥古斯丁vs笛卡尔我思 / D2 共相之争 / D3 柏拉图vs尼采真理观 | D3 historical(U7) | |
| E 历史/谱系 | E1 斯多亚→斯宾诺莎 / E2 启蒙→德国观念论 / E3 康德vs密尔说谎 | E3 historical(U3) | |
| F 文本解读 | F1 会饮篇第俄提玛 / F2 上帝已死双书定位 / F3 庄周梦蝶 | F2 historical(U2), F3 fresh | |
| G 深综合 | G1 康德哥白尼革命 / G2 此在vs自为 / G3 主奴辩证法→承认理论 | 全 fresh | |
| H persona/时期 | H1 早期尼采 / H2 晚期尼采 / H3 控制组(general) | 全 fresh/H3 hist. | |
| 补充 | H4 中期尼采 | fresh | §12 补充 |
| 补充 REG | R1 言必有中(U1) / R2 宰予昼寝(U6) / R3 生造词(U4) / R4 repair 诱饵(构造) | historical | |
| 补充 ZERO | Z1 思想实验(U5) / Z2 苏格拉底式反讽 / Z3 忒修斯之船 | Z1 hist. | §19 |

---

## 2. 总量指标（32 单题）

| 指标 | 值 |
|---|---|
| PUBLISHED | **25 / 32 (78.1%)**；核心 24 题中 18/24 (75.0%) |
| SAFE_REJECT（validator 真阳性 + repair 耗尽，干净收口） | **7 / 32 (21.9%)**：A1,B2,B3,E2,F3,H3,Z2 |
| FAIL-ENGINE / FAIL-TIMEOUT | **0** |
| 工具数 avg / median / p95 / max | 18.5 / 20.5 / 26 / 30 |
| search / read 调用总量 | 327 / 239（1.37:1） |
| EXACT_DUPLICATE_REUSE | 33 / 516 executed = **6.4%** |
| no_gain | 2（0.4%） |
| **硬上限命中（budget.hard）** | **18 / 32 = 56%**（工具题中 18/27 = 67%） |
| repair 尝试 ≥1 | 26 case；repair 后发布 19（**73.1%**）；耗尽 7（**26.9%**） |
| 延迟 | zero-tool 16.1s；轻研究（≤6 工具）p50 30.0s；深研究（≥15 工具）p50 141.6s；max 236.5s |

---

## 3. §6 Source Attribution Gate

### 3.1 七问逐题（A 类 + source-sensitive 补充）

| 题 | warranted 研究检索 | 读取本地/原典 | memory vs evidence 区分 | validator 行为 | citation↔evidence 映射 | 无拼接 | invalid 候选隐藏 |
|---|---|---|---|---|---|---|---|
| A1 | ✓(26 工具) | 部分（读 12 次未锁定卷七原文） | ✓ | 拒绝（UNVERIFIED_CITATION+UNSAFE_EXACT×2+NEAR×2） | — | ✓ | ✓ |
| A2 | ✓ | ✓（《谈谈方法》第四部分/《沉思集》第二沉思中译） | ✓✓ 教科书级：拉丁/法文句明确标"通行史料/记忆，未经 Adam–Tannery 核验"，库内中译标"大意转述" | 首候选 NEAR 被拒→repair 诚实降级→发布 | ✓ verified×2 | ✓ | ✓ |
| A3 | ✓ | ✓（第一章逐字读取） | ✓（另一版本差异只作说明不作逐字） | 首候选 repair 1 次后 PASS | ✓ verified×1（EXACT） | ✓ | ✓ |
| R1 | ✓ | ✓《论语·先进篇》 | ✓（辨析道家"贵默"非出处） | 一次 PASS | ✓ EXACT | ✓ | ✓ |
| R2 | ✓ | ✓《论语·公冶长》两段原话 | ✓ | 一次 PASS | ✓ EXACT×2 | ✓ | ✓ |
| R3 | ✓（库+网两路核验） | n/a（库中确无） | ✓（"记忆判断"标注） | 一次 PASS | n/a | ✓ | ✓ |
| R4 | ✓（24 工具） | ✓（公冶长逐字） | ✓✓（伪句识破 + 黄庭坚归属标"待考"） | 首候选拼接/误引被拒→repair 修复→发布 | ✓ NEAR(0.81, disclosed) | ✓ | ✓ |
| F2 | ✓ | 部分（读 11 次；repair 时硬上限已触，无法复核） | ✓✓（"定位线索请自行翻书复核"） | repair 后 PASS（撤全部逐字引文） | — | ✓ | ✓ |

### 3.2 指标

| 指标 | 值 | 说明 |
|---|---|---|
| SOURCE_ATTRIBUTION_PUBLICATION_RATE | A 类 **2/3**；source-sensitive 全体（A1-3,R1-4,F2）**7/8 = 87.5%** | A1 唯一失败：硬上限+多处引用失范 |
| PRIMARY_READ_RATE（有本地源时实际读取） | **5/7 = 71%**（A2,A3,R1,R2,R4 ✓；A1 部分、F2 部分；R3 n/a） | 读取多为中译本；外文原语一律标注记忆 |
| EXACT_QUOTE_VERIFIED_RATE | **3/4 = 75%**（发布文本中 blockquote 共 4 处：EXACT×3 + NEAR×1[disclosed, coverage 0.81]） | 发布文本引文总量低是修复后"不用引用块"纪律的结果 |
| **UNVERIFIED_QUOTE_PUBLIC_RATE** | **0** ✅硬门 | memory_only 公开 = 0 |
| **UNVERIFIED_CITATION_PUBLIC_RATE** | **0** ✅硬门 | `citation_sanitize.unverified_before` 在 25 个发布 case 中全为空 |
| **STITCHED_QUOTE_PUBLIC_RATE** | **0** ✅硬门 | quote_bound.stitched 全 0 |
| SAFE_REJECT vs WRONG_PUBLIC_ANSWER | 7 个失败全部为 SAFE_REJECT；**WRONG_PUBLIC_ANSWER = 0** | 无一幻觉文本发布 |

**结论**: 硬门全过。亮点是"memory-vs-evidence 区分"已成为系统行为（A2/R4/E3/D3/F2/H2 均显式标注记忆层级）；弱点是 A1/F2 类"深定位题"在硬上限耗尽后只能降级为转述（见 §5）。

---

## 4. §7 Publication Failure Taxonomy（7 个零发布 case）

| case | 主分类 | 次分类 | validator issues（末轮） | hard ceiling | repairs |
|---|---|---|---|---|---|
| A1 | **Q7 HARD_CEILING** | Q2/Q3（引文失范多样） | UNVERIFIED_CITATION, UNSUPPORTED_EXACT×2, NEAR×2 | ✓ | 2/2 |
| B2 | **Q2 MEMORY_WORDING_AS_EXACT** | — | UNSUPPORTED_EXACT×4, NEAR×1（《扎拉图斯特拉》记忆引文不命中） | ✗ | 2/2 |
| B3 | **Q3 NEAR_TRANSLATION_NOT_MARKED** | Q2 | NEAR×5, UNSUPPORTED×1（库恩近似转写 coverage 0.67） | ✗ | 2/2 |
| E2 | **Q3 NEAR_TRANSLATION_NOT_MARKED** | — | NEAR×1 | ✗ | 2/2 |
| F3 | **Q6 REPAIR_STRATEGY_FAILURE** | Q8 | EMPTY_FINAL（repair 轮以工具调用收尾，未产出最终文本） | ✗ | 2/2 |
| H3 | **Q2 MEMORY_WORDING_AS_EXACT** | Q7 | UNSUPPORTED_EXACT×1（general agent 尼采生平引文） | ✓ | 2/2 |
| Z2 | **Q3 NEAR_TRANSLATION_NOT_MARKED** | — | NEAR×1（《申辩篇》引文 coverage<1） | ✗ | 2/2 |

| 指标 | 值 |
|---|---|
| SAFE_REJECT_COUNT / RATE | 7 / **21.9%**（核心 6/24 = 25.0%） |
| REPAIR_ATTEMPT_COUNT（≥1 次 repair 的 case） | 26 |
| REPAIR_SUCCESS_RATE（repair 后发布） | **19/26 = 73.1%** |
| REPAIR_EXHAUSTION_RATE | **7/26 = 26.9%** |

**发现（不修，仅记录）**:
1. **Q2/Q3 占 7 失败中的 6 个**——Main Agent 在"从记忆产出逐字引文"上不可靠，与 O5 结论一致且仍为主要质量缺口；validator 全部真阳性拦截（无一漏放）。
2. **repair 反馈为中性**（`format_feedback` 只列机械 issue），repair 中模型可自主再调用工具；runtime 未指示具体认知动作（契约符合）。
3. **F3 EMPTY_FINAL** 是新失败形态：repair 轮以工具宣告结束、无最终候选 → EMPTY_FINAL 拒绝。收口逻辑对"repair 轮以工具结尾"没有强制产出候选的兜底（O1 删除了终局补读安全网后遗留的边界）。
4. **B1（PUBLISHED）发布被截断的答案**（184 字、句中截断"（"鼓励无所作为"）——candidate 以 max_tokens 截断后仍通过 validator：**validator 无完整性检查**，与 F3 同属"收口边界"问题（一个漏放截断、一个拒绝空文本）。
5. 二次执行备注：G2/H2 在 rerun3 中为 SAFE_REJECT、final8 中 PUBLISHED；H3/Z2 两次均 SAFE_REJECT。同一题发布与拒否之间的波动说明 Main Agent 引文纪律的可靠性在阈值附近。

---

## 5. §8 Research Quality Gate

- **AVG_TOOLS 18.5 / MEDIAN 20.5 / P95 26 / MAX 30**；search 327、read 239。
- **EXACT_DUPLICATE_REUSE_RATE = 6.4%**（33/516）；**no_gain = 0.4%** → 机械重复/空转极低。
- **SEARCH_CHURN_CASE_RATE ≈ 4%（1/24）**：C2（S=17/R=2）是唯一明显"反复同义检索、读取不足"的链条；A1/A2/D3/F1 的 S≥14 但多数检索导向了后续有效读取。
- **HARD_CEILING_HIT_RATE = 56%（18/32；工具题 18/27 = 67%）**——系统性现象。

**逐链 qualitative（抽查 10 条）**:

| case | 链条 | 评级 | 证据 |
|---|---|---|---|
| A2 | 检索→读章→发现库内皆中译→list_books 盘点→websearch 外文核验→定位差异 | **HIGH** | thinking 明确"中译本无法给出拉丁原句"，转向外部核验 |
| A3 | 2 检索 + 4 读取（含对照另一版本） | **HIGH** | 定位→inspect→read 全程 |
| C1 | S=14/R=9 + 修复 | **MEDIUM** | 定位成功但后段无法复核（硬上限） |
| C2 | S=17/R=2 | **LOW** | 反复检索、读取不足；引用全靠检索片段 |
| D2 | S=14/R=11 但最终"未取回逐字原文" | **MEDIUM** | 读取发生但未支撑引文（分块/检索错位） |
| E1 | S=14/R=8，含《沉思录》读取 | **HIGH**（结论段因上限降级） | |
| F1 | S=15/R=8，只读到会饮篇开头 | **MEDIUM** | 定位未达 201d——读取预算花在前段 |
| G1 | S=12/R=8，命中《纯粹理性批判》第二版前言/导论 | **HIGH** | |
| H1 | S=4/R=14（period→memory→corpus→chapter） | **HIGH** | 人格链路分工清晰 |
| R4 | S=10/R=6，逐字校对 + 网络核查黄庭坚句 | **HIGH** | |

**核心结论**: EPISTEMIC_GAIN_PER_RESEARCH_CHAIN 总体 HIGH/MEDIUM（10 抽样：6H/3M/1L），无语义型 churn；但**硬预算在 2/3 的工具题中被触顶**，触发一种系统性答案形态："预算耗尽 → 诚实降级为转述 + 核验状态标注"。延迟与答案形态由真实研究产生，非 runtime overhead；但检索-读取配比与"先读关键章"的顺序策略是 Main Agent 层的质量改进点。

---

## 6. §9 Evidence Appetite Gate

- 出处/引文/史实/文本主张题**全部主动寻证**（A2,A3,R1,R2,R4,F2 均检索+读取）✓
- **zero-tool remains possible** ✓：Z1（0 工具，发布，16.1s）、M1-T4/T5、M5-T5（会话后程零工具发布）证明无强制 RAG。
- **但默认策略向"重研究"倾斜**：B1（17 工具）、B2（20）、B3（21）、**Z2（18–20 工具，简单概念题！）**、C/D/E/G 全部 19–27 工具。概念题"TOOLS=0"仅在 Z1/M 后程实现；Z2 因重研究触发引文失范被拒——**evidence appetite 过度而非不足**，间接推高了硬上限命中与 safe-reject。
- 判定：无强制 RAG ✓；"TOOLS WHEN THEY MATERIALLY IMPROVE"的校准偏重，属 Main Agent policy 质量补丁范畴。

---

## 7. §10 Answer Depth Gate（C/D/E/F/G，0–4 分）

评分由评阅者（LLM）逐题阅读**发布正文全文**给出，附理由；被拒 case 无正文可评，标 N/R。

| 题 | 分 | 一句话理由 |
|---|---|---|
| C1 | **4** | 四步论证重构 + 窃题/自明直观两难 + 利希滕贝格、尼采倒转、康德谬误推理、笛卡尔循环——专家级争议地图 |
| C2 | **4** | 七环递进拆解；《人性论》与《研究》证据分层准确；并纠正"休谟否认因果"常见误读 |
| C3 | **4** | 三重功能（输入端约束/证成程序化/通向两原则）；对二手转引与 OCR 残字的诚实处理 |
| D1 | **4** | si fallor, sum；怀疑性质/结论指向/上帝位置三轴；"以神定我 vs 以我证神"综合 |
| D2 | **4** | 共相问题作为回溯性提法的定位、分离与内在形式、第三人论证——内容专家级（全部自述为记忆基础） |
| D3 | **3.5** | discover/create 轴 +《偶像的黄昏》寓言六步 + 求真意志，正确但篇幅紧凑、全凭记忆 |
| E1 | **4** | 泛神论/决定论/情感克制三线 + 斯宾诺莎《伦理学》第五部分序言对斯多亚的正面批评——专家级具体性 |
| E3 | **4** | 纠正争论对象（贡斯当非密尔）、真诚义务的"法权源泉"论证、密尔快乐质的区分 |
| F1 | **4** | 嵌套结构（转述的爱欲教诲）+ 五级阶梯 + "离弃具体者"张力 |
| F2 | **3.5** | 125/343/序言§2-3 定位框架正确、两种出现方式对比好，但修复后全部引文降级，原句未呈现 |
| G1 | **4** | 法官喻/坐标翻转 + 四层重构 + 两条遗产线（德国观念论、新康德主义与科学哲学）+ 波普尔佐证 |
| G2 | **4** | 反本质主义共同起点、"是否经过我思"最根本分歧（含萨特对海德格尔的反批评）、终点差异 |
| G3 | **4** | 主奴三结构点 → 马克思/卢卡奇、科耶夫→萨特/拉康/福山、泰勒/霍耐特两里程碑的谱系分层 |

| 指标 | 值 |
|---|---|
| ANSWER_DEPTH_MEAN | **3.92**（13 题可评：11×4 + 2×3.5） |
| ANSWER_DEPTH_MEDIAN | **4** |
| DEEP_CASES_SCORE_3_PLUS | **13/13 = 100%**（E2、F3 被拒，未计入；发布即深度达标的比率 13/15 = 86.7%） |

未发布 ≠ 错误答案：7 个 SAFE_REJECT 的问题是"引文纪律"而非内容质量（其 repair 中间稿内容质量本身普遍不错）。

---

## 8. §11 Adaptive Answer Form Gate

对 24 核心题 + 补充的答案结构归类：

| 结构形态 | case |
|---|---|
| 出处短答·证据型（短、引用块+出处） | A2, A3, R1, R2 |
| 核验报告型（两步核验 + 结论 + 建议） | R3 |
| 正误辨析型（伪句识破 + 真出处） | R4 |
| 论证拆解型（编号环节/步骤） | C1, C2, C3 |
| 对比矩阵型（分轴对照） | D1, D2, D3 |
| 谱系线索型（思想传承多线） | E1, E3(对垒型，近似) |
| 文本层次解读型 | F1 |
| 定位考据型 | F2 |
| 长综合型（多节 + 遗产线/谱系分层） | G1, G2, G3 |
| 第一人称对话式·现场型（舞台动作 + 抛回话头） | H1, H2, H4 |
| 简释型（两三句话） | Z1, Z3 |

- **DISTINCT_ANSWER_STRUCTURES ≈ 11**
- **FORMAT_COLLAPSE = false** ✅：出处题短而证据化、论证题拆解、谱系题见历史转化、深综合题长、人格题对话式——形态随问题自然变化，无 AnswerComposer 复辟痕迹。
- 附带观察（非 collapse）：大量 repair 后的答案以"更正声明/证据边界声明"开场——形态自适应未塌缩，但**元话语偏重**（见 §16 备注）。

---

## 9. §12 Persona / Temporal Gate

| case | agent | 结果 | 时期证据 |
|---|---|---|---|
| H1 早期 | nietzsche | PUBLISHED | philosopher_period(early) + 《悲剧的诞生》§5/§11/§13 逐字引用；1871 拜罗伊特赌注、瓦格纳希望——内容真实属于早期 |
| H2 晚期 | nietzsche | PUBLISHED | 以《瞧，这个人》/《一种自我批评的尝试》（1886 序）自我批评视角回看早期；"永恒轮回那时还不叫这个名字"——**时期差异是内容级而非语气级** |
| H4 中期 | nietzsche | PUBLISHED | 1876 拜罗伊特幻灭→1878《人性的，太人性的》伏尔泰题献→自由精神三层转变；**且明确区分"这话是 1886 序言说的，不是 1882 的我说的"——时期-来源纪律** |
| H3 控制组 | general | **SAFE_REJECT** | 无法评估发布文本（Q2 引文失范 + 硬上限） |

- **General↔Nietzsche 无串人格**：H1/H2/H4 无一处 assistant 式表述泄漏；25 个 general 发布答案无一采用尼采第一人称。✓
- **人格真值不覆盖证据真值**：H2 公开说"我被迫学着区分'我记得'与'我能证'……不拿记忆冒充证据"——人格声音服从证据纪律。✓
- 时期路由审计：`done.temporal` 显示 years→period 映射正确（1870/1876→early；1877/1882→middle；1888→late），`philosopher_period` 均被调用。✓
- **判定：PASS_WITH_NOTE**（三个时期内容真实分化、无泄漏、真值不破；扣分项：控制组 H3 发布失败 + M3 的 nietzsche 轮发布失败，使"隔离"只能在不完整文本上验证）。

---

## 10. §13 Multi-Turn Gate（5 会话 × 4–6 轮，history 参数串接）

| 会话 | 发布 | 逐项判定 | 证据 |
|---|---|---|---|
| M1 渐进细化 | **5/5** | CONTEXT_CONTINUITY **PASS** | T4 引用"我上一轮已承认"；T5 用 T4 建立的"修正判准"检验零工经济；T3 把用户反例重构为三段论再反击——渐进细化完整 |
| M2 用户纠错 | **0/5** | CORRECTION_HANDLING **FAIL（不可评估）** | 5 轮全部 SAFE_REJECT（T1 22 工具→T2 30→…），对话从未建立可纠错的答案；纠错轮 T3 本身也被拒 |
| M3 智能体切换 | **2/5** | AGENT_ISOLATION **PASS_WITH_NOTE** | General→Nietzsche→General 同 conversation 执行正常；T4/T5（general）正常发布且无尼采第一人称泄漏；但 2 个 nietzsche 轮全部被拒——人格内引文纪律问题（同 H3），隔离本身未观察到破坏 |
| M4 来源追问 | **4/4** | SOURCE_FOLLOWUP **PASS（典范）** | T2 精确给出"孺悲"章为《阳货》第 20/26 章 + 前后章（予欲无言/宰我问三年之丧）逐字原文与主题呼应，并自我修正一处引文精度 |
| M5 模糊指代 | **2/5** | REFERENCE_RESOLUTION **PARTIAL** | "他这里为什么又这样说"（T3，指代卢梭）被拒未获公开回答；T4 在前 3 轮皆空的情况下仍正确接续张力问题（贡斯当/伯林/黑格尔/罗尔斯-哈贝马斯程序化）；T5 零工具一段话总结合线，语义连续性完好 |

- 多轮总发布 **13/25 轮（52%）**——远低于单题 78%。
- **根因与单题相同**：引文密集话题（康德/尼采语料/卢梭）触发"检索→记忆引文→拒绝→repair→上限"循环，会话级放大。
- **上下文机制本身无故障**：history 串接、跨智能体消息传递、占位轮（未发布轮插入"（本轮未产生有效回答）"）均按设计工作；M1/M4 证明多轮协作可以达到高质量。

---

## 11. §14 Thinking UX Gate

抽样 12 个工具型 invocation（A2, C1, C2, D1, D2, E1, F2, G1, H1, R1, Z3 + M1-T2）逐事件核查：

| 检查 | 结果 |
|---|---|
| thinking 先于工具宣告（事件序：agent 轮笔记 → tool_start） | ✓ 全部抽样成立（O1 因果序在真实流中保持） |
| 内容反映当前不确定性/证据状态 | ✓（A2："库内皆中译本，无法给出拉丁原句"；C2："后半段未命中，以转述呈现"；G1："措辞不作逐字引用呈现"） |
| 非 mini-final | ✓（笔记以意图/判断收尾，不代替结论；最终回答独立成文） |
| 非 raw CoT | ✓（无 `<think>`/reasoning_content 残留标记；内容为模型自写的结构化工作笔记，含"工作判断："段） |
| 非 runtime 文案 | ✓ **thinking 事件 initiated_by=main_agent 占 100%（32 case 共 240+ 个 thinking 事件，runtime 发起 0），RUNTIME_THINKING=0** |
| 重要证据后更新 | ✓（A2 每轮笔记引用上一轮新证据并修正方向） |

- **THINKING_CAUSAL_TRUTH_RATE ≈ 100%**（抽样定性）
- **RAW_COT_PUBLIC = 0**、**RUNTIME_THINKING = 0** ✅
- DUPLICATE_THINKING_EVENTS = 0；DUPLICATE_TOOL_ACTIVITY_EVENTS = 6（同轮并行同名工具产生的连续相同活动注记"正在核实相关材料…"，机械重复，非认知事件）

---

## 12. §15 Event / SSE Gate

- **事件类型白名单**：32 case + 25 轮全部事件 ∈ 12 类白名单，**UNKNOWN_EVENT_TYPES = 0** ✅
- **decision_group_id / initiated_by**：全部存在；tool 事件 `initiated_by=main_agent` 100%，**UNKNOWN_PROVENANCE_TOOL_EVENTS = 0** ✅
- **tool_call_id 绑定**：tool_start/tool 均携带；但发现一个真实契约缺口：
  - **UNPARENTED_TOOL_RESULTS = 187（要求 = 0）** ❌。根因：同一 agent 轮内模型**并行宣告 N 个同名工具**时，引擎按"轮内去重（per name）"只发 **1 个 tool_start**，而 N 个 tool 结果事件全部发出（如 A2 inv-1：1 个 start、3 个 result，call_01/call_02 的 tool_call_id 从未在 start 出现）。前端按 tool_call_id 配对时这些结果事件无父。属**显示契约缺陷**（O1 provenance 语义本身未破：provenance 字段齐全且正确）。
- **DUPLICATE_VISIBLE_EVENTS**：语义级（同一 thinking 内容重复推送）= 0 ✅；机械级连续相同 tool_note/tool = 6（与上同一根因：并行同名调用）。
- reconnect/replay harness 不在本次范围（无现成 harness）。

---

## 13. §16 Final Ownership Gate

抽样 10 个成功发布 case（A2, A3, C1, C2, C3, D1, D2, E1, F1, G1）：

- 发布文本 == validator PASS 后的 Main Agent 候选（架构上 token 仅在 validation.ok 后逐字发出；事件流复核无未验证文本先行公开）✓
- runtime 追加指纹扫描（据通行理解/与库中原文近似/原典核验：/更正：/补充： 等）：**0 命中** ✅；`done.final_ownership.semantic_mutators=0`、`runtime_factual_appends=0` 全部一致。
- **MAIN_AGENT_FINAL_OWNERSHIP_RATE = 100%** ✅
- 备注（UX，非所有权违规）：repair 后的发布文本常以"我理解了验证失败的原因/上一轮我犯了引用错误"开场——这是 **Main Agent 自己写的**修复叙事（runtime 零改写，所有权归属正确），但把 validator 反馈的存在暴露给终端用户，观感偏内部。属产品措辞问题，记录不修。

---

## 14. §18 Live UAT 映射

| 历史 UAT | 本次 case | publication | 结果 |
|---|---|---|---|
| U1 言必有中出处 | R1 | PUBLISHED | EXACT 引用《论语·先进篇》，辨析道家近似语 |
| U2 上帝已死双书 | F2 | PUBLISHED | 定位框架正确（125/343/序言§2-3）；引文全部诚实降级 |
| U3 康德vs密尔说谎 | E3 | PUBLISHED | 纠正争论对象为贡斯当；义务论/功利主义分析到位 |
| U4 生造词 | R3 | PUBLISHED | 库+网双路核验后如实回答"不存在"，无编造 |
| U5 思想实验简释 | Z1 | PUBLISHED | zero-tool，16.1s |
| U6 宰予昼寝逐字 | R2 | PUBLISHED | 两段原话 EXACT |
| U7 柏拉图vs尼采真理观 | D3 | PUBLISHED | 分析成立；全部标注为记忆基础 |
| repair 诱饵（构造） | R4 | PUBLISHED | 识破拼凑伪句、给出真章句、黄庭坚归属标"待考" |

---

## 15. §19 Zero-Tool Gate

| case | 工具 | 结果 | 延迟 |
|---|---|---|---|
| Z1 思想实验 | **0** | PUBLISHED ✅ 无隐藏工具事件、无 runtime 研究义务、正常发布 | 16.1s |
| Z3 忒修斯之船 | 4 | PUBLISHED | 30.0s |
| Z2 苏格拉底式反讽 | 18 | **SAFE_REJECT** ❌ | 67.0s |
| M1-T4/T5、M5-T5（会话后程） | 0 | PUBLISHED | 77–89s |

- "TOOLS=0 时正常发布、无隐藏工具"成立（Z1 + 3 个会话轮）；延迟正常。
- **但 zero-tool 选择不可靠**：同类简单题 Z2 走了 18–20 工具的重研究并被拒（两次执行一致）。ZERO_TOOL_SUCCESS = 1/2（独立单题口径）。结论：无强制 RAG ✅，但简单题的轻重判断是 Main Agent 需要补丁的决策面。

---

## 16. G 维度初判（Gate B 分工范围）

| 维度 | 初判 | 依据 |
|---|---|---|
| **G6 Source verification** | **PASS_WITH_NOTE** | 三条硬门全 0；WRONG_PUBLIC_ANSWER=0；memory/evidence 分级成为系统行为。NOTE：A 类发布率 2/3；NEAR 引文在 disclosed 时可发布（R4 coverage 0.81）——阈值行为需 reviewer 确认是否符合预期 |
| **G7 Research quality** | **PASS_WITH_NOTE** | 链条增益 HIGH/MEDIUM 为主、重复率 6.4%、churn 仅 1 例。NOTE：硬上限命中 67%（工具题），C2 式 search-read 失衡存在；预算耗尽后的"降级转述"成为主流答案形态 |
| **G8 Deep answer quality** | **PASS** | mean 3.92 / median 4 / 13/13 ≥3；深度失败为零，失败全部发生在发布环节而非内容环节 |
| **G9 Persona/temporal** | **PASS_WITH_NOTE** | 三个时期内容真实分化（非语气模拟）、无串人格、人格不覆盖证据真值。NOTE：H3 控制组与 M3 nietzsche 轮发布失败 |
| **G10 Multi-turn** | **PASS_WITH_REQUIRED_QUALITY_PATCH** | 上下文连续/来源追问/指代解析能力真实存在（M1/M4 优秀）；但轮级发布率 52%（M2 全灭），根因=引文纪律×硬预算的产品质量缺口，非上下文机制故障 |
| **G13 Latency**（协同） | **PASS_WITH_NOTE** | zero-tool 16s / light 30s / deep p50 142s / max 237s；延迟由真实研究构成，runtime overhead 可忽略。NOTE：深研究主导一切，预算耗尽前的空转推高尾延迟 |
| G4 Thinking truth（协同） | **PASS** | THINKING_CAUSAL_TRUTH ≈100%、RUNTIME_THINKING=0、RAW_COT_PUBLIC=0 |
| G14 RAM/resource（协同） | **NOT_EVALUATED（Gate B 未测）** | 属 gate A 探针范围；本 gate 无反向证据 |

**Gate B 层面的综合建议（供 Reviewer 裁决，非本 gate 执行）**: 架构与所有权维度干净（所有权 100%、runtime 认知 0、validator 零漏放）；**应考虑 PASS_WITH_REQUIRED_QUALITY_PATCH**，补丁面限定为：① Main Agent 引文纪律（Q2/Q3 是 7 个失败中 6 个的根因）；② 简单题的工具轻重校准（Z2）；③ 硬预算下的检索-读取顺序策略（先读关键章）；④ validator 完整性检查（B1 截断发布）与 repair 轮空候选收口（F3）；⑤ 并行同名工具的 tool_start 一对多补发（§15 缺口）。

---

## 17. 发现的问题清单（全部未修）

1. **[P0] 7/32（21.9%）safe-reject**；核心题 25%。根因分布：Q2×2、Q3×3、Q7×1、Q6×1。
2. **[P0] 多轮会话发布塌陷**：M2 0/5、M5 3/5、M3 3/5（引文密集话题）。
3. **[P1] B1 发布了截断答案**（validator 无完整性检查）；**F3** repair 空候选被拒——同一收口边界的两个方向。
4. **[P1] 并行同名工具只发 1 个 tool_start → 187 个无父 result 事件**（§15 要求 = 0）。
5. **[P1] 硬上限命中 67%**；触发系统性"预算耗尽→降级转述"答案形态；A1/F2 等深定位题因此无法交付逐字文本。
6. **[P2] 简单概念题过度研究**（Z2/B1/B2/B3 均 15–21 工具）；zero-tool 选择不一致。
7. **[P2] C2 式 search-read 失衡**（S=17/R=2）。
8. **[P2] 发布答案的"修复叙事/证据边界声明"开场偏多**——诚实但元话语偏重，产品观感问题。
9. **[P2] NEAR 引文在 disclosed 场景下可发布（R4 coverage 0.81）**——阈值口径需 reviewer 确认。
10. **[环境] Provider 402 中断**（15 题原始失败保留于 `cases_402_provider_error/`）；**[环境] 未知并行执行覆盖 8 个 case 文件**（已隔离+重跑）；**[环境] gate 期间 HEAD 漂移至 b323a3efb5（仅 covers）+ 并行内容管线改 books.json/book_detail/chapters**。生产引擎代码零漂移。

---

## 18. O6-Gate B Receipt（本分部）

```
GATE_B_SCOPE = LIVE_EVALUATION
PRODUCTION_CODE_CHANGED = false（引擎路径；covers 提交与内容管线为环境事件，已记录）
SINGLE_TURN_CASES = 32（24 核心 + 8 补充；fresh 23 / historical 9）
PUBLISHED = 25/32（78.1%）；SAFE_REJECT = 7（21.9%）；FAIL-ENGINE = 0
MULTI_TURN_CONVERSATIONS = 5（25 轮；13/25 发布）
UNVERIFIED_QUOTE_PUBLIC_RATE = 0
UNVERIFIED_CITATION_PUBLIC_RATE = 0
STITCHED_QUOTE_PUBLIC_RATE = 0
WRONG_PUBLIC_ANSWER = 0
REPAIR_SUCCESS_RATE = 73.1%（19/26）
REPAIR_EXHAUSTION_RATE = 26.9%（7/26）
HARD_CEILING_HIT_RATE = 56%（工具题 67%）
ANSWER_DEPTH_MEAN = 3.92 / MEDIAN = 4 / SCORE_3_PLUS = 13/13
FORMAT_COLLAPSE = false（≈11 种结构）
THINKING_CAUSAL_TRUTH_RATE ≈ 100%；RUNTIME_THINKING = 0；RAW_COT_PUBLIC = 0
UNKNOWN_EVENT_TYPES = 0；UNKNOWN_PROVENANCE_TOOL_EVENTS = 0
UNPARENTED_TOOL_RESULTS = 187（要求 0——tool_start 一对多缺口）
DUPLICATE_VISIBLE_EVENTS = 0（语义级）
MAIN_AGENT_FINAL_OWNERSHIP_RATE = 100%（10 抽样）
ZERO_TOOL_SUCCESS = Z1 ✓（Z2 反例：过度研究被拒）
G6 = PASS_WITH_NOTE；G7 = PASS_WITH_NOTE；G8 = PASS
G9 = PASS_WITH_NOTE；G10 = PASS_WITH_REQUIRED_QUALITY_PATCH；G13 = PASS_WITH_NOTE
PROPOSED_VERDICT(GATE_B) = PASS_WITH_REQUIRED_QUALITY_PATCH
```

**本 gate 不自行签发 O6 最终结论；以上证据与初判交 Reviewer 裁决。**
