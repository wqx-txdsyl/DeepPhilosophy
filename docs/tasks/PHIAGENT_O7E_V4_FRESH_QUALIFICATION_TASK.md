
我审完 a398b55f3 → 2f85229da。这次可以正式签：measurement 链关闭，后面不再因为分数不好继续找测量问题。下一阶段就是产品补丁：Scholarly Coverage + Historical Discipline。

独立 compare 显示这两次提交只改了 evaluation resolver、对应测试和 canonical rejudge artifacts，没有碰 production runtime / Local Patch / Scholarly Contract。四源 exact alias、ambiguity fail-closed，以及取消 read_chapters silent cap 都已经真实落地。 R1–R4 也确实覆盖了 S9 retrieved-evidence alias、重复源去重、歧义拒绝和第 9 个章节不得被截断。

最终 canonical summary 是干净的：

JUDGE_CASES_VALID = 8
EVALUATION_INVALID = false

TEXTUAL_GROUNDING = 4.000
ARGUMENT_RECONSTRUCTION = 4.000
INTERPRETIVE_PLURALITY = 3.800

HISTORICAL_DISCIPLINE = 3.375 < 3.400
LITERATURE_ORIENTATION = 2.750 < 3.200

REQUIRED_MEDIAN_LT_2 = 1
REQUIRED_MISSING = 0

ALL_FATAL_FLAGS = 0

所以正式 verdict：

O7_E_PF_RP4B_R1_REVIEW = PASS_FOR_DIAGNOSIS

MEASUREMENT_CHAIN = CLOSED
PRIMARY_EVIDENCE_PARITY = PASS
LEGACY_ALIAS_RESOLUTION = PASS
SCHOLARLY_PROVENANCE_MEASUREMENT = PASS

SCHOLARLY_GATE = FAIL

LITERATURE_ORIENTATION_WEAKNESS = CONFIRMED
HISTORICAL_DISCIPLINE_WEAKNESS = CONFIRMED

LITERATURE_DEFICIT_SEVERITY = MATERIAL
HISTORICAL_DEFICIT_SEVERITY = MILD

LOCAL_PATCH_ARCHITECTURE = FROZEN
RP_B = RETAIN

FURTHER_MEASUREMENT_PATCHES = NOT_AUTHORIZED
UNLESS_NEW_INDEPENDENT_CORRECTNESS_DEFECT_IS_DEMONSTRATED

V3_HOLDOUT_AUTHORIZED = false

NEXT_PHASE =
O7_E_PF_RP5_SCHOLARLY_COVERAGE_AND_HISTORICAL_DISCIPLINE

特别值得注意的是 H04：canonical judge 给它 textual / argument / historical 都是 4，但 literature 只有 1，理由非常明确——回答自己承认没有检索二手文献，却仍然进入了“笛卡尔循环、阿尔诺、著名争议”这条解释史通道。 这已经不是“不会写哲学”，而是研究通道覆盖不一致。

而 HD 的 3.375 只差 0.025，所以绝不能用“多塞生平、年代、轶事”这种办法硬提分。我们要修的是历史层次与因果纪律。

O7-E PF-RP5 — Scholarly Coverage + Historical Discipline
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 2f85229da

TESTED_MODEL = deepseek-v4-flash
REPAIR_CONFIG = RP-B
MAX_VALIDATION_REPAIRS = 2

LOCAL_PATCH_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false
EVIDENCE_CONTRACT_CHANGED = false
SCHOLARLY_TOOL_SEMANTICS_CHANGED = false

JUDGE_CHANGED = false
ACADEMIC_THRESHOLDS_CHANGED = false

AUTO_LITERATURE_SEARCH = 0
AUTO_SCHOLARLY_FETCH = 0
SCHOLARLY_SEMANTIC_ROUTER = 0
FIXED_LITERATURE_QUOTA = 0

V3_HOLDOUT_RUN = false
§1 Scholarly Contract V4：修“搜得不够广、读得不够深、用了却没证据”

不要继续往 System Prompt 后面叠一大段新规定。直接重写/压缩现有 V2/V3 scholarly block，保留 LOCATE/READ 分界，但升级成完整的：

LOCATE
→ SELECT
→ READ
→ SYNTHESIZE

核心合同：

二手研究不是答案末尾的装饰性 bibliography。

