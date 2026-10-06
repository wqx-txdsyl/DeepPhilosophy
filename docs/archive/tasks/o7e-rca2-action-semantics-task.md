
我审完 93ee99c56 → 641847cdf。这次可以结束 RCA-1 的诊断阶段了。

先确认模型偏差：接受。 你已经明确禁止 deepseek-v4-pro 继续作为 Agent LLM，因此后续评测基线改为 deepseek-v4-flash。我不会再要求为了 O7-E 烧 V4-Pro。Flash 的 4/8 不能与之前 Pro 的 6/8 直接做性能纵向比较，但这次我们需要的核心证据是同一 trajectory 内 action → fingerprint 的因果关系，这一部分仍然有效。

正式签发：

O7_E_RP2_RCA1_FINAL_DIAGNOSTIC_REVIEW =
PASS_FOR_DIAGNOSIS

RCA1_DIAGNOSTIC_PHASE =
CLOSED

REPAIR_ACTION_SEMANTICS_REQUIRED =
CONFIRMED

QUOTE_REPLACE_TEXT_SEMANTICS =
STRUCTURALLY_DEFECTIVE

LOCAL_PATCH_FOUNDATION =
ACCEPTED_FOR_FURTHER_EVALUATION

LOCAL_PATCH_PRODUCTION_ENABLED =
false

RUN2_AUTHORIZED =
false

MAX_VALIDATION_REPAIRS =
RETAIN_2

REPAIR_PROMPT_TUNING =
NOT_AUTHORIZED

MODEL_POOL_EXPANSION =
NOT_AUTHORIZED

NEXT_PHASE =
O7_E_RP2_RCA2_REPAIR_ACTION_SEMANTICS

V3_STAGE_B_AUTHORIZED =
false
这次根因已经被真正证实

现在不再只是“我怀疑 REPLACE_TEXT 有问题”。

实现本身明确规定：无论 COPY_SLICE 还是 REPLACE_TEXT，最终都把 replacement 放到 content_start:content_end，也就是quote wrapper 内部。因此 REPLACE_TEXT 即使语义上是“paraphrase”，机械上仍然被保留在原来的 「…」 / blockquote 引文结构中。

H02 已经形成了非常干净的证据链：

initial:
4 issues

R1:
4 old fingerprints resolved
1 new UNSUPPORTED_EXACT_QUOTE introduced

actions:
quote REPLACE_TEXT ×2
quote COPY_SLICE ×1
citation REPLACE_TEXT ×1

R2:
R1 introduced 的 quote fingerprint resolved
又 introduction 一个新的 quote fingerprint

action:
quote REPLACE_TEXT

。

这正好吻合：

Agent 的意图：
“不要再逐字引用，我转述。”

当前 runtime 的执行：
“好的，我把转述文字塞回原来的引号里。”

Validator：
“这是一个新的逐字引文，而且没有证据。”

S4 的证据更强：第二轮成功解析的三个 citation COPY_SLICE 和三个 quote REPLACE_TEXT 把旧 fingerprint 全部消掉，却又产生了两个新 quote fingerprints。

H07 同样存在 quote REPLACE_TEXT，并在该轮后留下一个 persisted quote fingerprint 和一个 introduced fingerprint。

所以我现在正式接受：

剩余的核心 Local Patch 架构缺陷不是“模型还不够听话”，而是我们把“逐字引文修正”和“放弃逐字引文、改为转述”错误地塞进了同一种 content-span replacement 语义。

但我独立审计还发现两个统计口径 bug。它们不阻止 RCA-2，但下一阶段必须顺手修正。

第一，receipt 的：

ANCHOR_RESOLUTION_RATE = 0.947

不能解释成“Local Patch anchor 只有 94.7% 成功”。

Runner 当前把所有 repair attempts 的 bundle都计入：

Python
Run
bundle_rows = [
    b
    for t in trace
    for b in t.get("bundles", [])
]

而不是只统计真正进入 LOCAL_PATCH 的 attempt。

H07 已经直接暴露这个问题：

REPAIR_OUTPUT_MODES =
FULL_REWRITE,
LOCAL_PATCH

ANCHOR_TOTAL=10
ANCHOR_RESOLVED=8

。

