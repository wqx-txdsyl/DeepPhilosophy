
我审完 c2f623444 → dd202e279。这轮方向可以定了：PF-RP3B 对 scholarly provenance 的接线成功，SCHOL_CAL1 的 delivery gate 确实失败；但“8 case 零 scholarly 调用”是有效诊断信号，足以正式确认下一刀应该打 Scholarly Contract，而不是继续改 Local Patch。

O7_E_PF_RP3B_REVIEW = PASS_FOR_DIAGNOSIS

SCHOLARLY_PROVENANCE_PIPELINE = PASS
DELIVERY_GATE = FAIL
ACADEMIC_JUDGE_SKIP = PASS

MAIN_AGENT_SCHOLARLY_TOOL_USE_INSUFFICIENT = CONFIRMED

LOCAL_PATCH_ARCHITECTURE = FROZEN
RP_B = RETAIN
LOCAL_PATCH_REOPEN = false

SCHOLARLY_PRODUCT_PATCH = AUTHORIZED

V3_HOLDOUT_AUTHORIZED = false

独立核对后，SCHOL_CAL1 的确是 6/8、repair convergence 0.714，同时 SCHOLARLY_SEARCH_CASES=0 / SOURCE_FETCH_CASES=0 / RECORD_COUNT=0 / EVIDENCE_COUNT=0。

而 plumbing 本身已经接通：search_scholarship 与 get_scholarly_source 已进入 canonical retrieval set，所以会进入 raw tool log、trace 和机械 budget；Evidence Contract 也新增了独立 scholarly provenance，并在 result_full 被剥离前生成 done.scholarly_sources。 General Agent 的工具集本来就是全部注册工具，而 O7-C 两个 scholarly tool 也确实已经注册，因此真实 8 case 的零调用不能再归因于“工具没挂上”。

更关键的是，当前 Scholarly Contract 明明已经规定：出现“某学者认为 / 某种解释传统 / 学界争论”时，文献存在性必须来自 search_scholarship / get_scholarly_source。 但 SCHOL_CAL1 的 H04 仍然直接写出“学界普遍注意到”“通行解读”等判断，同时整个 run 的 scholarly 调用为零。 所以这已经不是 plumbing 问题，而是 Main Agent 没把 secondary scholarship 当成独立研究通道真正执行。

不过在改 Scholarly Contract 前，我还发现两个很小但必须先关掉的 measurement hole。第一，当前 SCHOLARLY_EVIDENCE_COUNT 实际统计的是 SCHOLARLY_EVIDENCE_RECORD_IDS 数量；而 build_scholarly_provenance() 对每一次成功的 get_scholarly_source 都会生成一条 evidence entry，即使只是 METADATA_ONLY 或 FULL_TEXT_AVAILABLE、里面没有摘要和 passages。测试本身也明确允许这种“空 evidence entry”。 因此下一轮不能再拿 SCHOLARLY_EVIDENCE_COUNT 当“真正读到了内容”的计数。

第二，O7-C 的真实 model view 原本还提供 source_category / source_providers / retrieval_origin / bibliographic_verified_fields，但 PF-RP3B 投影时把这些字段丢掉了，只留下一个 provider 字符串。 随后 judge 又把所有 run-time scholarly records 直接追加进 SECONDARY_SOURCE_RECORDS。 当前零调用所以没污染本轮，但下一轮真的开始使用 scholarly tools 后，这些 provenance 字段必须保留下来。

下一步：O7-E PF-RP4 — Scholarly Acquisition Activation

这次终于允许改 Scholarly Contract，但只改 Main Agent 的学术研究策略，不新增 Python semantic router，不自动搜文献，不设“必须搜 N 篇”的配额。

IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = dd202e279

MODEL_UNDER_TEST = deepseek-v4-flash
REPAIR_CONFIG = RP-B
MAX_VALIDATION_REPAIRS = 2

LOCAL_PATCH_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false
SLICE_CATALOG_CHANGED = false

SCHOLARLY_SEMANTIC_ROUTER = 0
AUTO_LITERATURE_SEARCH = 0
SCHOLARLY_SUFFICIENCY_GATE = 0

V3_HOLDOUT_RUN = false
§1 — 先做机械 measurement closure

build_scholarly_provenance() 保留 O7-C model view 的这些字段：

source_category
source_providers
retrieval_origin
bibliographic_verified_fields

记录计数拆成：

