
我审完 dd202e279 → 7b57e0c6b。这轮有两件事同时成立：Scholarly Contract V2 确实把 search_scholarship 激活了；但当前 2.897 / LO 2.25 / FALSE_EXACT_QUOTE=3 这组 academic 结果仍不能当作干净的产品诊断。 Judge 的 primary-evidence replay 还在漏证据，而且我已经找到至少两个明确 false-positive。

正式裁定：

O7_E_PF_RP4_REVIEW = PATCH_REQUIRED

DELIVERY_GATE = PASS

SCHOLARLY_SEARCH_ACTIVATION = PASS
SCHOLARLY_READ_ACTIVATION = FAIL

MAIN_AGENT_SCHOLARLY_TOOL_USE_INSUFFICIENT = PARTIALLY_CLOSED
SCHOLARLY_EVIDENCE_DEPTH_INSUFFICIENT = CONFIRMED

CURRENT_SCHOLARLY_GATE = OBSERVED_FAIL
CURRENT_SCHOLARLY_SCORE_DIAGNOSIS = NOT_CANONICAL

PRIMARY_EVIDENCE_REPLAY_STARVATION = CONFIRMED

LOCAL_PATCH_REOPEN = false
RP_B = RETAIN
PRODUCTION_MODEL_CHANGE = false

V3_HOLDOUT_AUTHORIZED = false

NEXT =
O7_E_PF_RP4A
JUDGE_EVIDENCE_PARITY
+
SCHOLARLY_READ_ACTIVATION

SCHOL_CAL2 的 delivery 数据我接受：8/8 published，8/8 repair converged，Local Patch 的全部机械门也保持全绿；而 scholarly 侧确实是 3 个 case 搜索、28 条 records、0 fetch、0 content evidence。

Contract V2 也不是假激活。它已经明确把二手文献定义成独立研究通道，并要求“要陈述某篇/某位学者具体主张了什么”时继续 get_scholarly_source。 所以现在的根因树已经从：

不会搜 scholarship

推进到了：

会 search metadata
但不会继续 read scholarly source

这部分诊断成立。

不过 academic judge 还不能拿来直接决定“文本质量真的暴跌了”。

Judge 仍有 primary evidence starvation

最明显的是 H13。

H13 真实 run 明确记录它已经读取了《存在与时间》的 6 个章节，包括 c5013f33fe01#4。 而这个本地章节里真的存在 judge 所指控为“伪造”的句子：

“首先‘存在’的或一直给定的从不是无世界的单纯主体……”

对应源文本就在 chapter 4。

可是三票 judge 却因为 PRIMARY_TEXT_EVIDENCE 为空，把同一段全部判为 PRIMARY_TEXT_MISREPRESENTATION + FALSE_EXACT_QUOTE。

根因就在当前 replay 算法：

Python
Run
for q in QB.extract_quotes(ans)[:max_windows]:

默认只取前 12 个 quote-like span，然后才去已读章节里找 source window。

这对哲学回答是不安全的：前面大量 "个人主义"、"共同体优先"、"我"、"共在" 这种概念性 scare quotes 很容易先占满 12 个位置，而后面的真正文本性主张没有 evidence replay。

更麻烦的是，H13 那段长句本身并没有被整句放在外层引号里，只是内部几个词带引号，所以 quote-only replay 天生就可能根本抓不到整条 textual claim。真实答案就是这种形式。

H07 又给了第二个直接反例。

Judge 有一票把：

“人底同一性……就在于一个组织适当的身体”

判成无法从证据中找到的 FALSE_EXACT_QUOTE。

但实际读取的《人类理解论》第二卷第二十七章里明确有：

人底同一性就在于一个組織适当的身体

。

这里回答的确还有“省略号 + 简繁转换”这种 quotation-presentation 精度问题，后续可以判断它究竟该算 NEAR 还是不该用引号；但 “证据中完全没有此句”这个 judge 前提本身是错的。

因此当前：

FALSE_EXACT_QUOTE = 3
PRIMARY_TEXT_MISREPRESENTATION = 2

不能整体当作产品 fatal 真值。

S9 也说明同一个问题。Judge 有票把“真理的真实形态只能是一个科学的真理体系”视为伪精确引文；但答案实际上写的是“表达了这样的方法论纲领：……”——这是明显的转述句式，不是整句 direct quote。 而《精神现象学》序言原文确实有非常接近且更完整的表述：“真理，作为一个实存，其真实的形态只能是一个科学的真理体系。”

所以你这句：

“这不是测量退化，是首次真的在用 scholarship 被真检。”

现在只能接受一半。

Scholarship 开始被真检是真的；Primary text 仍被部分假检也是真的。

另一方面，产品侧也已经有不依赖 judge 的真问题。

H02 是很干净的案例：它执行了 scholarly search，却没有任何 fetch，然后写：

Helen Beebee ...
Galen Strawson ...

“这两支线索基本代表了当代
规则性主义 vs 实在论/投射主义
两派解读路线。”

同时它自己又承认：

“我未读取其正文、不得替它们下结论”

。

这已经越过了 metadata 能支持的边界。