第一轮正是因为有 unresolved anchor，所以正确地被 preflight 拦截并转成 FULL_REWRITE；这两个 unresolved anchor 不应该反过来降低 Local Patch 的 anchor hard gate。

也就是说应该拆成：

PREP_ANCHOR_RESOLUTION_RATE

用于诊断，

以及：

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE

用于 hard gate。

后者必须只统计：

repair_output_mode == LOCAL_PATCH

的 attempts。

第二，当前：

LINKED_EVIDENCE_STARVATION = 5

也不是一个可信的 starvation 数。

Runner 现在直接：

Python
Run
sum(
    1 for b in bundle_rows
    if not b.get("linked_source")
)

。

这会把两种完全不同的情况混为一谈：

A. issue 有 evidence_ref，
   本来应该解析出 source，
   结果没有 source
→ 真 starvation

B. issue 本来 evidence_ref=None，
   只允许 best-effort 找上下文，
   最后没找到
→ 不是 linked-evidence starvation

而 repair_context 明确允许第二种 MEMORY_ONLY/no-ref quote issue 走 best-effort；没有命中并不代表 linked evidence 丢失。

因此 receipt 中：

H02 ×3
H07 ×2

这五个我不接受为已证实 starvation。

下一阶段改成机械真值：

LINKED_EVIDENCE_REQUIRED
LINKED_EVIDENCE_PRESENT
LINKED_EVIDENCE_STARVATION

starvation =
evidence_ref_present
AND source_missing

并且同样只针对真正进入 LOCAL_PATCH 的 attempt 做 product hard gate。

这两个是 metric correction，不允许因此再开一个“H2E diagnostic”。

O7-E RP2 RCA-2
Quote Action Semantics Split
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 641847cdf

MODEL_UNDER_TEST = deepseek-v4-flash
REPAIR_CONFIG = 当前 Flash matched config

MAX_VALIDATION_REPAIRS = 2

PRODUCTION_LOCAL_PATCH_ENABLED = false
V3_HOLDOUT_RUN = false

这一阶段只改一个真正的架构问题：

quote repair
COPY exact text
≠
paraphrase claim
新 action contract

Citation 暂时不动。

Quote issue 从：

COPY_SLICE
REPLACE_TEXT

改成：

COPY_SLICE
PARAPHRASE_CLAIM
COPY_SLICE

语义保持现在完全不变：

Main Agent chooses slice_id
↓
runtime copies exact source bytes
↓
replace content_span only
↓
quote wrapper preserved

也就是：

> 「错误原文」

→

> 「准确原文」

Hard：

COPY_SLICE_TARGET = content_span
QUOTE_WRAPPER_PRESERVED = true
PARAPHRASE_CLAIM

这是新语义。

Main Agent 明确声明：

我不再把这段内容作为逐字引文，而是改为我自己的普通转述。

输出：

JSON
{
  "issue_id": "vi_3",
  "action": "PARAPHRASE_CLAIM",
  "replacement_text": "……"
}

Runtime：

replace claim_span

不是：

replace content_span

因此：

> 「孔子原话是……」

可以机械变成：

孔子在这里强调的是……

外部引号 / blockquote 被移除，是因为 Main Agent 显式选择了“这不再是一条逐字引文”。

这不是 runtime sanitizer，也不是 validator gaming。

权力归属仍然是：

要不要放弃逐字引文
→ Main Agent

转述写什么
→ Main Agent

把它机械放到 claim_span
→ runtime

所以：

COGNITIVE_POLICY_OWNER = 1
FINAL_WRITER = MAIN_AGENT
RUNTIME_GENERATED_PROSE_CHARS = 0
禁止 quote issue 使用旧 REPLACE_TEXT

Hard：

quote + REPLACE_TEXT
→ INVALID_ACTION_FOR_QUOTE

不要兼容。

否则旧 bug 迟早会回来。

Citation issue 暂时仍可以：

REPLACE_TEXT
COPY_SLICE

本阶段不同时重构 citation action；S4 的 citation COPY 已经实证能消除对应旧 fingerprints，不要一次改两个变量。

PARAPHRASE_CLAIM 本身不能重新制造 quote

机械 gate：

Python
Run
QB.extract_quotes(replacement_text)

必须为空。

如果 replacement 本身又形成 QuoteBound 可识别的逐字引文：

PARAPHRASE_CONTAINS_VERBATIM_QUOTE