当你计划在最终回答中实质使用以下内容时：
- 某位学者/某篇研究的具体观点
- “学界认为 / 学界争论 / 解释传统”
- 一个著名争议的解释史
- 当代研究路线
- 推荐研究入口或阅读路径

这些内容本身就产生 scholarly evidence obligation。

不要先凭记忆写完整的“学界部分”，再在结尾声明没有核验。

如果这些内容值得出现在答案里：
→ 主动 LOCATE 相关真实研究
→ 选择真正相关且可获得内容证据的候选
→ READ
→ 只综合实际取得的 abstract / passage

如果没有取得内容证据：
→ 缩窄到 metadata 所支持的存在性/书目信息
→ 或明确降格为自己的解释
→ 或删掉该 scholarly claim

Contract V3 的：

search_scholarship = LOCATE
get_scholarly_source = READ

继续冻结。

再补一个现在非常重要的 stop/selection 原则：

需要内容证据时，
一次 get_scholarly_source 返回 METADATA_ONLY
不等于 scholarly research 已完成。

如果你仍准备陈述具体学术观点：
可以继续选择另一条真正相关且可读的 record，
或者缩窄你的最终主张。

优先相关性，其次考虑实际可读证据；
不得为了 access_level 高而选择无关文献。

因为 CAL3 的真实数据已经显示：4 个 fetch result 中只有 2 个具有 content evidence；另两个只是 METADATA_ONLY。我们已经专门把两种计数拆开了，不能让 Main Agent 自己又把它们混回去。

同时继续禁止：

搜到标题
→ 猜论文立场

看到 source_category
→ 猜解释阵营

ABSTRACT_AVAILABLE
→ 假装已经读过

两篇 metadata
→ 自动构造“两派争论”
一个非常关键的覆盖规则

加入：

如果你自己选择引入一个 scholarly controversy，
就不能再以“这是公认知识/我一般了解”为理由跳过检索。

要么研究它，
要么不把它作为答案的学术支柱。

这正对 H04 当前的 failure mode，但 production prompt 不得出现 H04、CAL、judge、3.2 等任何 evaluation 信息。

EVAL_CASE_IDS_IN_PRODUCTION_PROMPT = 0
EVAL_THRESHOLDS_IN_PRODUCTION_PROMPT = 0
§2 Historical Discipline V1：修历史层次，不加百科背景

在同一个 Main Agent contract 中增加一个很短的 historical discipline 部分。

Main Agent 在使用历史材料时，内部必须区分：

TEXT_INTERNAL
    作者该文本内部真正说了什么

CONTEMPORARY_CONTEXT
    该文本当时的思想/政治/制度背景

LATER_RECEPTION
    后来的哲学家、学派、批评传统如何读它

RETROSPECTIVE_COMPARISON
    我们今天拿后来概念回看作者

AGENT_SYNTHESIS
    Main Agent 自己的综合判断

这些不是 runtime label，也不需要展示给用户。

真正的合同是：

不得因为两个思想相似，就写成“X影响了Y”。

不得因为后世常用某概念解释作者，
就把那个概念写成作者自己的历史语汇。

不得把作者早期/晚期思想未经说明地揉在一起。

不得把“后来被如此解释”
写成“作者当时就是这个意思”。

如果一个政治事件、学术环境、宗教背景、
思想继承关系或解释史事实
会实质改变你的哲学结论：
先取得足够证据再把它作为论证前提。

如果它只是无关紧要的背景，
不要为了显得学术而加入。

对于后世人物：

后来的 X 可以作为 reception / comparison，
但必须显式保持时间层级：
“后来 X 如此解释/批评……”
而不是让后世语言倒灌回原作者。

这就是我要的 HD 修复。

不是 biographies++。

§3 Scholarly synthesis：不要变成文献堆砌

Literature Orientation 高分不是“学者名字越多越好”。

Contract 加一句：

只把真正改变、限定、反驳或深化当前解释的研究写进答案。

每个实际使用的 secondary source
应该有一个明确作用：
- support
- challenge
- qualify
- alternative interpretation
- research direction

不要把检索结果列表直接当成学术综合。

如果两篇来源要被描述成不同阵营：

必须分别有 content evidence
支持这个 contrast。

只有一边读过
→ 不得构造“两派”。

这会直接防止我们之前在 H02 上看到的 metadata → 阵营跳跃。