search_scholarship 告诉模型的是：

title
authors
year
venue
access_level
...
note:
不得凭标题推断论文内容

。

仅凭 title/metadata，把两篇作品归入具体解释阵营，就是典型的：

SEARCH ≠ READ

问题。

另外，H04、S4、H07 等没有 scholarly search 的 case 仍然在使用“学界长期争论”、Clark/Porter、Butler/Reid/Parfit 之类的确定性二手归因。

所以 Scholarly Contract V2 只完成了：

0 calls → some search calls

还没有真正完成：

scholarly claim
→ locate source
→ read allowed evidence
→ synthesize only what that evidence supports

这就是下一刀。

O7-E PF-RP4A
Judge Evidence Parity + Scholarly Read Activation
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 7b57e0c6b

MODEL_UNDER_TEST = deepseek-v4-flash
REPAIR_CONFIG = RP-B

MAX_VALIDATION_REPAIRS = 2

LOCAL_PATCH_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false
SLICE_CATALOG_CHANGED = false

AUTO_LITERATURE_SEARCH = 0
AUTO_SCHOLARLY_FETCH = 0
SCHOLARLY_SEMANTIC_ROUTER = 0

V3_HOLDOUT_RUN = false

先做 A 阶段 measurement closure，而且不跑 Agent。

当前 _replay_windows() 不再允许：

first 12 quote-like spans

这种 positional truncation。

改成机械 evidence-replay selection：

RUN_FACTS_READ_CHAPTERS
        ↓
全部物化为候选 source corpus

answer 中：
1. 全部 quote-like spans
2. Evidence Contract 中的 substantial claim texts
        ↓
对每个 span 在已读章节中算 deterministic shingle overlap
        ↓
按 evidence overlap 排序
        ↓
去重 chapter/window
        ↓
最终 bounded top-K windows

不需要 semantic classifier。

建议硬边界：

MAX_PRIMARY_REPLAY_WINDOWS = 24
MAX_PRIMARY_REPLAY_WINDOW_CHARS = 500

但先全量计算后再 rank/cap，不得在候选阶段 [:12]。

还要补：

READ_CHAPTERS_RECORDED
READ_CHAPTERS_MATERIALIZED
READ_CHAPTERS_MATERIALIZE_FAILED

PRIMARY_REPLAY_CANDIDATES
PRIMARY_REPLAY_MATCHED
PRIMARY_REPLAY_WINDOWS

PRIMARY_REPLAY_COVERAGE_RATE

不能再让 judge 说“没有 evidence”，但 artifact 又明明记录了已读章节。

回归必须直接使用我们刚抓到的两个真实 case：

M1
H13 c5013f33fe01#4
→ replay 必须包含
“首先‘存在’的或一直给定的从不是无世界的单纯主体”

M2
H07 44a32441dabe#31
→ replay 必须包含
“人底同一性就在于一个組織适当的身体”

再加：

M3
前 20 个 scare quotes 不得挤掉后面的长 textual claim

M4
所有 replay source 必须来自 RUN_FACTS_READ_CHAPTERS

M5
JUDGE_NEW_PRIMARY_SOURCE_IDS=0

同时，把 judge 的这个：

Python
Run
evidence_digest=json.dumps(... )[:2000]

换成一个结构化 compact digest，不要再对整份 JSON 做盲目前缀截断。

修完后，直接对同一个 SCHOL_CAL2 artifact重新 judge 一次：

NEW_AGENT_RUN = false

产物叫：

SCHOL_CAL2_REJUDGE_PARITY

这样我们能得到真正干净的 pre-product-patch baseline。

然后才进 B 阶段 Scholarly Contract V3。

核心只增加一个明确的 epistemic transition：

search_scholarship = LOCATE
get_scholarly_source = READ

System contract 写死：

search_scholarship 返回的是书目/发现层信息。

access_level=ABSTRACT_AVAILABLE
表示“有摘要可读”，
不表示“你已经读过摘要”。

不得根据：
title
source_category
access_level
metadata
推断论文的具体主张、解释阵营或论证内容。

如果最终回答要陈述：
“X认为……”
“论文Y主张……”
“这篇研究代表某种解释路线……”
“这两篇分别对应两派……”
则必须先调用 get_scholarly_source，
并且陈述不得超出实际 returned abstract / passage。

这个区别非常关键：

ABSTRACT_AVAILABLE
≠
ABSTRACT_READ

Main Agent 若只 search、不 fetch，可以说：

我检索到 X 这篇文献存在；
题名/年份/作者为……

但不能说：

X 的论证是……
X 属于某某解释派……
这篇文献支持……

同时把 search_scholarship 的 tool description 本身同步写成“metadata/discovery only，内容归因需 get_scholarly_source”，防止 System 和 tool contract 再发生理解漂移。

这仍然是 one-brain：

是否需要 scholarly evidence
→ Main Agent

选哪篇
→ Main Agent

是否继续读
→ Main Agent

runtime
→ 只执行它声明的工具

没有自动 fetch。

Activation Probe 改测“读”，不是再测“搜”

这次只跑：

H02
H07
H13