协议错误。

这不是判断“转述写得好不好”，只是保证：

你既然选择 PARAPHRASE_CLAIM，那输出就必须真的不是逐字引文。

普通哲学术语仍然可以正常写；只要不会被现有 QuoteBound 规则认作 verbatim claim 即可。

intentional demotion 与 wrapper loss 必须区分

现在：

QUOTE_WRAPPER_LOSS

是 anti-gaming metric。

但 PARAPHRASE_CLAIM 本来就有意移除 wrapper。

所以不能把合法 semantic action 算成 wrapper loss。

新增：

INTENTIONAL_QUOTE_TO_PARAPHRASE

计数。

Hard：

UNINTENTIONAL_QUOTE_WRAPPER_LOSS = 0

而：

INTENTIONAL_QUOTE_TO_PARAPHRASE

只做 telemetry。

并继续保证：

PREEXISTING_VERIFIED_QUOTES_OUTSIDE_TARGET_LOST = 0
NON_TARGET_TEXT_CHANGED_CHARS = 0
metric correction 同一 commit 做掉

不允许另开阶段。

必须输出：

PREP_ANCHOR_TOTAL
PREP_ANCHOR_RESOLVED

LP_ANCHOR_TOTAL
LP_ANCHOR_RESOLVED
LOCAL_PATCH_ANCHOR_RESOLUTION_RATE

Hard gate 看：

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE = 1.0

而不是所有 preflight。

Evidence：

LINKED_EVIDENCE_REQUIRED
LINKED_EVIDENCE_PRESENT
LINKED_EVIDENCE_STARVATION
BEST_EFFORT_SOURCE_MISSING

定义：

LINKED_EVIDENCE_REQUIRED =
LOCAL_PATCH bundle.evidence_ref != null

最好再让 resolver 状态显式进入 bundle：

evidence_resolution =
RESOLVED
/
UNRESOLVED
/
NOT_REQUIRED

这样不再从 source is None 反推语义。

这次不要再动 slice catalog / prompt policy

除为了表达新 action schema 必须修改：

REPLACE_TEXT
→ PARAPHRASE_CLAIM

对应合同文字之外：

REPAIR_POLICY_CHANGED = false
SLICE_CATALOG_CHANGED = false
SOURCE_CONTEXT_ALGORITHM_CHANGED = false
VALIDATOR_CHANGED = false
QUOTE_BOUND_MATCHING_CHANGED = false

不许顺手“再优化一下”。

必测回归

至少锁这 12 项：

Q1 quote COPY_SLICE 仍只替换 content span，wrapper 保留；

Q2 quote PARAPHRASE_CLAIM 替换 claim span；

Q3 blockquote paraphrase 后 > 不再存在于目标 claim；

Q4 quoted/leadin paraphrase 后原 quote delimiters 不再包住 replacement；

Q5 PARAPHRASE_CLAIM replacement 被 QuoteBound 识别成新 quote → reject；

Q6 quote REPLACE_TEXT → reject；

Q7 citation REPLACE_TEXT 行为不变；

Q8 citation COPY_SLICE 行为不变；

Q9 target claim 外字节完全不变；

Q10 目标外已验证 quote byte-preserved；

Q11 intentional demotion 不计 UNINTENTIONAL_QUOTE_WRAPPER_LOSS；

Q12 LP anchor/starvation metric 只统计真实 LOCAL_PATCH attempt，FULL_REWRITE preflight 不进入 product denominator。

Evaluation

仍旧是当前 8-case calibration pool。

模型：

deepseek-v4-flash

不再用 Pro。

RUN1 hard gates：

COMPLETED = 8
PUBLISHED >= 7

if REPAIR_TRIGGERED >= 3:
    REPAIR_CONVERGENCE >= 0.80

VALIDATOR_EMPTY_FINAL = 0
TERMINAL_CANDIDATE_EMPTY = 0

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE = 1.0
PROMPT_ISSUE_COVERAGE = 1.0
LINKED_EVIDENCE_STARVATION = 0

UNKNOWN_SLICE_ID = 0
UNINTENTIONAL_QUOTE_WRAPPER_LOSS = 0
NON_TARGET_TEXT_CHANGED_CHARS = 0

另外报告：