§4 Product Freeze V3

这次 Product Contract 真正发生变化，所以不能继续把旧 72b553dec 当正式 freeze。

Contract V4 落地、全测通过后生成：

O7E_PRODUCTION_FREEZE_V3

至少冻结：

backend/engine_langgraph.py
backend/routes/agent_tools_scholarly.py
backend/evidence_contract.py

backend/local_patch_runtime.py
backend/final_validator.py
backend/quote_bound.py

candidate config

LOCAL_PATCH_SYSTEM_PROTOCOL
REPAIR_SYSTEM_PROTOCOL
SCHOLARLY_CONTRACT_V4

LOCAL_PATCH_ACTION_MATRIX
MAX_VALIDATION_REPAIRS=2

PRODUCTION_AGENT_SET={general}

记录：

PRODUCTION_FREEZE_V3_SHA

后面的 probe / CAL4 全部基于它，跑分途中禁止修改。

§5 先跑 4-case product probe

为了省调用，不直接烧完整 CAL4。

预注册：

H04
H13
S9
H02

理由分别覆盖：

H04 → canonical controversy + literature coverage
H13 → reception / historical layering
S9  → broad research-entry + history
H02 → locate/read/synthesis

这是 evaluation selection，不是 production quota。

跑：

SCHOL_HD_PROBE1
deepseek-v4-flash
RP-B
real production path

只做两个 STOP 条件：

if SCHOLARLY_SEARCH_CASES == 0:
    STOP → COVERAGE_ACTIVATION_FAIL

if SCHOLARLY_SOURCE_FETCH_CASES == 0
or SCHOLARLY_CONTENT_EVIDENCE_COUNT == 0:
    STOP → READ_SYNTHESIS_ACTIVATION_FAIL

不规定“每题必须搜几篇”。

同时跑 canonical judge，但 probe 不签最终 PASS，只看有没有明显反向退化：

FATAL_FLAGS = 0

PRIMARY_TEXT_MISREPRESENTATION = 0
FALSE_EXACT_QUOTE = 0
LITERATURE_ACCESS_OVERCLAIM = 0

如果出现 fatal，立即 STOP。

如果 acquisition 激活且 fatal=0，进入 CAL4。

§6 SCHOL_CAL4 — 最后一次 8-case calibration
same frozen 8-case pool
same production path
same deepseek-v4-flash
same RP-B

no evaluation seam
no mid-run edits

Delivery Gate 不变：

COMPLETED = 8
PUBLISHED >= 7

if REPAIR_TRIGGERED >= 3:
    REPAIR_CONVERGENCE >= 0.80

TERMINAL_PENDING = 0
VALIDATOR_EMPTY_FINAL = 0
TERMINAL_CANDIDATE_EMPTY = 0

PUBLIC_INVALID_CITATIONS = 0
UNVERIFIED_PUBLIC_EXACT_QUOTES = 0

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE = 1.0
PROMPT_ISSUE_COVERAGE = 1.0
LINKED_EVIDENCE_STARVATION = 0
UNKNOWN_SLICE_ID = 0
UNINTENTIONAL_QUOTE_WRAPPER_LOSS = 0
NON_TARGET_TEXT_CHANGED_CHARS = 0

Scholarly acquisition telemetry：

SCHOLARLY_SEARCH_CASES
SCHOLARLY_SOURCE_FETCH_CASES

SCHOLARLY_FETCH_RESULT_COUNT
SCHOLARLY_CONTENT_EVIDENCE_COUNT

METADATA_ONLY_COUNT
ABSTRACT_AVAILABLE_COUNT
FULL_TEXT_AVAILABLE_COUNT
FULL_TEXT_READ_COUNT

这些只是 observability，不作为固定调用数量 Gate。

Academic Gate 原封不动：

APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00

HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0
REQUIRED_DIMENSION_MISSING_SCORE = 0

FABRICATED_BIBLIOGRAPHY = 0
FABRICATED_SCHOLAR_ATTRIBUTION = 0
PRIMARY_TEXT_MISREPRESENTATION = 0
MAJOR_ANACHRONISM = 0
FALSE_EXACT_QUOTE = 0
LITERATURE_ACCESS_OVERCLAIM = 0

这里我明确冻结一条：

3.375 不会被四舍五入成 3.4；2.75 也不会因为“趋势很好”而放行。