SCHOLARLY_SOURCE_FETCH_CALLS
    = get_scholarly_source 实际执行次数

SCHOLARLY_FETCH_RESULT_COUNT
    = 成功返回 provenance 的 fetch 数

SCHOLARLY_CONTENT_EVIDENCE_COUNT
    = 真正存在可支持内容主张的记录数

其中：

METADATA_ONLY
→ content evidence = false

FULL_TEXT_AVAILABLE but not read
→ content evidence = false

ABSTRACT_AVAILABLE + nonempty returned abstract
→ content evidence = true

FULL_TEXT_READ + nonempty returned passages
→ content evidence = true

旧 SCHOLARLY_EVIDENCE_COUNT 不再模糊使用；要么删除，要么明确 alias 到 CONTENT_EVIDENCE_COUNT。

Judge 仍然 只能消费本 run provenance，不得事后查 registry。每条 scholarly record 要把 source_category 等 provenance 原样传过去，不准把 UNKNOWN/primary/reference 在 runtime 中自动“升级”为 secondary interpretation。

§2 — Scholarly Contract V2：从“禁止乱引”升级到“主动获取 scholarship”

现在的 E 条款主要是：

你一旦说某学者/学界，就必须有证据。

这只是一条 honesty constraint，不足以形成 literature-oriented research。

改成一个由 Main Agent 自己执行的研究判断：

Secondary scholarship is an independent research channel,
not merely a fallback after primary-text retrieval.

对于研究入口、解释争议、思想史定位、某论证的解释史、
学界分歧、阅读路径、当代研究状态等问题：

在形成最终答案前，主动判断：
“真实二手研究是否可能实质改变、限定或深化我的回答？”

若答案为是：
→ 自主调用 search_scholarship

若要陈述“某篇/某位学者具体主张了什么”：
→ 再调用 get_scholarly_source 获取实际内容证据

仍然禁止任何固定数目：

NO:
必须搜 2 篇
每题自动 literature search
出现某关键词 runtime 强制调用

YES:
Main Agent 根据研究价值自己决定搜什么、读什么、何时停止

再加两个重要冲突消解。

第一：

websearch != search_scholarship

websearch 可补背景事实；
但 scholarly identity / attribution / interpretation literature
优先使用 search_scholarship。

因为当前早期 System Prompt 明确写了“原典不足先 websearch”，这不能再被模型理解成“学术文献也用普通 web search 就行”。

第二：

“我自己知道这个学界观点”
不构成跳过 scholarly retrieval 的理由。

这是对 Phase-T tool-selection 原则的精确限定：对于可验证的书目身份、学者归因和文献内容，scholarly tools 提供的是模型记忆无法提供的 provenance，所以不属于“工具只是在重复我自己能写的 prose”。当前工具选择原则允许模型在认为自己能高质量完成时不调用，这很可能正是零调用的一个诱因。

同时规定：

如果本轮没有取得 scholarly evidence：
不得写成确定事实：
“学界普遍认为……”
“某学者证明/主张……”
“当前研究认为……”

可以：
明确写成 Agent 自己基于原典的解释，
或诚实说明本轮未核验相关二手文献。

这不是 validator gate，仍由 Main Agent 自己遵守。

§3 — 先跑小型 Activation Probe，别直接烧完整 8 case

预注册三个 calibration case：

H04
H07
H02

它们都是我们已经反复见过的、会触及解释史/二手研究价值的 case。

SCHOL_ACTIVATION_PROBE = 3 cases
same production path
deepseek-v4-flash
RP-B

这里只做诊断，不做最终产品分数。

要求：

COMPLETED=3
SCHOLARLY_PIPELINE_ERRORS=0
POSTHOC_REGISTRY_LOOKUP=0

SCHOLARLY_SEARCH_CALLS_TOTAL > 0

如果还是：

SCHOLARLY_SEARCH_CALLS_TOTAL=0

立即 STOP：

SCHOLARLY_CONTRACT_V2_ACTIVATION = FAIL

不要跑完整 8 case，也不要继续往 prompt 上堆十条规则；回来给我看三个 case 的真实工具选择轨迹。

如果 >0，才进完整 calibration。

get_scholarly_source 不设置死次数门，因为 metadata-only 的书目确认不一定需要读摘要；但报告：

SEARCH_CALLS
FETCH_CALLS
CONTENT_EVIDENCE_COUNT

让我看 Agent 到底停在哪一层。

§4 — 完整 SCHOL_CAL2