COPY_SLICE_ACTIONS
PARAPHRASE_CLAIM_ACTIONS
CITATION_REPLACE_TEXT_ACTIONS

INTENTIONAL_QUOTE_TO_PARAPHRASE

QUOTE_ISSUES_RESOLVED_BY_COPY
QUOTE_ISSUES_RESOLVED_BY_PARAPHRASE

PARAPHRASE_INTRODUCED_QUOTE_ISSUES

我们真正想看到：

PARAPHRASE_INTRODUCED_QUOTE_ISSUES = 0

如果 RUN1 PASS：

RUN2 自动授权

同模型、同 config、同合同重跑。

如果两轮都 PASS：

LOCAL_PATCH_ARCHITECTURE_QUALIFIED = true

我再审是否正式接生产。

如果 RUN1 仍 FAIL：

不再增加 H2X。

我会直接根据失败类型在以下两者之间裁决：

A. Flash serialization/model reliability
B. Local Patch architecture still insufficient

不会再继续微调 patch prompt。

最终回执：

O7_E_RP2_RCA2 =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

ACTION_SEMANTICS_SHA=
METRIC_CORRECTION_SHA=
TEST_SHA=
RUN1_SHA=
HEAD_SHA=
REMOTE_SHA=

MODEL_UNDER_TEST=deepseek-v4-flash

QUOTE_ACTIONS=
COPY_SLICE,PARAPHRASE_CLAIM

QUOTE_REPLACE_TEXT_ALLOWED=false

COPY_SLICE_TARGET=content_span
PARAPHRASE_CLAIM_TARGET=claim_span

PARAPHRASE_CONTAINS_VERBATIM_QUOTE_REJECTED=
RUNTIME_GENERATED_PROSE_CHARS=0

INTENTIONAL_QUOTE_TO_PARAPHRASE=
UNINTENTIONAL_QUOTE_WRAPPER_LOSS=

PREEXISTING_VERIFIED_QUOTES_OUTSIDE_TARGET_LOST=
NON_TARGET_TEXT_CHANGED_CHARS=

PREP_ANCHOR_TOTAL=
PREP_ANCHOR_RESOLVED=

LP_ANCHOR_TOTAL=
LP_ANCHOR_RESOLVED=
LOCAL_PATCH_ANCHOR_RESOLUTION_RATE=

LINKED_EVIDENCE_REQUIRED=
LINKED_EVIDENCE_PRESENT=
LINKED_EVIDENCE_STARVATION=
BEST_EFFORT_SOURCE_MISSING=

RUN1_COMPLETED=8
RUN1_PUBLISHED=
RUN1_REPAIR_TRIGGERED=
RUN1_REPAIR_CONVERGED=
RUN1_REPAIR_CONVERGENCE=

COPY_SLICE_ACTIONS=
PARAPHRASE_CLAIM_ACTIONS=
CITATION_REPLACE_TEXT_ACTIONS=

QUOTE_ISSUES_RESOLVED_BY_COPY=
QUOTE_ISSUES_RESOLVED_BY_PARAPHRASE=
PARAPHRASE_INTRODUCED_QUOTE_ISSUES=

PATCH_PROTOCOL_ERRORS=
VALIDATOR_EMPTY_FINAL=
TERMINAL_CANDIDATE_EMPTY=

PROMPT_ISSUE_COVERAGE=
UNKNOWN_SLICE_ID=

RUN2_EXECUTED=
RUN2_PUBLISHED=
RUN2_REPAIR_CONVERGENCE=

MAX_VALIDATION_REPAIRS=2
PRODUCTION_LOCAL_PATCH_ENABLED=false

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false
SLICE_CATALOG_CHANGED=false
SOURCE_CONTEXT_ALGORITHM_CHANGED=false

PRODUCTION_MODEL_CHANGED=false
V3_HOLDOUT_RUN=false
PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_LOCAL_PATCH_PRODUCTION /
PATCH_REQUIRED

STOP

所以这次不用再诊断了。

RCA-1 已经完成它的任务：H02 与 S4 给出了足够强的因果证据，证明 REPLACE_TEXT-on-quote 是一个错误的 action semantics。

下一刀就落这里：不是“把引号删掉骗 validator”，而是让 Main Agent 明确选择：这是继续作为逐字引文，还是主动降为普通转述。Runtime 只负责把这个选择准确执行。