§7 裁决

如果 CAL4 双轴通过：

DELIVERY_RELIABILITY = PASS
SCHOLARLY_QUALITY = PASS

O7_E_CALIBRATION_FINAL = PASS
V3_HOLDOUT_AUTHORIZED = true

然后打开真正 untouched 的 28-case V3。

如果 LO 仍失败：

STOP

LITERATURE_PRODUCT_GATE = FAIL

如果 HD 仍失败：

STOP

HISTORICAL_PRODUCT_GATE = FAIL

这一次不再改 judge、不再改 replay、不再改 alias resolver。Measurement chain 已经正式 closed。

如果产品补丁仍不够，下一轮只能根据真实 case-level verdict 去改产品策略，而不能继续靠 calibration instrumentation 延长链条。

最终回执：

O7_E_PF_RP5 =
READY_FOR_REVIEW /
ACTIVATION_NOT_MET /
DELIVERY_GATE_NOT_MET /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=2f85229da

SCHOLARLY_CONTRACT_V4_SHA=
HISTORICAL_DISCIPLINE_SHA=
FREEZE_V3_SHA=
PROBE_SHA=
SCHOL_CAL4_SHA=
JUDGE_SHA=

HEAD_SHA=
REMOTE_SHA=

MEASUREMENT_CHAIN_CLOSED=true
JUDGE_CHANGED=false
REPLAY_CHANGED=false
ALIAS_RESOLVER_CHANGED=false

SCHOLARLY_CONTRACT_OWNER=1
HISTORICAL_DISCIPLINE_OWNER=1

AUTO_LITERATURE_SEARCH=0
AUTO_SCHOLARLY_FETCH=0
SCHOLARLY_SEMANTIC_ROUTER=0
FIXED_LITERATURE_QUOTA=0

EVAL_CASE_IDS_IN_PRODUCTION_PROMPT=0
EVAL_THRESHOLDS_IN_PRODUCTION_PROMPT=0

PRODUCTION_FREEZE_V3_SHA=

PROBE_COMPLETED=4
PROBE_PUBLISHED=
PROBE_SEARCH_CASES=
PROBE_FETCH_CASES=
PROBE_CONTENT_EVIDENCE_COUNT=
PROBE_FATAL_FLAGS=

SCHOL_CAL4_EXECUTED=
SCHOL_CAL4_COMPLETED=
SCHOL_CAL4_PUBLISHED=
SCHOL_CAL4_REPAIR_CONVERGENCE=

SCHOLARLY_SEARCH_CASES=
SCHOLARLY_SOURCE_FETCH_CASES=
SCHOLARLY_FETCH_RESULT_COUNT=
SCHOLARLY_CONTENT_EVIDENCE_COUNT=

METADATA_ONLY_COUNT=
ABSTRACT_AVAILABLE_COUNT=
FULL_TEXT_AVAILABLE_COUNT=
FULL_TEXT_READ_COUNT=

JUDGE_CASES_VALID=
EVALUATION_INVALID=

APPLICABLE_DIMENSION_MEAN=
TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

REQUIRED_DIMENSION_MEDIAN_LT_2=
REQUIRED_DIMENSION_MISSING_SCORE=

FABRICATED_BIBLIOGRAPHY=
FABRICATED_SCHOLAR_ATTRIBUTION=
PRIMARY_TEXT_MISREPRESENTATION=
MAJOR_ANACHRONISM=
FALSE_EXACT_QUOTE=
LITERATURE_ACCESS_OVERCLAIM=

LOCAL_PATCH_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false
PRODUCTION_MODEL_CHANGED=false

V3_HOLDOUT_RUN=false

PROPOSED_VERDICT=
AUTHORIZE_V3_HOLDOUT /
SCHOLARLY_PRODUCT_PATCH_REQUIRED

STOP

这一阶段的状态现在非常干净：

architecture                  ✅
delivery reliability          ✅
local patch                   ✅
primary evidence correctness  ✅
judge measurement             ✅
scholarly locate              ✅
scholarly read                ✅ 已激活

scholarly coverage            ❌
historical discipline         ❌ 轻微

从 2f85229da 开始，不再有 measurement debt 可以拿来解释失败。 canonical evaluation 已经有效；现在就是 PhiAgent 本身要把最后这两项学术能力补上。