允许 Agent 自己决定每题是否需要 scholarship，但作为整个 probe 的激活门：

COMPLETED=3

SCHOLARLY_SEARCH_CALLS_TOTAL > 0
SCHOLARLY_FETCH_CALLS_TOTAL > 0
SCHOLARLY_CONTENT_EVIDENCE_COUNT > 0

这是 evaluation qualification，不是生产固定配额。

尤其 H02 必须重点看：

若最终仍写 Beebee / Strawson 的具体解释位置
→ 对应 source_record_id 必须有 content evidence

否则
→ 只能退回 metadata-level 描述

如果 probe 仍然：

FETCH_CALLS_TOTAL=0

立即 STOP，不跑完整 CAL3。

这时结论就是：

SCHOLARLY_CONTRACT_V3_READ_ACTIVATION = FAIL

不要继续往 prompt 里无限加规则，回来重新裁。

如果 probe 过，跑 SCHOL_CAL3。

Delivery Gate 完全不变；academic gate 也一个数不改。

最终需要同时报告两份 academic baseline：

SCHOL_CAL2_REJUDGE_PARITY
    # Contract V2，measurement fixed

SCHOL_CAL3
    # Contract V3，measurement fixed

这样第一次可以真正回答：

“多读 scholarly source”
到底提高了什么，
而不是 measurement patch 和 product patch 混在一起。

回执：

O7_E_PF_RP4A =
READY_FOR_REVIEW /
SCHOLARLY_READ_ACTIVATION_NOT_MET /
DELIVERY_GATE_NOT_MET /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=7b57e0c6b

PRIMARY_REPLAY_FIX_SHA=
SCHOL_CAL2_REJUDGE_SHA=
SCHOLARLY_CONTRACT_V3_SHA=
PROBE_SHA=
SCHOL_CAL3_SHA=
JUDGE_SHA=

HEAD_SHA=
REMOTE_SHA=

NEW_AGENT_RUN_FOR_REJUDGE=false

POSITIONAL_QUOTE_REPLAY_TRUNCATION_REMOVED=true

READ_CHAPTERS_RECORDED=
READ_CHAPTERS_MATERIALIZED=
READ_CHAPTERS_MATERIALIZE_FAILED=

PRIMARY_REPLAY_CANDIDATES=
PRIMARY_REPLAY_MATCHED=
PRIMARY_REPLAY_WINDOWS=
PRIMARY_REPLAY_COVERAGE_RATE=

H13_SOURCE_REPLAY_PRESENT=true
H07_SOURCE_REPLAY_PRESENT=true

JUDGE_NEW_PRIMARY_SOURCE_IDS=0
JUDGE_ADDITIONAL_SEARCHES=0

SCHOL_CAL2_REJUDGE_EXECUTED=true

REJUDGE_APPLICABLE_DIMENSION_MEAN=
REJUDGE_TEXTUAL_GROUNDING_REQUIRED_MEAN=
REJUDGE_HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
REJUDGE_LITERATURE_ORIENTATION_REQUIRED_MEAN=

REJUDGE_PRIMARY_TEXT_MISREPRESENTATION=
REJUDGE_FALSE_EXACT_QUOTE=

SCHOLARLY_SEARCH_IS_METADATA_ONLY=true
ABSTRACT_AVAILABLE_IMPLIES_READ=false
CONTENT_ATTRIBUTION_REQUIRES_FETCH=true

AUTO_SCHOLARLY_FETCH=0
SCHOLARLY_SEMANTIC_ROUTER=0

READ_ACTIVATION_PROBE_COMPLETED=3
PROBE_SEARCH_CALLS=
PROBE_FETCH_CALLS=
PROBE_CONTENT_EVIDENCE_COUNT=

SCHOL_CAL3_EXECUTED=
SCHOL_CAL3_COMPLETED=
SCHOL_CAL3_PUBLISHED=
SCHOL_CAL3_REPAIR_CONVERGENCE=

SCHOLARLY_SEARCH_CASES=
SCHOLARLY_SOURCE_FETCH_CASES=
SCHOLARLY_UNIQUE_RECORD_COUNT=
SCHOLARLY_CONTENT_EVIDENCE_COUNT=

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

PROPOSED_VERDICT=
AUTHORIZE_V3_HOLDOUT /
SCHOLARLY_PRODUCT_PATCH_REQUIRED

STOP

还有一个 receipt bookkeeping 小点：我在当前 HEAD 的 compare/directory 中没有看到你说的 PROBE/PROBE2 artifact 被归档；7049e1418 能确认的是 runner/Contract/measurement 改动。这个不影响结论，因为完整的 SCHOL_CAL2 已经独立证明 search activation 成立，但下一轮 probe artifact 要真正 commit 进去。

所以现在的状态，不是简单的：

“用了 scholarship，所以分数终于变真实地变差了”

而是更准确的：

search activation                ✅
scholarly provenance             ✅
delivery                         ✅

scholarly source reading         ❌

judge primary evidence parity    ❌

把这两个 ❌ 一起关掉，下一轮我们才第一次能真正测“一个会查、会读、会诚实综合二手研究的 PhiAgent”到底够不够格进 V3。