仍是同一 8-case calibration pool。

Delivery 先过：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

TERMINAL_PENDING=0
VALIDATOR_EMPTY_FINAL=0
TERMINAL_CANDIDATE_EMPTY=0

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0
UNKNOWN_SLICE_ID=0
UNINTENTIONAL_QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

如果 delivery fail：

STOP
SCHOL_CAL2_DELIVERY_GATE_NOT_MET

不要 judge，也不要回改 Local Patch。

如果 delivery pass，立即跑 canonical academic judge，学术门一个数字都不改：

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

这一次最有价值的不是只看 LO 总分，还要把 scholarly acquisition 链拆开：

SCHOLARLY_SEARCH_CASES
SCHOLARLY_SOURCE_FETCH_CASES
SCHOLARLY_UNIQUE_RECORD_COUNT
SCHOLARLY_CONTENT_EVIDENCE_COUNT

ACCESS_LEVEL_COUNTS:
METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ

不做 NAMED_SECONDARY_SOURCE_CLAIMS 的脆弱正则启发式。答案和 safe judge verdict 已经足够让我判断“搜了但没读 / 读了但没用 / 用了但综合差”，没必要再造一个 shadow semantic classifier。

最终回执：

O7_E_PF_RP4 =
READY_FOR_REVIEW /
SCHOLARLY_ACTIVATION_NOT_MET /
DELIVERY_GATE_NOT_MET /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=dd202e279

MEASUREMENT_CLOSURE_SHA=
SCHOLARLY_CONTRACT_V2_SHA=
PROBE_SHA=
SCHOL_CAL2_SHA=
JUDGE_SHA=

HEAD_SHA=
REMOTE_SHA=

SOURCE_CATEGORY_PRESERVED=true
SOURCE_PROVIDERS_PRESERVED=true
RETRIEVAL_ORIGIN_PRESERVED=true
BIBLIOGRAPHIC_VERIFIED_FIELDS_PRESERVED=true

SCHOLARLY_FETCH_RESULT_COUNT_SEPARATE=true
SCHOLARLY_CONTENT_EVIDENCE_COUNT_SEPARATE=true
METADATA_ONLY_COUNTS_AS_CONTENT_EVIDENCE=false
FULL_TEXT_AVAILABLE_COUNTS_AS_CONTENT_EVIDENCE=false

SCHOLARLY_CONTRACT_OWNER=1
AUTO_LITERATURE_SEARCH=0
SCHOLARLY_SEMANTIC_ROUTER=0
FIXED_LITERATURE_QUOTA=0

ACTIVATION_PROBE_COMPLETED=3
ACTIVATION_SEARCH_CALLS=
ACTIVATION_FETCH_CALLS=
ACTIVATION_CONTENT_EVIDENCE_COUNT=

SCHOL_CAL2_EXECUTED=
SCHOL_CAL2_COMPLETED=
SCHOL_CAL2_PUBLISHED=
SCHOL_CAL2_REPAIR_TRIGGERED=
SCHOL_CAL2_REPAIR_CONVERGED=
SCHOL_CAL2_REPAIR_CONVERGENCE=

SCHOLARLY_SEARCH_CASES=
SCHOLARLY_SOURCE_FETCH_CASES=
SCHOLARLY_UNIQUE_RECORD_COUNT=
SCHOLARLY_CONTENT_EVIDENCE_COUNT=

METADATA_ONLY_COUNT=
ABSTRACT_AVAILABLE_COUNT=
FULL_TEXT_AVAILABLE_COUNT=
FULL_TEXT_READ_COUNT=

POSTHOC_REGISTRY_JUDGE_LOOKUP=0

ACADEMIC_JUDGE_EXECUTED=

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

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_V3_HOLDOUT /
SCHOLARLY_PRODUCT_PATCH_REQUIRED /
DELIVERY_GATE_NOT_MET

STOP

所以现在可以把根因树正式缩到很小了：

O7-C retrieval capability        ✅
O7-D curated scholarly corpus    ✅
O7-E provenance plumbing         ✅

Main Agent actually uses it      ❌

而且这不是猜测。当前 canonical contract 已经要求 scholarly attribution 必须有真实文献记录，但真实 8-case run 依然是 0 search / 0 fetch。

下一刀就应该是 让同一个脑子真正学会把 scholarship 当研究材料使用，而不是再往 runtime 里造一个“检测到学界二字就自动搜论文”的第二大脑。